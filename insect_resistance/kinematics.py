import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

from .edge_cases import compute_gradient_concentration, is_in_dead_zone

def smooth_trajectory(group, window_length, polyorder):
    """
    Apply Savitzky-Golay filter to (x, y) coordinates for a single insect's trajectory.
    Interpolates NaNs linearly before smoothing since savgol_filter needs contiguous data.
    """
    df = group.copy().sort_values("frame")
    
    # Interpolate missing tracking data
    x_interp = df["x_px"].interpolate(method='linear', limit_direction='both').bfill().ffill()
    y_interp = df["y_px"].interpolate(method='linear', limit_direction='both').bfill().ffill()
    
    # Apply Savitzky-Golay
    df["x_smooth"] = savgol_filter(x_interp, window_length=window_length, polyorder=polyorder)
    df["y_smooth"] = savgol_filter(y_interp, window_length=window_length, polyorder=polyorder)
    
    return df

def compute_kinematics(df, metadata, window_length=15, polyorder=3, tortuosity_window=60):
    """
    Compute velocity, deceleration, turning angle, and tortuosity.
    Default savgol window of 15 corresponds to 0.5s at 30 fps, capturing real turns without over-smoothing jitter.
    """
    fps = metadata["fps"]
    dt = 1.0 / fps
    arena_radius = metadata["arena_radius"]
    treated_center = metadata["treated_disc_center"]
    decay_length = metadata["decay_length"]
    dead_zone_margin = metadata["recommended_dead_zone_margin_px"]
    
    results = []
    
    for insect_id, group in df.groupby("insect_id"):
        # 1. Smooth
        smooth_df = smooth_trajectory(group, window_length, polyorder)
        
        # 2. Kinematics
        x = smooth_df["x_smooth"].values
        y = smooth_df["y_smooth"].values
        
        dx = np.gradient(x)
        dy = np.gradient(y)
        
        velocity = np.sqrt(dx**2 + dy**2) / dt
        
        # Deceleration is negative derivative of velocity
        dv = np.gradient(velocity)
        deceleration = -dv / dt
        
        # Turning angle
        angles = np.arctan2(dy, dx)
        d_theta_rad = np.diff(angles, prepend=angles[0])
        d_theta_rad = (d_theta_rad + np.pi) % (2 * np.pi) - np.pi
        turning_angle = np.degrees(d_theta_rad)
        
        # Tortuosity (sliding window)
        tortuosity = np.ones(len(x))
        for i in range(len(x)):
            start_idx = max(0, i - tortuosity_window)
            end_idx = i + 1
            
            # path length
            path_length = np.sum(np.sqrt(np.diff(x[start_idx:end_idx])**2 + np.diff(y[start_idx:end_idx])**2))
            # chord length
            chord_length = np.hypot(x[i] - x[start_idx], y[i] - y[start_idx])
            
            if chord_length > 1e-5:
                tortuosity[i] = path_length / chord_length
            else:
                tortuosity[i] = 1.0 # default to 1 if no movement
                
        # Edge cases 
        in_dead_zone = np.array([is_in_dead_zone(xi, yi, arena_radius, dead_zone_margin) for xi, yi in zip(x, y)])
        concentration = np.array([compute_gradient_concentration(xi, yi, treated_center, decay_length) for xi, yi in zip(x, y)])
        
        smooth_df["velocity"] = velocity
        smooth_df["deceleration"] = deceleration
        smooth_df["turning_angle"] = turning_angle
        smooth_df["tortuosity"] = tortuosity
        smooth_df["in_dead_zone"] = in_dead_zone
        smooth_df["concentration"] = concentration
        
        results.append(smooth_df)
        
    return pd.concat(results).sort_values(["frame", "insect_id"])

def summarize_kinematics(kinematics_df):
    """
    Compute per-insect, per-trial summary metrics based on kinematics.
    """
    summaries = []
    
    for insect_id, group in kinematics_df.groupby("insect_id"):
        # filter out dead zone points for valid resistance scoring
        valid_points = group[~group["in_dead_zone"]]
        
        if len(valid_points) == 0:
            summaries.append({
                "insect_id": insect_id,
                "mean_deceleration_weighted": 0,
                "peak_deceleration": 0,
                "mean_abs_turn_weighted": 0,
                "peak_abs_turn": 0,
                "mean_tortuosity_weighted": 1.0,
                "avoidance_score": 0.0
            })
            continue
            
        c = valid_points["concentration"].values
        dec = valid_points["deceleration"].values
        turn = np.abs(valid_points["turning_angle"].values)
        tort = valid_points["tortuosity"].values
        
        # Weighted by concentration so actions near gradient count more
        c_sum = np.sum(c) if np.sum(c) > 1e-5 else 1.0
        
        mean_dec_w = np.sum(dec * c) / c_sum
        peak_dec = np.max(dec) if len(dec) > 0 else 0
        
        mean_turn_w = np.sum(turn * c) / c_sum
        peak_turn = np.max(turn) if len(turn) > 0 else 0
        
        mean_tort_w = np.sum(tort * c) / c_sum
        
        # Composite avoidance score
        # Scale each metric reasonably so they contribute
        # dec is ~ cm/s^2, turn is ~ degrees, tort is > 1
        score = (mean_dec_w * 0.1) + (mean_turn_w * 0.5) + (mean_tort_w * 5.0)
        
        # We might have negative dec if accelerating, just clip to 0 for scoring
        score = max(0, score)
        
        summaries.append({
            "insect_id": insect_id,
            "mean_deceleration_weighted": mean_dec_w,
            "peak_deceleration": peak_dec,
            "mean_abs_turn_weighted": mean_turn_w,
            "peak_abs_turn": peak_turn,
            "mean_tortuosity_weighted": mean_tort_w,
            "avoidance_score": score
        })
        
    return pd.DataFrame(summaries)
