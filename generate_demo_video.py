import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import imageio_ffmpeg
import os
import sys

# Ensure insect_resistance is in path
sys.path.append(os.path.abspath("."))
from insect_resistance.synthetic_insect_data_generator import generate_synthetic_data

def main():
    print("Generating synthetic data...")
    # Generate 15 seconds of data at 30 fps = 450 frames.
    insects = []
    for i in range(12):
        pheno = "resistant" if i % 2 == 0 else "susceptible"
        start_x = np.random.uniform(-100, 100)
        start_y = np.random.uniform(-100, 100)
        insects.append({"id": i+1, "phenotype": pheno, "start": (start_x, start_y)})
        
    csv_path, json_path = generate_synthetic_data(output_dir="data", seed=101, duration=15, insects=insects)
    df = pd.read_csv(csv_path)
    
    print("Preparing animation...")
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(6, 6), dpi=120)
    fig.patch.set_facecolor('#050505')
    ax.set_facecolor('#050505')
    
    arena_radius = 500.0
    ax.set_xlim(-arena_radius, arena_radius)
    ax.set_ylim(-arena_radius, arena_radius)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Draw arena
    arena_circle = plt.Circle((0, 0), arena_radius, color='#333333', fill=False, lw=2)
    ax.add_artist(arena_circle)
    
    # Draw treated disc
    treated = plt.Circle((-250, 0), 50, color='#ff3300', alpha=0.15, zorder=1)
    treated_edge = plt.Circle((-250, 0), 50, color='#ff3300', fill=False, lw=1.5, zorder=2)
    ax.add_artist(treated)
    ax.add_artist(treated_edge)
    
    # Draw control disc
    control = plt.Circle((250, 0), 50, color='#ffffff', alpha=0.05, zorder=1)
    control_edge = plt.Circle((250, 0), 50, color='#666666', fill=False, lw=1.5, zorder=2)
    ax.add_artist(control)
    ax.add_artist(control_edge)
    
    lines = {}
    dots = {}
    for i in insects:
        color = '#ff3300' if i['phenotype'] == 'resistant' else '#0066ff'
        line, = ax.plot([], [], color=color, alpha=0.5, lw=2, zorder=3)
        dot, = ax.plot([], [], 'o', color=color, markersize=5, zorder=4)
        lines[i['id']] = line
        dots[i['id']] = dot
        
    time_text = ax.text(0.05, 0.95, '', transform=ax.transAxes, color='#ffffff', 
                        fontsize=14, fontweight='bold', fontfamily='sans-serif',
                        va='top')

    df_grouped = df.groupby("frame")
    max_frame = df["frame"].max()
    
    def init():
        for l in lines.values(): l.set_data([], [])
        for d in dots.values(): d.set_data([], [])
        time_text.set_text('')
        return list(lines.values()) + list(dots.values()) + [time_text]
        
    def update(frame):
        if frame not in df_grouped.groups:
            return list(lines.values()) + list(dots.values()) + [time_text]
            
        current_data = df_grouped.get_group(frame)
        # Trail length: last 45 frames (1.5 seconds)
        past_data = df[(df["frame"] <= frame) & (df["frame"] > frame - 45)]
        
        for ins_id, line in lines.items():
            ins_past = past_data[past_data["insect_id"] == ins_id]
            if not ins_past.empty:
                line.set_data(ins_past["x_true_px"], ins_past["y_true_px"])
            else:
                line.set_data([], [])
                
        for ins_id, dot in dots.items():
            ins_curr = current_data[current_data["insect_id"] == ins_id]
            if not ins_curr.empty:
                dot.set_data([ins_curr["x_true_px"].values[0]], [ins_curr["y_true_px"].values[0]])
            else:
                dot.set_data([], [])
                
        time_s = frame / 30.0
        time_text.set_text(f"ELAPSED: {time_s:.1f}s")
        return list(lines.values()) + list(dots.values()) + [time_text]
    
    print("Animating...")
    # Render at 30 fps directly for smooth video
    ani = animation.FuncAnimation(fig, update, frames=range(0, int(max_frame)+1), init_func=init, blit=True)
                                  
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    plt.rcParams['animation.ffmpeg_path'] = ffmpeg_exe
    writer = animation.FFMpegWriter(fps=30, metadata=dict(artist='EntoMetrics'), bitrate=1500)
    
    os.makedirs("docs/assets", exist_ok=True)
    out_path = "docs/assets/pipeline_demo.mp4"
    ani.save(out_path, writer=writer)
    print(f"Saved to {out_path}")
    print(f"File size: {os.path.getsize(out_path) / (1024*1024):.2f} MB")
    
if __name__ == "__main__":
    main()
