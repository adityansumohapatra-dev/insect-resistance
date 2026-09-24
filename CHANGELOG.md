# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-09-25

### Added
- **Synthetic Data Generator**: Added `synthetic_insect_data_generator.py` for generating biologically plausible biased random walks with gradient aversion, thigmotaxis, and camera noise (occlusions, pixel jitter).
- **Kinematics Engine**: Added `kinematics.py` which computes velocity, deceleration, turning angles, and tortuosity metrics frame-by-frame.
- **Smoothing Filters**: Implemented Savitzky-Golay filtering in the kinematics engine to handle camera pixel-jitter gracefully.
- **Edge-Case Masking**: Added `edge_cases.py` to correctly map continuous Gaussian chemical gradients and dynamically mask dead zones (arena walls) to exclude thigmotaxis from avoidance scores.
- **Tracking Engine**: Added `tracking.py` featuring an OpenCV MOG2 background subtractor coupled with a SORT (Kalman Filter + Hungarian Algorithm) tracking system.
- **Validation Harness**: Added `validate.py` to programmatically confirm mathematical separation between "resistant" and "susceptible" behaviors, alongside a quantifiable residual-error check for smoothing.
- **CLI & Demo**: Added `cli.py` for general pipeline use on real data, and `demo.py` for a fast, visual, LinkedIn-ready demonstration of the pipeline.
