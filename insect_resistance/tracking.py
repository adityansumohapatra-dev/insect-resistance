import cv2
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

class KalmanTracker:
    def __init__(self, id, initial_pos, dt=1/30.0):
        self.id = id
        self.kf = cv2.KalmanFilter(4, 2)
        
        # State: [x, y, vx, vy]
        # Measurement: [x, y]
        self.kf.measurementMatrix = np.array([[1, 0, 0, 0],
                                              [0, 1, 0, 0]], np.float32)
                                              
        self.kf.transitionMatrix = np.array([[1, 0, dt, 0],
                                             [0, 1, 0, dt],
                                             [0, 0, 1, 0],
                                             [0, 0, 0, 1]], np.float32)
                                             
        self.kf.processNoiseCov = np.eye(4, dtype=np.float32) * 1e-2
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 1e-1
        self.kf.errorCovPost = np.eye(4, dtype=np.float32)
        
        self.kf.statePost = np.array([[initial_pos[0]], [initial_pos[1]], [0.0], [0.0]], np.float32)
        self.time_since_update = 0
        self.hits = 1
        
    def predict(self):
        pred = self.kf.predict()
        self.time_since_update += 1
        return (pred[0, 0], pred[1, 0])
        
    def update(self, measurement):
        self.kf.correct(np.array([[np.float32(measurement[0])], [np.float32(measurement[1])]]))
        self.time_since_update = 0
        self.hits += 1

def process_video(video_path, dt=1/30.0, max_age=15):
    """
    Process video using OpenCV background subtraction, contours, and SORT-style 
    Kalman Filter + Hungarian Algorithm tracking.
    Outputs trajectory DataFrame matching Phase 1 generator format.
    """
    cap = cv2.VideoCapture(video_path)
    
    bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=False)
    
    trackers = []
    next_id = 1
    
    results = []
    frame_idx = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        time_s = frame_idx * dt
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply background subtraction
        fg_mask = bg_subtractor.apply(gray)
        _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
        
        # Clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=2)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        measurements = []
        for contour in contours:
            if cv2.contourArea(contour) > 10: # minimum size to filter noise
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = M["m10"] / M["m00"]
                    cy = M["m01"] / M["m00"]
                    measurements.append((cx, cy))
                    
        # Predict all trackers
        predictions = []
        for trk in trackers:
            predictions.append(trk.predict())
            
        # Hungarian Algorithm assignment
        if len(predictions) > 0 and len(measurements) > 0:
            cost_matrix = np.zeros((len(trackers), len(measurements)))
            for i, p in enumerate(predictions):
                for j, m in enumerate(measurements):
                    cost_matrix[i, j] = np.hypot(p[0] - m[0], p[1] - m[1])
                    
            row_ind, col_ind = linear_sum_assignment(cost_matrix)
            
            unassigned_trackers = set(range(len(trackers)))
            unassigned_measurements = set(range(len(measurements)))
            
            for r, c in zip(row_ind, col_ind):
                if cost_matrix[r, c] < 50: # distance threshold for valid matching
                    trackers[r].update(measurements[c])
                    unassigned_trackers.remove(r)
                    if c in unassigned_measurements:
                        unassigned_measurements.remove(c)
        else:
            unassigned_trackers = set(range(len(trackers)))
            unassigned_measurements = set(range(len(measurements)))
            
        # Create new trackers
        for c in unassigned_measurements:
            trk = KalmanTracker(next_id, measurements[c], dt)
            trackers.append(trk)
            next_id += 1
            
        # Output results
        for trk in trackers:
            if trk.time_since_update == 0:
                pos = (trk.kf.statePost[0, 0], trk.kf.statePost[1, 0])
                results.append({
                    "frame": frame_idx,
                    "time_s": time_s,
                    "insect_id": trk.id,
                    "x_px": pos[0],
                    "y_px": pos[1],
                    "visible": True
                })
            elif trk.time_since_update <= max_age:
                pos = (trk.kf.statePost[0, 0], trk.kf.statePost[1, 0])
                results.append({
                    "frame": frame_idx,
                    "time_s": time_s,
                    "insect_id": trk.id,
                    "x_px": np.nan,
                    "y_px": np.nan,
                    "visible": False
                })
                
        # Remove dead trackers
        trackers = [t for t in trackers if t.time_since_update <= max_age]
        
        frame_idx += 1
        
    cap.release()
    
    if len(results) == 0:
        return pd.DataFrame(columns=["frame", "time_s", "insect_id", "x_px", "y_px", "visible"])
        
    return pd.DataFrame(results)
