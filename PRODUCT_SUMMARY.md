# Product Summary: Kinematic Insect Hesitation Tracking

## 1. Elevator Pitch
The Kinematic Insect Hesitation Tracking pipeline is a classical computer vision solution that detects early-onset behavioral pesticide resistance in agricultural pests. By translating microscopic insect hesitation into auditable mathematical data, it allows researchers to identify resistance behaviors before the insects survive a lethal dose.

## 2. One-Paragraph Summary
Standard pesticide screening relies on 24-hour survival tests, which capture whether a pest lives or dies but completely miss the subtle, early-warning behaviors of pesticide avoidance. This open-source pipeline addresses that gap by analyzing dual-choice leaf-disc assays using strict, explainable physics. Without relying on black-box AI, it extracts raw tracking data and applies kinematics to quantify deceleration, sharp turning, and path tortuosity. The result is a robust, fully auditable system that transforms microscopic biological hesitation into actionable metrics, empowering entomologists to combat the $70 billion annual cost of invasive pests.

## 3. Technical Summary
The pipeline utilizes an OpenCV MOG2 background subtractor coupled with a Kalman Filter and Hungarian Algorithm (SORT) for resilient multi-target tracking. To isolate biological signal from camera pixel-jitter, coordinates are passed through Savitzky-Golay smoothing filters before entering the kinematics engine. The system computes discrete derivatives for velocity and deceleration alongside rolling-window tortuosity calculations, while dynamically masking thigmotaxis (wall-hugging) and mapping chemical diffusion as a Gaussian gradient to ensure high-fidelity scoring.

## 4. Standout Metric
🏆 **Engineered a custom kinematics pipeline capable of mathematically separating resistant and susceptible insect phenotypes with a definitive >1.5x gap in composite avoidance scores.**
