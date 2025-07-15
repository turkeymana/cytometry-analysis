"""
Interactive dashboard for cytometry data analysis.
Built with Streamlit for web-based visualization.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from pathlib import Path
import sys
import os

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__)))

from database import CytometryDatabase
from analysis import CytometryAnalyzer


def load_data():
    """Load data from database."""
    try:
        analyzer = CytometryAnalyzer()
        return analyzer
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


def display_data_overview(analyzer):
    """Display Part 2 data overview."""
    st.header("Part 2: Data Overview")

    with st.spinner("Calculating relative frequency metrics..."):
        df = analyzer.part2_data_overview()

    if df.empty:
        st.warning("No data available for overview. Please verify that the input data is present and valid.")
        return

    st.subheader("Sample Summary Statistics")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Samples", df['sample'].nunique())
    with col2:
        st.metric("Cell Populations", df['population'].nunique())
    with col3:
        st.metric("Total Records", len(df))

    # Display sample data
    st.subheader("Relative Frequency Data (first 20 rows)")
    st.dataframe(df.head(20))

    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Full Dataset (CSV)",
        data=csv,
        file_name="data_overview.csv",
        mime="text/csv"
    )

    # Visualization
    st.subheader("Population Distribution Across All Samples")

    # Average percentage by population
    avg_percentages = df.groupby('population')['percentage'].mean().reset_index()
    avg_percentages = avg_percentages.sort_values('percentage', ascending=False)

    fig = px.bar(
        avg_percentages,
        x='population',
        y='percentage',
        title='Average Cell Population Percentages',
        labels={'percentage': 'Average Percentage (%)', 'population': 'Cell Population'}
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)


def display_statistical_analysis(analyzer):
    """Display Part 3 statistical analysis."""
    st.header("Part 3: Statistical Analysis")
    st.markdown("**Comparison of responders and non-responders for melanoma miraclib PBMC samples**")

    with st.spinner("Running statistical analysis..."):
        df, stats_results, matplotlib_fig = analyzer.part3_statistical_analysis()

    if df.empty:
        st.warning("No melanoma miraclib PBMC data available for analysis. Please check your input dataset.")
        return

    # Determine the correct sample column name
    sample_col = 'sample_id' if 'sample_id' in df.columns else 'sample'

    # Display summary metrics
    st.subheader("Sample Summary")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Samples", df[sample_col].nunique())
    with col2:
        responder_count = df[df['response'] == 'yes'][sample_col].nunique()
        st.metric("Responder Samples", responder_count)
    with col3:
        non_responder_count = df[df['response'] == 'no'][sample_col].nunique()
        st.metric("Non-Responder Samples", non_responder_count)

    # Interactive boxplot with Plotly
    st.subheader("Population Comparison: Responders vs Non-Responders")

    # Calculate percentages for plotting
    sample_totals = df.groupby(sample_col)['count'].sum().reset_index()
    sample_totals.columns = [sample_col, 'total_count']
    plot_df = df.merge(sample_totals, on=sample_col, how='left')
    # After merging, fix total_count columns
    if 'total_count_x' in plot_df.columns and 'total_count_y' in plot_df.columns:
        plot_df['total_count'] = plot_df['total_count_x']
        plot_df = plot_df.drop(['total_count_x', 'total_count_y'], axis=1)
    elif 'total_count_x' in plot_df.columns:
        plot_df['total_count'] = plot_df['total_count_x']
        plot_df = plot_df.drop(['total_count_x'], axis=1)
    elif 'total_count_y' in plot_df.columns:
        plot_df['total_count'] = plot_df['total_count_y']
        plot_df = plot_df.drop(['total_count_y'], axis=1)
    if 'total_count' not in plot_df.columns:
        st.error("'total_count' column missing after merge. Please check your data and merge keys.")
        return
    plot_df['percentage'] = (plot_df['count'] / plot_df['total_count']) * 100

    fig = px.box(
        plot_df,
        x='population_id',
        y='percentage',
        color='response',
        title='Cell Population Frequencies: Responders vs Non-Responders',
        labels={
            'percentage': 'Percentage (%)',
            'population_id': 'Cell Population',
            'response': 'Response'
        }
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # Statistical results table
    st.subheader("Statistical Test Results")


# --- Add this at the end of the file to render the dashboard ---
analyzer = load_data()
if analyzer:
    display_data_overview(analyzer)
    display_statistical_analysis(analyzer)