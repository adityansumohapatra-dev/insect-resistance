# Methodology & Mathematical Foundation

This document details the scientific and mathematical justification behind the Kinematic Insect Hesitation Tracking pipeline. It is intended for researchers seeking an exact, reproducible explanation of how "avoidance" is quantified from raw pixel coordinates.

## 1. Background: The Biomechanics of Avoidance

As described by Kareiva & Shigesada (1983) [1], animal movement can be modeled as a **correlated random walk (CRW)**. In the context of pesticide resistance, stimulus-dependent behavioral resistance manifests not merely as a survival outcome, but as a real-time modification of the insect's CRW parameters upon detecting a chemical gradient.

Specifically, "hesitation" in insects is mechanically defined by:
1. **Deceleration**: A rapid drop in linear velocity.
2. **Increased Turning Variance**: A deviation from straight-line pathing, resulting in sharp angular turns as the insect attempts to reorient away from the stimulus.
3. **High Tortuosity**: A localized increase in the "squiggliness" of the path (Benhamou, 2004) [2].

## 2. Signal Recovery: Savitzky-Golay Smoothing

Raw camera data (from standard macro-lens setups tracking small insects) inherently contains high-frequency pixel jitter. If we compute the derivative of position (velocity) on raw data, this jitter dominates the signal.

To solve this, we apply a **Savitzky-Golay filter** to the $x(t)$ and $y(t)$ coordinates.
Unlike a simple moving average, which erases genuine sharp turns (low-pass filtering away biological hesitation), the Savitzky-Golay filter fits a local low-degree polynomial (e.g., $k=3$) over a sliding window (e.g., 15 frames). This preserves the mathematical moments (the peaks and valleys) of the turning behavior while smoothing out artificial Gaussian camera noise.

## 3. Kinematics Calculations

Let the smoothed coordinates at frame $t$ be $(x_t, y_t)$.

### Velocity ($v_t$)
Velocity is the discrete derivative of position over time $\Delta t$.
$$ v_t = \frac{\sqrt{(x_t - x_{t-1})^2 + (y_t - y_{t-1})^2}}{\Delta t} $$

### Deceleration ($a_t$)
Deceleration is strictly the negative derivative of velocity. We isolate deceleration because braking is the primary biomechanical indicator of hesitation.
$$ a_t = -\frac{v_t - v_{t-1}}{\Delta t} $$

### Turning Angle ($\theta_t$)
The turning angle is the change in heading between consecutive frames.
Let heading $\phi_t = \text{atan2}(y_t - y_{t-1}, x_t - x_{t-1})$.
$$ \theta_t = (\phi_t - \phi_{t-1}) \pmod{360^\circ} $$
We map $\theta_t$ to the range $[-180^\circ, 180^\circ]$. Large absolute values $|\theta_t|$ indicate a sharp reorientation.

### Tortuosity ($\tau$)
Tortuosity is calculated over a sliding window (e.g., 60 frames) rather than start-to-end of the trial, capturing *localized* pacing behavior.
$$ \tau = \frac{L}{C} $$
Where $L$ is the actual path length (sum of step distances in the window) and $C$ is the straight-line chord distance from the start to the end of the window.

## 4. Edge-Case Corrections

A naive approach to scoring simply aggregates these metrics. However, insects in a petri dish present two major confounding variables.

### Thigmotaxis (Wall-Hugging)
Insects innately hug walls, an anxiety response known as thigmotaxis. When an insect reaches the plastic edge of a petri dish, it decelerates and turns sharply to follow the curve. A naive algorithm scores this as "avoidance." 
**Solution**: We define a static radial margin (the "Dead Zone"). Any kinematic metrics computed while the insect's centroid is inside this margin are permanently zeroed out or excluded from the final composite score.

### Gradient Concentration Mapping
Pesticide vapor diffusing from a leaf disc does not form a hard, binary wall. If an insect hesitates halfway across the dish, it should not be scored as avoiding the pesticide if the concentration there is near zero.
**Solution**: We model the chemical field as a continuous Gaussian decay centered on the treated disc $(x_c, y_c)$ with decay length $\lambda$:
$$ C(x, y) = e^{-\frac{(x - x_c)^2 + (y - y_c)^2}{2\lambda^2}} $$

When computing the final "Avoidance Score", the insect's deceleration and absolute turning angles are mathematically weighted by $C(x,y)$. Therefore, a sharp turn directly adjacent to the treated disc heavily inflates the resistance score, while a random sharp turn far away contributes almost nothing.

## References

1. Kareiva, P., & Shigesada, N. (1983). Analyzing insect movement as a correlated random walk. *Oecologia*, 56(2-3), 234-238.
2. Benhamou, S. (2004). How to reliably estimate the tortuosity of an animal's path: straightness, sinuosity, or fractal dimension? *Journal of Theoretical Biology*, 229(2), 209-220.
