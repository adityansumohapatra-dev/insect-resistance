# Contributing to Kinematic Insect Hesitation Tracking

First off, thank you for considering contributing to this project! It's people like you that make the open-source community such a great place to learn, inspire, and create.

## How to Contribute

### 1. File an Issue
If you find a bug or have a feature request, please file an issue using the templates provided in `.github/ISSUE_TEMPLATE/`.
- Ensure the bug was not already reported by searching on GitHub under Issues.
- If you're unable to find an open issue addressing the problem, open a new one.

### 2. Proposing Changes
1. Fork the repository and create your branch from `main`.
2. Name your branch using the convention: `feat/feature-name` or `bugfix/issue-description`.
3. If you've added code that should be tested, add tests in the `insect_resistance/tests/` directory.
4. Ensure the test suite passes (see below).
5. Update documentation and README.md if applicable.
6. Issue that pull request!

### 3. Coding Style Expectations
- **Type Hints:** Please use Python type hinting (`def process(video_path: str) -> pd.DataFrame:`) for new functions.
- **Docstrings:** All public modules, functions, classes, and methods should have a docstring following PEP 257. Include a brief description of the mathematical operations if writing kinematic functions.
- **No Deep Learning:** Adhere strictly to the project constraint: no deep learning frameworks (PyTorch, TensorFlow) or trained ML models. Use classical computer vision and statistics.

### 4. Running the Test Suite
Before submitting a PR, verify that all core mathematical assertions hold true.
```bash
pip install -r requirements.txt
pytest insect_resistance/tests/
```
All tests must pass. We use continuous integration (GitHub Actions) which will automatically reject PRs with failing tests.

### Code of Conduct
By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).
