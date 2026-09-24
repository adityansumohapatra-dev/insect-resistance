import argparse
import json
import pandas as pd
import matplotlib.pyplot as plt
import os
from .kinematics import compute_kinematics, summarize_kinematics

def run_cli():
    parser = argparse.ArgumentParser(description="Kinematic Insect Hesitation Tracking CLI")
    parser.add_argument("--csv", required=True, help="Path to input trajectory CSV")
    parser.add_argument("--json", required=True, help="Path to input metadata JSON")
    parser.add_argument("--outdir", default="output", help="Output directory")
    
    args = parser.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    
    df = pd.read_csv(args.csv)
    with open(args.json, 'r') as f:
        metadata = json.load(f)
        
    print("Computing kinematics...")
    kinematics_df = compute_kinematics(df, metadata)
    
    print("Generating summaries...")
    summary_df = summarize_kinematics(kinematics_df)
    
    kinematics_out = os.path.join(args.outdir, "kinematics.csv")
    kinematics_df.to_csv(kinematics_out, index=False)
    
    summary_out = os.path.join(args.outdir, "summary.csv")
    summary_df.to_csv(summary_out, index=False)
    
    print(f"Kinematics saved to {kinematics_out}")
    print(f"Summary saved to {summary_out}")
    
    # Generate Plot
    plt.figure(figsize=(8, 8))
    score_map = dict(zip(summary_df["insect_id"], summary_df["avoidance_score"]))
    max_score = summary_df["avoidance_score"].max()
    
    for insect_id, group in kinematics_df.groupby("insect_id"):
        score = score_map.get(insect_id, 0)
        norm_score = score / max_score if max_score > 0 else 0
        color = plt.cm.plasma(norm_score)
        plt.plot(group["x_smooth"], group["y_smooth"], label=f"ID {insect_id} (Score: {score:.1f})", color=color)
        
    plt.scatter([metadata["treated_disc_center"][0]], [metadata["treated_disc_center"][1]], color='red', marker='x', s=100, label='Treated')
    plt.scatter([metadata["control_disc_center"][0]], [metadata["control_disc_center"][1]], color='blue', marker='x', s=100, label='Control')
    
    circle = plt.Circle((0, 0), metadata["arena_radius"], color='black', fill=False, linestyle='--')
    plt.gca().add_patch(circle)
    
    dead_zone = plt.Circle((0, 0), metadata["arena_radius"] - metadata["recommended_dead_zone_margin_px"], color='gray', fill=False, linestyle=':')
    plt.gca().add_patch(dead_zone)
    
    plt.xlim(-metadata["arena_radius"] - 50, metadata["arena_radius"] + 50)
    plt.ylim(-metadata["arena_radius"] - 50, metadata["arena_radius"] + 50)
    
    plt.title("Insect Trajectories Colored by Avoidance Score")
    plt.legend()
    plot_out = os.path.join(args.outdir, "trajectories_plot.png")
    plt.savefig(plot_out)
    print(f"Plot saved to {plot_out}")
    
    report_out = os.path.join(args.outdir, "report.md")
    with open(report_out, "w") as f:
        f.write("# Trial Report\n\n")
        f.write("## Per-Insect Avoidance Scores\n\n")
        for _, row in summary_df.iterrows():
            f.write(f"- **Insect {int(row['insect_id'])}**: Avoidance Score = {row['avoidance_score']:.2f}\n")
            
    print(f"Markdown report saved to {report_out}")

if __name__ == "__main__":
    run_cli()
