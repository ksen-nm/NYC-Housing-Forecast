# NYC Housing Forecast

[![R](https://img.shields.io/badge/Language-R-276DC3.svg)](https://www.r-project.org/)
[![Python](https://img.shields.io/badge/Language-Python-3776AB.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Overview

This repository contains a **complete, professional‑grade data analysis and data‑science project** built from two NYC Department of Housing Preservation and Development (HPD) datasets:

- `housing-new-york-units-by-building.csv` – 4,959 rows, 42 columns (one row per building)
- `housing-new-york-units-by-project.csv` – 2,583 rows, 18 columns (one row per project)

The project is written in **R** (using **R Markdown**) for the analytical pipeline and **Python/Streamlit** for an interactive dashboard.

## Repository Structure

```
├── housing_analysis.Rmd        # Full R‑Markdown report that knits to HTML
├── app.py                      # Streamlit dashboard (Python)
├── housing-new-york-units-by-building.csv
├── housing-new-york-units-by-project.csv
├── README.md                   # This file
├── .gitignore                  # Standard ignores (data, cache, etc.)
└── ... (metadata JSON files)
```

## Getting Started

### Prerequisites

- **R (>= 4.3)** with the following packages (install via the R Markdown header or manually):
  ```r
  install.packages(c(
    "tidyverse", "lubridate", "betareg", "caret", "randomForest",
    "gbm", "vip", "pdp", "car", "ggcorrplot", "leaflet", "sf",
    "scales", "knitr", "kableExtra", "marginaleffects", "broom",
    "patchwork", "ggridges", "viridis", "MASS"
  ))
  ```
- **Python (>= 3.9)** with the required libraries:
  ```bash
  pip install streamlit pandas plotly pydeck
  ```

### Running the R Report

```bash
# Open the project in RStudio (or any R environment)
# Then knit the Rmd file to HTML
rmarkdown::render("housing_analysis.Rmd")
```

The output HTML will be generated in the same directory and contains:
- Data loading & cleaning
- Feature engineering
- Exploratory visualizations (11 plots)
- Spatial analysis with Leaflet
- Statistical modeling (OLS, Beta regression, Random Forest, GBM)
- Policy interpretation and conclusions

### Running the Streamlit Dashboard

```bash
streamlit run app.py
```

The dashboard opens at `http://localhost:8502` and provides four tabs:
1. **Overview** – KPI cards and high‑level charts.
2. **Explorer** – Interactive filters and data table.
3. **Map** – Pydeck/Mapbox map colored by affordable %.
4. **Model insights** – Feature importance (RF) and actual vs. predicted plot.

## Project Highlights

- **Consistent aesthetics** – `theme_minimal()` for ggplot2, `viridis` palette, and Plotly’s built‑in theme.
- **Robust statistical modeling** – OLS (with diagnostics), Beta regression (appropriate for proportion outcomes), Random Forest, and Gradient Boosting, with a model‑comparison table.
- **Spatial insights** – Interactive Leaflet map and council‑district heatmaps.
- **Policy‑focused conclusions** – Identifies gentrification‑risk districts, tax‑benefit program performance, and suggests next‑step research.

## License

This project is licensed under the MIT License – see the `LICENSE` file for details.

---

*Feel free to open issues or pull requests if you have suggestions, find bugs, or want to extend the analysis.*
