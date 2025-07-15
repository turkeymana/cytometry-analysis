"""
Analysis module for cytometry data.
Handles data analysis, statistical tests, and visualization.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from pathlib import Path
import sqlite3
from typing import Tuple, Dict, List
import warnings

warnings.filterwarnings('ignore')


class CytometryAnalyzer:
    """
    Main analysis class for cytometry data.
    Handles Parts 2, 3, and 4 of the analysis requirements.
    """

    def __init__(self, db_path: str = "cytometry_data.db"):
        """Initialize analyzer with database connection."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)

    def part2_data_overview(self) -> pd.DataFrame:
        """
        Part 2: Calculate relative frequency of each cell type in each sample.

        Returns:
            DataFrame with columns: sample, total_count, population, count, percentage
        """
        query = """
        SELECT 
            cc.sample_id as sample,
            cp.population_id as population,
            cc.count
        FROM cell_counts cc
        JOIN cell_populations cp ON cc.population_id = cp.population_id
        ORDER BY cc.sample_id, cp.population_id
        """

        df = pd.read_sql_query(query, self.conn)

        # Calculate total count per sample
        sample_totals = df.groupby('sample')['count'].sum().reset_index()
        sample_totals.columns = ['sample', 'total_count']

        # Merge with original data
        result = df.merge(sample_totals, on='sample')

        # Calculate percentage
        result['percentage'] = (result['count'] / result['total_count']) * 100

        # Reorder columns as specified
        result = result[['sample', 'total_count', 'population', 'count', 'percentage']]

        return result

    def part3_statistical_analysis(self) -> Tuple[pd.DataFrame, Dict, plt.Figure]:
        """
        Part 3: Compare melanoma miraclib PBMC samples between responders and non-responders.

        Returns:
            Tuple of (summary_data, statistical_results, plot_figure)
        """

        # Query for melanoma patients with miraclib treatment and PBMC samples
        query = """
        SELECT 
            s.subject_id,
            s.response,
            sa.sample_id,
            cc.population_id,
            cc.count,
            sa.time_from_treatment_start
        FROM subjects s
        JOIN samples sa ON s.subject_id = sa.subject_id
        JOIN cell_counts cc ON sa.sample_id = cc.sample_id
        WHERE s.condition = 'melanoma' 
        AND s.treatment = 'miraclib'
        AND sa.sample_type = 'PBMC'
        AND s.response IS NOT NULL
        """

        df = pd.read_sql_query(query, self.conn)

        if df.empty:
            return pd.DataFrame(), {}, plt.figure()

        # Calculate total counts and percentages
        sample_totals = df.groupby('sample_id')['count'].sum().reset_index()
        sample_totals.columns = ['sample_id', 'total_count']

        df = df.merge(sample_totals, on='sample_id')
        df['percentage'] = (df['count'] / df['total_count']) * 100

        # Statistical analysis
        populations = df['population_id'].unique()
        statistical_results = {}

        plot_data = []

        for pop in populations:
            pop_data = df[df['population_id'] == pop]

            responders = pop_data[pop_data['response'] == 'yes']['percentage']
            non_responders = pop_data[pop_data['response'] == 'no']['percentage']

            # Statistical test (Mann-Whitney U test for non-parametric data)
            if len(responders) > 0 and len(non_responders) > 0:
                statistic, p_value = stats.mannwhitneyu(
                    responders, non_responders, alternative='two-sided'
                )

                # Effect size (r = Z/√N)
                n_total = len(responders) + len(non_responders)
                z_score = stats.norm.ppf(p_value / 2)  # Convert p-value to z-score
                effect_size = abs(z_score) / np.sqrt(n_total)

                statistical_results[pop] = {
                    'responders_mean': responders.mean(),
                    'responders_std': responders.std(),
                    'non_responders_mean': non_responders.mean(),
                    'non_responders_std': non_responders.std(),
                    'mann_whitney_u': statistic,
                    'p_value': p_value,
                    'effect_size': effect_size,
                    'significant': p_value < 0.05,
                    'n_responders': len(responders),
                    'n_non_responders': len(non_responders)
                }

                # Prepare data for boxplot (include total_count)
                for val, tc in zip(responders, pop_data[pop_data['response'] == 'yes']['total_count']):
                    plot_data.append({
                        'population': pop,
                        'response': 'Responder',
                        'percentage': val,
                        'total_count': tc
                    })
                for val, tc in zip(non_responders, pop_data[pop_data['response'] == 'no']['total_count']):
                    plot_data.append({
                        'population': pop,
                        'response': 'Non-Responder',
                        'percentage': val,
                        'total_count': tc
                    })

        # Create visualization
        plot_df = pd.DataFrame(plot_data)

        # Fix: Consolidate total_count columns after merge
        if 'total_count_x' in plot_df.columns and 'total_count_y' in plot_df.columns:
            plot_df['total_count'] = plot_df['total_count_x']
            plot_df = plot_df.drop(['total_count_x', 'total_count_y'], axis=1)
        elif 'total_count' not in plot_df.columns and 'total_count_x' in plot_df.columns:
            plot_df['total_count'] = plot_df['total_count_x']
            plot_df = plot_df.drop(['total_count_x'], axis=1)
        elif 'total_count' not in plot_df.columns and 'total_count_y' in plot_df.columns:
            plot_df['total_count'] = plot_df['total_count_y']
            plot_df = plot_df.drop(['total_count_y'], axis=1)

        # Create boxplot
        fig, ax = plt.subplots(figsize=(12, 8))

        if not plot_df.empty:
            sns.boxplot(data=plot_df, x='population', y='percentage',
                        hue='response', ax=ax)
            ax.set_title('Cell Population Frequencies: Responders vs Non-Responders\n(Melanoma Miraclib PBMC Samples)')
            ax.set_xlabel('Cell Population')
            ax.set_ylabel('Percentage (%)')
            ax.tick_params(axis='x', rotation=45)

            # Add statistical significance annotations
            for i, pop in enumerate(populations):
                if pop in statistical_results and statistical_results[pop]['significant']:
                    ax.annotate('*', xy=(i, ax.get_ylim()[1] * 0.95),
                                ha='center', va='bottom', fontsize=16, color='red')

        plt.tight_layout()

        return df, statistical_results, fig

    def part4_subset_analysis(self) -> Dict:
        """
        Part 4: Analyze melanoma PBMC baseline samples with miraclib treatment.

        Returns:
            Dictionary with analysis results
        """

        # Query for melanoma PBMC baseline samples with miraclib
        query = """
        SELECT 
            s.project_id,
            s.subject_id,
            s.response,
            s.sex,
            sa.sample_id
        FROM subjects s
        JOIN samples sa ON s.subject_id = sa.subject_id
        WHERE s.condition = 'melanoma'
        AND s.treatment = 'miraclib'
        AND sa.sample_type = 'PBMC'
        AND sa.time_from_treatment_start = 0
        """

        df = pd.read_sql_query(query, self.conn)

        if df.empty:
            return {}

        results = {
            'total_samples': len(df),
            'samples_by_project': df['project_id'].value_counts().to_dict(),
            'responders_by_response': df['response'].value_counts().to_dict(),
            'subjects_by_gender': df['sex'].value_counts().to_dict(),
            'unique_subjects': df['subject_id'].nunique()
        }

        return results

    def save_results(self, output_dir: str = "output"):
        """Save all analysis results to files."""

        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)

        # Part 2: Data overview
        part2_results = self.part2_data_overview()
        part2_results.to_csv(f"{output_dir}/part2_data_overview.csv", index=False)

        # Part 3: Statistical analysis
        part3_data, part3_stats, part3_fig = self.part3_statistical_analysis()
        part3_data.to_csv(f"{output_dir}/part3_melanoma_data.csv", index=False)
        part3_fig.savefig(f"{output_dir}/part3_boxplot.png", dpi=300, bbox_inches='tight')

        # Save statistical results
        stats_df = pd.DataFrame(part3_stats).T
        stats_df.to_csv(f"{output_dir}/part3_statistical_results.csv")

        # Part 4: Subset analysis
        part4_results = self.part4_subset_analysis()

        # Save part 4 results as text file
        with open(f"{output_dir}/part4_baseline_analysis.txt", "w") as f:
            f.write("Part 4: Baseline Melanoma Miraclib PBMC Analysis\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total samples: {part4_results.get('total_samples', 0)}\n")
            f.write(f"Unique subjects: {part4_results.get('unique_subjects', 0)}\n\n")

            f.write("Samples by project:\n")
            for project, count in part4_results.get('samples_by_project', {}).items():
                f.write(f"  {project}: {count}\n")

            f.write("\nSubjects by response:\n")
            for response, count in part4_results.get('responders_by_response', {}).items():
                f.write(f"  {response}: {count}\n")

            f.write("\nSubjects by gender:\n")
            for gender, count in part4_results.get('subjects_by_gender', {}).items():
                f.write(f"  {gender}: {count}\n")

    def close(self):
        """Close database connection."""
        self.conn.close()


def main():
    """Run the complete analysis pipeline."""

    analyzer = CytometryAnalyzer()

    try:
        # Run all analyses and save results
        analyzer.save_results()

    except Exception as e:
        print(f"Error during analysis: {e}")

    finally:
        analyzer.close()


if __name__ == "__main__":
    main()