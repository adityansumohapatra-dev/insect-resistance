import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

from .synthetic_insect_data_generator import generate_synthetic_data
from .kinematics import compute_kinematics, summarize_kinematics

def run_validation(output_dir="validation_output"):
    os.makedirs(output_dir, exist_ok=True)
    
    print("1. Generating synthetic ground-truth data...")
    csv_path, json_path = generate_synthetic_data(output_dir, seed=42)
    
    df = pd.read_csv(csv_path)
    with open(json_path, 'r') as f:
        metadata = json.load(f)
        
    print("2. Running kinematics pipeline...")
    kinematics_df = compute_kinematics(df, metadata, window_length=15, polyorder=3, tortuosity_window=60)
    
    print("3. Validating Savitzky-Golay smoothing...")
    # Exclude NaNs from original data where visible=False, but compare smoothed x_px against x_true_px
    err_x = kinematics_df['x_smooth'] - kinematics_df['x_true_px']
    err_y = kinematics_df['y_smooth'] - kinematics_df['y_true_px']
    rmse = np.sqrt(np.mean(err_x**2 + err_y**2))
    print(f"   -> Smoothing RMSE vs Ground Truth: {rmse:.2f} pixels")
    if rmse < 10.0:
        print("   -> Smoothing validation PASSED.")
    else:
        print("   -> Smoothing validation FAILED (error too high).")
        
    print("4. Scoring and separation validation...")
    summary_df = summarize_kinematics(kinematics_df)
    
    # Merge phenotype back for validation
    pheno_map = {ins["id"]: ins["phenotype"] for ins in metadata["insects"]}
    summary_df["phenotype"] = summary_df["insect_id"].map(pheno_map)
    
    print("\n--- Summary ---")
    print(summary_df[['insect_id', 'phenotype', 'avoidance_score']].to_string(index=False))
    
    res_scores = summary_df[summary_df["phenotype"] == "resistant"]["avoidance_score"].values
    sus_scores = summary_df[summary_df["phenotype"] == "susceptible"]["avoidance_score"].values
    
    if len(res_scores) > 0 and len(sus_scores) > 0:
        mean_res = np.mean(res_scores)
        mean_sus = np.mean(sus_scores)
        print(f"\nMean Resistant Score: {mean_res:.3f}")
        print(f"Mean Susceptible Score: {mean_sus:.3f}")
        
        if mean_res > mean_sus * 1.5:  # Arbitrary separation threshold for this demo
            print("=> Validation PASSED: Clear separation between resistant and susceptible phenotypes.")
        else:
            print("=> Validation FAILED: Insufficient separation.")
    
    # Plot score separation and trajectories
    plt.figure(figsize=(10, 5))
    
    plt.subplot(1, 2, 1)
    for insect_id, group in kinematics_df.groupby("insect_id"):
        pheno = pheno_map[insect_id]
        color = 'red' if pheno == 'resistant' else 'blue'
        plt.plot(group['x_smooth'], group['y_smooth'], label=f"ID {insect_id} ({pheno})", color=color, alpha=0.7)
    
    plt.scatter([metadata["treated_disc_center"][0]], [metadata["treated_disc_center"][1]], color='red', marker='x', s=100, label='Treated')
    plt.scatter([metadata["control_disc_center"][0]], [metadata["control_disc_center"][1]], color='blue', marker='x', s=100, label='Control')
    
    circle = plt.Circle((0, 0), metadata["arena_radius"], color='black', fill=False, linestyle='--')
    plt.gca().add_patch(circle)
    
    dead_zone = plt.Circle((0, 0), metadata["arena_radius"] - metadata["recommended_dead_zone_margin_px"], color='gray', fill=False, linestyle=':')
    plt.gca().add_patch(dead_zone)
    
    plt.xlim(-600, 600)
    plt.ylim(-600, 600)
    plt.legend()
    plt.title("Smoothed Trajectories")
    
    plt.subplot(1, 2, 2)
    labels = summary_df['phenotype'].values
    scores = summary_df['avoidance_score'].values
    plt.bar(labels, scores, color=['red' if l == 'resistant' else 'blue' for l in labels])
    plt.ylabel('Avoidance Score')
    plt.title('Resistance Score Separation')
    
    plot_path = os.path.join(output_dir, "validation_plot.png")
    plt.savefig(plot_path)
    print(f"\nPlot saved to {plot_path}")

if __name__ == "__main__":
    run_validation()
