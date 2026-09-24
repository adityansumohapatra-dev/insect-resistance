import pytest
import numpy as np
import pandas as pd
from insect_resistance.kinematics import compute_kinematics

def test_kinematics_velocity_and_deceleration():
    # Straight line movement: (0,0) to (3,4) to (6,8) -> dist = 5 per frame
    # Time delta = 1 sec
    metadata = {
        "fps": 1, 
        "arena_radius": 500,
        "treated_disc_center": (0, 0),
        "decay_length": 150,
        "recommended_dead_zone_margin_px": 50
    }
    
    # We provide a smoothed trajectory effectively by making x_px already perfect 
    # and skipping the SG filter or setting polyorder to something that preserves lines.
    # To bypass SG filter altering perfectly straight lines, 3 points with order 1 
    # will exactly reproduce the line, but we have a default window of 15.
    # Let's provide 15 points to satisfy window size.
    
    x = np.linspace(0, 42, 15)  # step 3
    y = np.linspace(0, 56, 15)  # step 4
    
    df = pd.DataFrame({
        "frame": np.arange(15),
        "insect_id": [1]*15,
        "x_px": x,
        "y_px": y
    })
    
    # We will use window=3, polyorder=1 to preserve exactly the linear data
    res = compute_kinematics(df, metadata, window_length=3, polyorder=1, tortuosity_window=5)
    
    velocity = res["velocity"].values
    deceleration = res["deceleration"].values
    
    # dt = 1 (since fps = 1). dx = 3, dy = 4 -> v = 5.
    np.testing.assert_allclose(velocity, 5.0, atol=1e-5)
    
    # Deceleration is negative derivative of velocity. Constant velocity -> deceleration = 0.
    np.testing.assert_allclose(deceleration, 0.0, atol=1e-5)

def test_kinematics_turning_angle():
    metadata = {
        "fps": 1, 
        "arena_radius": 500,
        "treated_disc_center": (0, 0),
        "decay_length": 150,
        "recommended_dead_zone_margin_px": 50
    }
    
    # Movement: along X axis, then turns 90 degrees to move along Y axis.
    # Points to make window size 3 valid:
    # (0,0), (1,0), (2,0), (2,1), (2,2)
    # At (2,0), angle changes from 0 to 90 degrees.
    df = pd.DataFrame({
        "frame": np.arange(5),
        "insect_id": [1]*5,
        "x_px": [0, 1, 2, 2, 2],
        "y_px": [0, 0, 0, 1, 2]
    })
    
    res = compute_kinematics(df, metadata, window_length=3, polyorder=1, tortuosity_window=5)
    
    # Note: SG filter will slightly smooth the corner, so we test if the turning angle spikes positive
    turn_angles = res["turning_angle"].values
    assert np.max(turn_angles) > 30.0 # Must detect a significant left turn
    assert np.min(turn_angles) >= -5.0 # Shouldn't detect significant right turns

def test_kinematics_tortuosity():
    metadata = {
        "fps": 1, 
        "arena_radius": 500,
        "treated_disc_center": (0, 0),
        "decay_length": 150,
        "recommended_dead_zone_margin_px": 50
    }
    
    # Semi-circle of radius R=10
    theta = np.linspace(0, np.pi, 15)
    x = 10 * np.cos(theta)
    y = 10 * np.sin(theta)
    
    df = pd.DataFrame({
        "frame": np.arange(15),
        "insect_id": [1]*15,
        "x_px": x,
        "y_px": y
    })
    
    res = compute_kinematics(df, metadata, window_length=3, polyorder=1, tortuosity_window=15)
    
    tortuosity = res["tortuosity"].values[-1]
    # Path length = pi * R ~ 31.415
    # Chord length = 2 * R = 20
    # Expected tortuosity = pi / 2 ~ 1.57
    expected_tortuosity = np.pi / 2
    assert np.abs(tortuosity - expected_tortuosity) < 0.1
