import numpy as np
from insect_resistance.edge_cases import compute_gradient_concentration, is_in_dead_zone

def test_compute_gradient_concentration():
    treated_center = (0, 0)
    decay_length = 100.0
    
    # At center, concentration should be exactly 1.0
    c_center = compute_gradient_concentration(0, 0, treated_center, decay_length)
    assert np.isclose(c_center, 1.0)
    
    # At decay_length, dist^2 = decay_length^2 -> exp(-1/2) ~ 0.6065
    c_decay = compute_gradient_concentration(100, 0, treated_center, decay_length)
    assert np.isclose(c_decay, np.exp(-0.5))
    
    # Very far away, should approach 0
    c_far = compute_gradient_concentration(1000, 0, treated_center, decay_length)
    assert c_far < 1e-10

def test_is_in_dead_zone():
    arena_radius = 500.0
    margin = 50.0
    center = (0, 0)
    
    # Dead zone boundary is 450.
    
    # Origin is strictly inside the arena (not in dead zone)
    assert not is_in_dead_zone(0, 0, arena_radius, margin, center)
    
    # 400 is not in dead zone
    assert not is_in_dead_zone(400, 0, arena_radius, margin, center)
    
    # 450.1 is in dead zone
    assert is_in_dead_zone(450.1, 0, arena_radius, margin, center)
    
    # 500 is in dead zone
    assert is_in_dead_zone(500, 0, arena_radius, margin, center)
