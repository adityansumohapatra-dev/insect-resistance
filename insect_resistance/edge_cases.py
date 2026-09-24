import numpy as np

def compute_gradient_concentration(x, y, treated_center, decay_length):
    """
    Evaluate the local chemical concentration as a continuous Gaussian field 
    decaying from the treated disc center.
    """
    dist_sq = (x - treated_center[0])**2 + (y - treated_center[1])**2
    return np.exp(-dist_sq / (2.0 * decay_length**2))

def is_in_dead_zone(x, y, arena_radius, margin_px, arena_center=(0.0, 0.0)):
    """
    Flag if a coordinate is within the configurable margin of the arena perimeter.
    Used to exclude thigmotaxis-driven movement from resistance scoring.
    """
    dist = np.hypot(x - arena_center[0], y - arena_center[1])
    return dist > (arena_radius - margin_px)
