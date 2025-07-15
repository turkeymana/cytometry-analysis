"""
Main execution script for Cytometry Data Analysis.
Runs the complete analysis pipeline for Loblaw Bio coding challenge.
"""

import sys
import os
from pathlib import Path
import subprocess
import socket
import time
import webbrowser

# Ensure src directory is in Python path regardless of working directory
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
if not os.path.isdir(src_path):
    raise FileNotFoundError(f"Could not find 'src' directory at expected location: {src_path}")
if src_path not in sys.path:
    sys.path.append(src_path)

try:
    from database import CytometryDatabase
    from analysis import CytometryAnalyzer
except ImportError as e:
    raise ImportError(f"Failed to import CytometryDatabase or CytometryAnalyzer.\n"
                      f"Check that 'src/database.py' and 'src/analysis.py' exist and are correct.\n"
                      f"Original error: {e}")


def main():
    """
    Main execution pipeline for cytometry analysis.

    Steps:
    1. Initialize database and load data
    2. Run all analysis parts (2, 3, 4)
    3. Generate visualizations and reports
    4. Save results to output directory
    """

    print("Cytometry Data Analysis - Loblaw Bio Challenge")
    print("=" * 60)

    # Step 1: Database Setup and Data Loading
    print("\nStep 1: Database Setup and Data Loading")
    print("-" * 40)

    # Check if CSV file exists
    csv_path = "data/cell-count.csv"
    if not os.path.exists(csv_path):
        print(f"CSV file not found at {csv_path}")
        print("Please ensure the cell-count.csv file is in the data/ directory")
        return

    # Initialize database
    try:
        db = CytometryDatabase("cytometry_data.db")
        db.load_data_from_csv(csv_path)

        # Display data summary
        summary = db.get_sample_summary()
        print(f"Database initialized successfully")
        print(f"Data Summary:")
        print(f"   - Projects: {summary.iloc[0]['num_projects']}")
        print(f"   - Subjects: {summary.iloc[0]['num_subjects']}")
        print(f"   - Samples: {summary.iloc[0]['num_samples']}")
        print(f"   - Conditions: {summary.iloc[0]['num_conditions']}")
        print(f"   - Treatments: {summary.iloc[0]['num_treatments']}")

        db.close()

    except Exception as e:
        print(f"Database setup failed: {e}")
        return

    # Step 2: Run Analysis Pipeline
    print("\nStep 2: Running Analysis Pipeline")
    print("-" * 40)

    try:
        analyzer = CytometryAnalyzer("cytometry_data.db")

        # Create output directory
        output_dir = "output"
        Path(output_dir).mkdir(exist_ok=True)

        # --- Print statistical analysis results in main pipeline ---
        # Part 2: Data Overview
        print("Running Part 2: Data Overview...")
        part2_results = analyzer.part2_data_overview()
        print(f"Generated summary table with {len(part2_results)} rows")
        # Part 3: Statistical Analysis
        print("Running Part 3: Statistical Analysis...")
        part3_data, part3_stats, _ = analyzer.part3_statistical_analysis()
        # Print statistical analysis summary
        if part3_stats:
            print("\n=== Statistical Analysis Results ===")
            print("Comparing responders vs non-responders for melanoma miraclib PBMC samples:\n")
            for pop, results in part3_stats.items():
                print(f"{pop.upper()}:")
                print(f"  Responders: {results['responders_mean']:.2f}% ± {results['responders_std']:.2f}% (n={results['n_responders']})")
                print(f"  Non-responders: {results['non_responders_mean']:.2f}% ± {results['non_responders_std']:.2f}% (n={results['n_non_responders']})")
                print(f"  Mann-Whitney U: {results['mann_whitney_u']:.2f}")
                print(f"  p-value: {results['p_value']:.4f}")
                print(f"  Effect size: {results['effect_size']:.3f}")
                print(f"  Significant: {'Yes' if results['significant'] else 'No'}\n")
        else:
            print("No statistical results available.")
        # Part 4: Subset Analysis
        print("Running Part 4: Subset Analysis...")
        analyzer.part4_subset_analysis()
        # --- End statistical print block ---

        analyzer.save_results(output_dir)
        print("Analysis pipeline completed successfully")
        print(f"Results saved to '{output_dir}' directory")

    except Exception as e:
        print(f"Analysis pipeline failed: {e}")
        return

    # Step 3: Dashboard Information
    print("\nStep 3: Interactive Dashboard")
    print("-" * 40)

    # --- Dashboard launch code removed for CLI separation ---
    print("To launch the interactive dashboard, run:")
    print("    streamlit run src/dashboard.py --server.port 8000")
    print("in your terminal after this script completes.")
    # End of dashboard launch block

    # Step 4: Output Files Summary
    print("\nStep 4: Generated Output Files")
    print("-" * 40)

    output_files = [
        ("part2_data_overview.csv", "Relative frequency data for all samples"),
        ("part3_melanoma_data.csv", "Melanoma miraclib PBMC sample data"),
        ("part3_statistical_results.csv", "Statistical test results"),
        ("part3_boxplot.png", "Boxplot visualization"),
        ("part4_baseline_analysis.txt", "Baseline sample analysis summary")
    ]

    for filename, description in output_files:
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            print(f"{filename} - {description}")
        else:
            print(f"{filename} - Not generated")

    print(f"\nAnalysis Complete!")
    print(f"Please review the results in the '{output_dir}' directory")


if __name__ == "__main__":
    main()