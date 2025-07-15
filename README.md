# Cytometry Data Analysis - Loblaw Bio Challenge

This project analyzes clinical cytometry data and provides an interactive dashboard for exploration.

Message from Callum: Sorry for this being late, I was unable to gain access to a computer over the weekend and programming on my phone was making me tear my hair out. In total I spent about 2:30 on completing it. I was shocked how well Claude managed to get the initial requirements correct and didn't have to do too many modifications from there. I can't wait to continue to work with you in the future and maybe dive into interactome for these dashboards aswell.

## Quick Start

### 1. Environment Setup
- Python 3.9+ required.
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### 2. Prepare Data
- Place your `cell-count.csv` file in the `data/` directory:
  ```
  data/
  └── cell-count.csv
  ```

### 3. Run the Analysis Pipeline
- This will generate all output files in the `output/` directory:
  ```bash
  python main.py
  ```

### 4. Launch the Dashboard
- Start Streamlit (this will open a single browser tab):
  ```bash
  streamlit run src/dashboard.py --server.port 8000
  ```
- Visit [http://localhost:8000](http://localhost:8000) if it does not open automatically.

## Output Files
- All results are saved to the `output/` directory:
  - `part2_data_overview.csv`: Relative frequency data for all samples
  - `part3_melanoma_data.csv`: Melanoma PBMC sample data
  - `part3_statistical_results.csv`: Statistical test results
  - `part3_boxplot.png`: Boxplot visualization
  - `part4_baseline_analysis.txt`: Baseline sample analysis summary

## Project Structure
- `main.py`: Runs the full analysis pipeline
- `src/database.py`: Database schema and data loader
- `src/analysis.py`: All analysis logic
- `src/dashboard.py`: Streamlit dashboard UI
- `output/`: All generated results

## Notes
- Only run `main.py` once to generate outputs. Then use Streamlit as above.
- If you update your data or code, rerun `main.py` before refreshing the dashboard.
