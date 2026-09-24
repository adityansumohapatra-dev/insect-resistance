import os
import json
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from insect_resistance.synthetic_insect_data_generator import generate_synthetic_data
from insect_resistance.kinematics import compute_kinematics, summarize_kinematics

def print_banner(text):
    print("\n" + "="*70)
    print(f" {text.upper()} ")
    print("="*70)

def apply_plot_style():
    plt.style.use('default')
    plt.rcParams.update({
        'font.size': 14,
        'axes.titlesize': 18,
        'axes.labelsize': 14,
        'lines.linewidth': 2.5,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
        'axes.grid': False
    })

def plot_arena(ax, metadata):
    circle = plt.Circle((0, 0), metadata["arena_radius"], color='black', fill=False, linestyle='-', linewidth=2)
    ax.add_patch(circle)
    
    treated = plt.Circle(metadata["treated_disc_center"], metadata["disc_radius"], color='salmon', alpha=0.5, label='Treated Disc')
    ax.add_patch(treated)
    
    control = plt.Circle(metadata["control_disc_center"], metadata["disc_radius"], color='lightblue', alpha=0.5, label='Control Disc')
    ax.add_patch(control)
    
    ax.set_xlim(-metadata["arena_radius"]-50, metadata["arena_radius"]+50)
    ax.set_ylim(-metadata["arena_radius"]-50, metadata["arena_radius"]+50)
    ax.set_aspect('equal')

def main():
    apply_plot_style()
    os.makedirs("demo_output", exist_ok=True)
    
    # ---------------------------------------------------------
    # BEAT 1 — Generate synthetic ground truth
    # ---------------------------------------------------------
    print_banner("Beat 1: Generating Ground Truth Data")
    print("Before touching real video data, we need absolute ground truth to prove our math works.")
    
    insects = [
        {"id": 1, "phenotype": "resistant", "start": (50.0, 150.0)},
        {"id": 2, "phenotype": "resistant", "start": (50.0, 0.0)},
        {"id": 3, "phenotype": "resistant", "start": (50.0, -150.0)},
        {"id": 4, "phenotype": "susceptible", "start": (-50.0, 100.0)},
        {"id": 5, "phenotype": "susceptible", "start": (-50.0, -50.0)},
        {"id": 6, "phenotype": "susceptible", "start": (-50.0, -200.0)}
    ]
    
    csv_path, json_path = generate_synthetic_data(output_dir="demo_output", seed=101, duration=30, insects=insects)
    
    df = pd.read_csv(csv_path)
    with open(json_path, 'r') as f:
        metadata = json.load(f)
        
    print(f"-> Generated {len(insects)} insects (3 Resistant, 3 Susceptible)")
    print(f"-> Trial duration: {metadata['duration']}s @ {metadata['fps']} FPS ({len(df)} total data points)")
    print(f"-> Arena radius: {metadata['arena_radius']}px | Treated disc at {metadata['treated_disc_center']}")
    time.sleep(1.5)
    
    # ---------------------------------------------------------
    # BEAT 2 — Show the raw trajectory plot
    # ---------------------------------------------------------
    print_banner("Beat 2: Raw Trajectories Visualized")
    print("Plotting the raw noisy paths. Notice how resistant insects (red) loop and hesitate near the treated disc.")
    
    fig, ax = plt.subplots(figsize=(8, 8))
    plot_arena(ax, metadata)
    
    # Map for easy pheno lookup
    pheno_map = {ins["id"]: ins["phenotype"] for ins in metadata["insects"]}
    
    res_plotted = False
    sus_plotted = False
    
    for insect_id, group in df.groupby("insect_id"):
        pheno = pheno_map[insect_id]
        color = '#d62728' if pheno == 'resistant' else '#1f77b4'
        
        label = None
        if pheno == 'resistant' and not res_plotted:
            label = 'Resistant'
            res_plotted = True
        elif pheno == 'susceptible' and not sus_plotted:
            label = 'Susceptible'
            sus_plotted = True
            
        ax.plot(group["x_px"], group["y_px"], color=color, alpha=0.8, linewidth=2, label=label)
        
    ax.set_title("Dual-Choice Assay Trajectories")
    ax.legend(loc="upper right", frameon=True, shadow=True)
    
    plot2_path = "demo_output/beat2_trajectories.png"
    plt.savefig(plot2_path, dpi=150, bbox_inches='tight')
    print(f"-> Saved {plot2_path}")
    plt.show(block=False)
    plt.pause(2.0)
    
    # ---------------------------------------------------------
    # BEAT 3 — Run kinematics & Prove separation
    # ---------------------------------------------------------
    print_banner("Beat 3: Kinematics Engine & Scoring")
    print("Running SG-smoothing, Velocity, Deceleration, Turning Angle, and Tortuosity...")
    
    kinematics_df = compute_kinematics(df, metadata, window_length=15, polyorder=3, tortuosity_window=60)
    summary_df = summarize_kinematics(kinematics_df)
    summary_df["phenotype"] = summary_df["insect_id"].map(pheno_map)
    
    res_scores = summary_df[summary_df["phenotype"] == "resistant"]["avoidance_score"]
    sus_scores = summary_df[summary_df["phenotype"] == "susceptible"]["avoidance_score"]
    
    print("\n--- RESULTS TABLE ---")
    print(f"{'Phenotype':<15} | {'Mean Avoidance Score':<20}")
    print("-" * 40)
    print(f"{'Resistant':<15} | {res_scores.mean():.2f}")
    print(f"{'Susceptible':<15} | {sus_scores.mean():.2f}")
    
    gap = res_scores.mean() / sus_scores.mean() if sus_scores.mean() > 0 else 0
    print(f"\n=> {gap:.1f}x effect size. Clear mathematical separation achieved.")
    
    fig, ax = plt.subplots(figsize=(6, 5))
    bars = ax.bar(['Resistant', 'Susceptible'], [res_scores.mean(), sus_scores.mean()], color=['#d62728', '#1f77b4'])
    ax.set_ylabel("Composite Avoidance Score")
    ax.set_title("Quantified Resistance Separation")
    
    # Add values on top of bars
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 0.5, f"{yval:.1f}", ha='center', va='bottom', fontweight='bold')
        
    plot3_path = "demo_output/beat3_separation.png"
    plt.savefig(plot3_path, dpi=150, bbox_inches='tight')
    print(f"-> Saved {plot3_path}")
    plt.show(block=False)
    plt.pause(2.0)
    
    # ---------------------------------------------------------
    # BEAT 4 — Smoothing Validation
    # ---------------------------------------------------------
    print_banner("Beat 4: Signal Recovery (Smoothing Validation)")
    print("Verifying that Savitzky-Golay filtering removes pixel jitter without erasing real behavior.")
    
    target_id = 1
    insect1_raw = df[df["insect_id"] == target_id]
    insect1_kin = kinematics_df[kinematics_df["insect_id"] == target_id]
    
    # Interpolate raw for fair error metric mapping
    raw_x = insect1_raw["x_px"].interpolate().bfill().ffill()
    raw_y = insect1_raw["y_px"].interpolate().bfill().ffill()
    true_x = insect1_raw["x_true_px"]
    true_y = insect1_raw["y_true_px"]
    smooth_x = insect1_kin["x_smooth"]
    smooth_y = insect1_kin["y_smooth"]
    
    err_raw = np.sqrt((raw_x - true_x)**2 + (raw_y - true_y)**2).mean()
    err_smooth = np.sqrt((smooth_x - true_x)**2 + (smooth_y - true_y)**2).mean()
    
    print(f"-> Raw Camera Jitter Error: {err_raw:.2f}px")
    print(f"-> Smoothed Residual Error: {err_smooth:.2f}px")
    print(f"Noise reduced by {((err_raw - err_smooth) / err_raw)*100:.1f}%")
    
    fig, ax = plt.subplots(figsize=(6, 6))
    # Zoom in on a chunk of the trajectory
    zoom_start = 200
    zoom_end = 350
    ax.plot(raw_x.iloc[zoom_start:zoom_end], raw_y.iloc[zoom_start:zoom_end], color='gray', alpha=0.5, label='Raw Camera', marker='.', linestyle='')
    ax.plot(true_x.iloc[zoom_start:zoom_end], true_y.iloc[zoom_start:zoom_end], color='black', linewidth=4, alpha=0.3, label='Ground Truth')
    ax.plot(smooth_x.iloc[zoom_start:zoom_end], smooth_y.iloc[zoom_start:zoom_end], color='#d62728', linewidth=2.5, label='SG Smoothed')
    
    ax.set_title(f"Trajectory Smoothing (Insect {target_id})")
    ax.legend()
    
    plot4_path = "demo_output/beat4_smoothing.png"
    plt.savefig(plot4_path, dpi=150, bbox_inches='tight')
    print(f"-> Saved {plot4_path}")
    plt.show(block=False)
    plt.pause(2.0)
    
    # ---------------------------------------------------------
    # BEAT 5 — Dead Zone / Thigmotaxis Correction
    # ---------------------------------------------------------
    print_banner("Beat 5: Thigmotaxis Correction (Dead Zone)")
    
    margin = metadata["recommended_dead_zone_margin_px"]
    radius = metadata["arena_radius"]
    
    target_id_sus = 5  # Pick a susceptible insect that hits the wall
    sus_kin = kinematics_df[kinematics_df["insect_id"] == target_id_sus]
    
    in_dead_zone = sus_kin["in_dead_zone"]
    excluded_frames = in_dead_zone.sum()
    
    print(f"Excluding wall-hugging behavior so it doesn't inflate hesitation scores.")
    print(f"-> Insect {target_id_sus} (Susceptible): Excluded {excluded_frames} frames ({excluded_frames/len(sus_kin)*100:.1f}%) in the dead zone.")
    
    fig, ax = plt.subplots(figsize=(7, 7))
    circle = plt.Circle((0, 0), radius, color='black', fill=False, linewidth=2)
    ax.add_patch(circle)
    
    # Shaded dead zone
    dead_zone_inner = plt.Circle((0, 0), radius - margin, color='gray', alpha=0.2, fill=True)
    ax.add_patch(dead_zone_inner)
    
    # Invert the inner circle visually by making it white (so only the ring is shaded)
    white_inner = plt.Circle((0, 0), radius - margin, color='white', fill=True)
    ax.add_patch(white_inner)
    
    # Outline of dead zone
    dead_zone_line = plt.Circle((0, 0), radius - margin, color='gray', fill=False, linestyle='--')
    ax.add_patch(dead_zone_line)
    
    # Plot points
    ax.plot(sus_kin[~in_dead_zone]["x_smooth"], sus_kin[~in_dead_zone]["y_smooth"], color='#1f77b4', linewidth=2.5, label='Valid Scoring Region')
    ax.plot(sus_kin[in_dead_zone]["x_smooth"], sus_kin[in_dead_zone]["y_smooth"], color='orange', linewidth=2.5, label='Excluded (Thigmotaxis)')
    
    ax.set_xlim(-radius-50, radius+50)
    ax.set_ylim(-radius-50, radius+50)
    ax.set_aspect('equal')
    ax.set_title(f"Dead Zone Masking (Insect {target_id_sus})")
    ax.legend(loc='center')
    
    plot5_path = "demo_output/beat5_deadzone.png"
    plt.savefig(plot5_path, dpi=150, bbox_inches='tight')
    print(f"-> Saved {plot5_path}")
    plt.show(block=False)
    
    print_banner("Demo Complete!")
    print("All artifacts saved to demo_output/. Close plot windows to exit.")
    plt.show() # Keeps everything open until closed by user

if __name__ == "__main__":
    main()
