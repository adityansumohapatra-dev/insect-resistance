import numpy as np
import pandas as pd
import json
import os
import argparse

def generate_synthetic_data(output_dir="data", seed=42, duration=60, insects=None):
    np.random.seed(seed)
    os.makedirs(output_dir, exist_ok=True)
    
    fps = 30
    n_frames = fps * duration
    dt = 1.0 / fps
    
    arena_radius = 500.0
    treated_disc_center = (-250.0, 0.0)
    control_disc_center = (250.0, 0.0)
    disc_radius = 50.0
    decay_length = 150.0
    recommended_dead_zone_margin_px = 50.0
    
    if insects is None:
        insects = [
            {"id": 1, "phenotype": "resistant", "start": (0.0, 200.0)},
            {"id": 2, "phenotype": "susceptible", "start": (0.0, -200.0)}
        ]
    
    records = []
    
    for ins in insects:
        x, y = ins["start"]
        theta = np.random.uniform(-np.pi, np.pi)
        base_speed = 100.0
        
        for frame in range(n_frames):
            time_s = frame * dt
            
            # gradient from treated disc
            dist_to_treated = np.hypot(x - treated_disc_center[0], y - treated_disc_center[1])
            concentration = np.exp(-(dist_to_treated**2) / (2 * decay_length**2))
            
            # thigmotaxis
            dist_to_center = np.hypot(x, y)
            
            speed = base_speed
            d_theta = np.random.normal(0, 0.2)
            
            if ins["phenotype"] == "resistant":
                # Decelerate and increase turning variance near chemical
                speed = base_speed * (1.0 - 0.95 * concentration) # Almost stops
                d_theta = np.random.normal(0, 0.2 + 2.0 * concentration) # Huge turning
                
                # Steer away from treated disc
                if concentration > 0.05:
                    angle_to_treated = np.arctan2(treated_disc_center[1] - y, treated_disc_center[0] - x)
                    angle_diff = (angle_to_treated - theta + np.pi) % (2 * np.pi) - np.pi
                    d_theta -= 1.5 * np.sign(angle_diff) * concentration
            
            # wall hugging (thigmotaxis)
            if dist_to_center > arena_radius - recommended_dead_zone_margin_px:
                angle_to_center = np.arctan2(-y, -x)
                angle_diff = (angle_to_center - theta + np.pi) % (2 * np.pi) - np.pi
                d_theta += 0.8 * np.sign(angle_diff)
                speed *= 0.5
            
            theta += d_theta
            
            # update true pos
            x_true = x + speed * np.cos(theta) * dt
            y_true = y + speed * np.sin(theta) * dt
            
            # hard boundary
            if np.hypot(x_true, y_true) > arena_radius:
                x_true = x
                y_true = y
                theta += np.pi # bounce
                
            x, y = x_true, y_true
            
            # Add noise and dropout
            visible = np.random.rand() > 0.05
            x_px = x_true + np.random.normal(0, 3) if visible else np.nan
            y_px = y_true + np.random.normal(0, 3) if visible else np.nan
            
            records.append({
                "frame": frame,
                "time_s": time_s,
                "insect_id": ins["id"],
                "phenotype": ins["phenotype"],
                "x_px": x_px,
                "y_px": y_px,
                "visible": visible,
                "x_true_px": x_true,
                "y_true_px": y_true
            })
            
    df = pd.DataFrame(records)
    csv_path = os.path.join(output_dir, "synthetic_trajectory.csv")
    df.to_csv(csv_path, index=False)
    
    metadata = {
        "arena_radius": arena_radius,
        "fps": fps,
        "duration": duration,
        "treated_disc_center": treated_disc_center,
        "control_disc_center": control_disc_center,
        "disc_radius": disc_radius,
        "decay_length": decay_length,
        "recommended_dead_zone_margin_px": recommended_dead_zone_margin_px,
        "insects": insects,
        "seed": seed
    }
    
    json_path = os.path.join(output_dir, "synthetic_metadata.json")
    with open(json_path, 'w') as f:
        json.dump(metadata, f, indent=4)
        
    return csv_path, json_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=str, default="data", help="Output directory")
    args = parser.parse_args()
    generate_synthetic_data(args.out)
