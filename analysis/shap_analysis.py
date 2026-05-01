"""Backward-compatible entry point for explainability analysis.

This file name is kept because SHAP is one accepted explainability option in the
competition rules. The main report, however, is component-based and explains the
actual deterministic forecasting pipeline. SHAP is only an optional diagnostic.
"""

from explainability_analysis import main


if __name__ == "__main__":
    main()
