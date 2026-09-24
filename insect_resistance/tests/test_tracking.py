import pytest
import numpy as np
from insect_resistance.tracking import KalmanTracker

def test_kalman_tracker_predict_update():
    # Initial position (0, 0)
    tracker = KalmanTracker(id=1, initial_pos=(0, 0), dt=1.0)
    
    # Predict without update
    pred1 = tracker.predict()
    # Expect it to be essentially 0,0 since velocity is initialized to 0
    np.testing.assert_allclose(pred1, (0, 0), atol=1e-3)
    
    # Provide an update at (10, 0)
    tracker.update((10, 0))
    
    # Predict again
    pred2 = tracker.predict()
    # Now velocity should be estimated towards positive X
    assert pred2[0] > 0.0
    
    # Provide another update at (20, 0)
    tracker.update((20, 0))
    pred3 = tracker.predict()
    assert pred3[0] > pred2[0]
