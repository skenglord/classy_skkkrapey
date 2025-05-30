# Contributing to Ibiza Event Scraper & API

First off, thank you for considering contributing to this project! We welcome and appreciate all contributions, from bug reports to new features. This document provides guidelines to help you get started.

## Getting Started

1.  **Set Up Your Development Environment:**
    *   Ensure you have met all the prerequisites listed in the main `README.md` file.
    *   Follow the "Setup and Installation" instructions in `README.md` to clone the repository, set up your virtual environment, and install core dependencies.

2.  **Install Development Dependencies:**
    This project uses a separate file for development-specific dependencies, such as testing tools. Install them using:
    ```bash
    pip install -r requirements-dev.txt
    ```

## How to Contribute

### Reporting Bugs

If you encounter a bug, please help us by reporting it:

1.  **Check Existing Issues:** Before submitting a new bug report, please check the existing issues on GitHub to see if the bug has already been reported.
2.  **Provide Details:** If the bug hasn't been reported, open a new issue. Please include:
    *   A clear and descriptive title.
    *   A detailed description of the bug.
    *   Steps to reproduce the bug.
    *   The version of the software you are using (if applicable, or commit hash).
    *   Information about your environment (e.g., OS, Python version, MongoDB version).
    *   Any relevant error messages or screenshots.

### Suggesting Enhancements

We are open to suggestions for new features or improvements to existing functionality.

1.  **Check Existing Issues/Discussions:** See if your idea has already been suggested or discussed.
2.  **Open an Issue:** If not, please open a new issue to outline your enhancement proposal. Provide:
    *   A clear and descriptive title.
    *   A detailed explanation of the proposed enhancement and its benefits.
    *   Any potential drawbacks or considerations.
    *   (Optional) Mockups or specific examples if applicable.

### Code Contributions

If you'd like to contribute code to fix a bug or implement an enhancement:

1.  **Fork the Repository:** Create your own fork of the project on GitHub.
2.  **Create a Branch:** Create a new branch in your fork for your changes. Use a descriptive name, for example:
    *   For features: `git checkout -b feature/your-awesome-feature`
    *   For bug fixes: `git checkout -b bugfix/fix-for-issue-123`
3.  **Make Your Changes:** Write your code!
4.  **Coding Style:**
    *   Please adhere to the [PEP 8 style guide](https://www.python.org/dev/peps/pep-0008/) for Python code.
    *   Write clear, readable, and well-commented code where necessary.
    *   Ensure type hints are used appropriately.
5.  **Testing:**
    *   **Write New Tests:** If you are adding a new feature or fixing a bug, please add new tests to cover your changes.
    *   **Ensure Existing Tests Pass:** Make sure all existing tests continue to pass after your changes.
    *   **Run Tests:** You can run the test suite using `pytest`:
        ```bash
        pytest
        ```
6.  **Documentation:**
    *   If your changes affect existing documentation (e.g., `README.md`, docstrings, or other specific docs), please update it accordingly.
    *   For new features, ensure they are appropriately documented.
7.  **Commit Your Changes:** Use clear and descriptive commit messages. A good commit message explains *why* a change was made, not just *what* was changed.
    ```bash
    git add .
    git commit -m "feat: Implement X feature for Y module"
    # Example fix: git commit -m "fix: Resolve issue Z in ABC component"
    ```
8.  **Push to Your Fork:**
    ```bash
    git push origin feature/your-awesome-feature
    ```
9.  **Open a Pull Request (PR):**
    *   Navigate to the main repository and open a Pull Request from your forked branch to the `main` branch (or `develop` if that is the primary development branch).
    *   Provide a clear title for your PR (e.g., "Feature: Add X functionality" or "Fix: Corrects Y bug").
    *   Include a detailed description of the changes in your PR, explaining what you've done and why.
    *   Link to any relevant GitHub issues (e.g., "Closes #123" or "Addresses #456").

## Pull Request Review Process

1.  **Review:** Your PR will be reviewed by one or more maintainers.
2.  **Feedback:** Maintainers may provide feedback or ask for changes. Please be responsive to any comments.
3.  **Merging:** Once the PR is approved and passes any automated checks, it will be merged.

## Code of Conduct

While this project does not yet have a formal Code of Conduct document, we expect all contributors to engage in respectful and constructive communication. Please be considerate of others and help create a positive and welcoming environment.

## Questions?

If you have any questions about contributing, feel free to:
*   Open an issue on GitHub and label it as a "question."
*   (If applicable) Join any project communication channels like a Discord server or mailing list.

Thank you for contributing!
