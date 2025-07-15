"""
Database module for cytometry data analysis.
Handles SQLite database creation, schema design, and data loading.
"""

import sqlite3
import pandas as pd
import os
from pathlib import Path


class CytometryDatabase:
    """
    Database handler for cytometry analysis data.

    Schema Design Rationale:
    - Normalized structure for scalability
    - Separate tables for different entities
    - Proper indexing for query performance
    - Flexible design for multiple projects and sample types
    """

    def __init__(self, db_path: str = "cytometry_data.db"):
        """Initialize database connection and create schema."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        self.create_schema()

    def create_schema(self):
        """
        Create database schema optimized for analytical queries.

        Design considerations:
        1. Projects table: Scalable for hundreds of projects
        2. Subjects table: Patient/subject metadata
        3. Samples table: Sample-specific information
        4. Cell_counts table: Normalized cell population data
        5. Proper indexing for common query patterns
        """

        # Projects table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                project_name TEXT,
                description TEXT,
                created_date DATE DEFAULT CURRENT_DATE
            )
        """)

        # Subjects table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                subject_id TEXT PRIMARY KEY,
                project_id TEXT,
                condition TEXT,
                age INTEGER,
                sex TEXT CHECK (sex IN ('M', 'F')),
                treatment TEXT,
                response TEXT CHECK (response IN ('yes', 'no', NULL)),
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            )
        """)

        # Samples table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS samples (
                sample_id TEXT PRIMARY KEY,
                subject_id TEXT,
                sample_type TEXT,
                time_from_treatment_start INTEGER,
                collection_date DATE,
                FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
            )
        """)

        # Cell populations reference table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cell_populations (
                population_id TEXT PRIMARY KEY,
                population_name TEXT,
                description TEXT
            )
        """)

        # Cell counts table (normalized)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cell_counts (
                sample_id TEXT,
                population_id TEXT,
                count INTEGER,
                PRIMARY KEY (sample_id, population_id),
                FOREIGN KEY (sample_id) REFERENCES samples(sample_id),
                FOREIGN KEY (population_id) REFERENCES cell_populations(population_id)
            )
        """)

        # Create indexes for common queries
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_subjects_condition_treatment 
            ON subjects(condition, treatment)
        """)

        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_samples_time_type 
            ON samples(time_from_treatment_start, sample_type)
        """)

        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cell_counts_sample 
            ON cell_counts(sample_id)
        """)

        # Initialize cell populations
        self.initialize_cell_populations()

        self.conn.commit()

    def initialize_cell_populations(self):
        """Initialize the cell population reference table."""
        populations = [
            ('b_cell', 'B Cell', 'B lymphocytes'),
            ('cd8_t_cell', 'CD8+ T Cell', 'Cytotoxic T lymphocytes'),
            ('cd4_t_cell', 'CD4+ T Cell', 'Helper T lymphocytes'),
            ('nk_cell', 'NK Cell', 'Natural killer cells'),
            ('monocyte', 'Monocyte', 'Monocytes/macrophages')
        ]

        self.conn.executemany("""
            INSERT OR REPLACE INTO cell_populations 
            (population_id, population_name, description) 
            VALUES (?, ?, ?)
        """, populations)

    def load_data_from_csv(self, csv_path: str):
        """
        Load data from CSV file into the database.

        Args:
            csv_path: Path to the cell-count.csv file
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # Read CSV
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} rows from {csv_path}")

        # Validate required columns
        required_columns = [
            'project', 'subject', 'condition', 'age', 'sex', 'treatment',
            'response', 'sample', 'sample_type', 'time_from_treatment_start',
            'b_cell', 'cd8_t_cell', 'cd4_t_cell', 'nk_cell', 'monocyte'
        ]

        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Clear all main tables in correct order to avoid foreign key conflicts
        self.conn.execute("DELETE FROM cell_counts")
        self.conn.execute("DELETE FROM samples")
        self.conn.execute("DELETE FROM subjects")
        self.conn.execute("DELETE FROM projects")

        # Load projects
        projects = df[['project']].drop_duplicates()
        projects = projects.rename(columns={'project': 'project_id'})
        projects['project_name'] = projects['project_id']
        projects['description'] = 'Cytometry analysis project'
        projects.to_sql('projects', self.conn, if_exists='append', index=False)

        # Load subjects
        subjects = df[['subject', 'project', 'condition', 'age', 'sex',
                       'treatment', 'response']].drop_duplicates()
        subjects = subjects.rename(columns={
            'subject': 'subject_id',
            'project': 'project_id'
        })
        subjects.to_sql('subjects', self.conn, if_exists='append', index=False)

        # Load samples
        samples = df[['sample', 'subject', 'sample_type', 'time_from_treatment_start']].copy()
        samples = samples.rename(columns={
            'sample': 'sample_id',
            'subject': 'subject_id'
        })
        samples.to_sql('samples', self.conn, if_exists='append', index=False)

        # Load cell counts (normalized format)
        cell_populations = ['b_cell', 'cd8_t_cell', 'cd4_t_cell', 'nk_cell', 'monocyte']
        cell_count_rows = []
        for _, row in df.iterrows():
            for pop in cell_populations:
                cell_count_rows.append({
                    'sample_id': row['sample'],
                    'population_id': pop,
                    'count': row[pop]
                })
        cell_counts_df = pd.DataFrame(cell_count_rows)
        cell_counts_df.to_sql('cell_counts', self.conn, if_exists='append', index=False)

        self.conn.commit()
        print(f"Successfully loaded {len(df)} samples with {len(cell_count_rows)} cell count records")

    def get_sample_summary(self):
        """Get summary statistics of loaded data."""
        query = """
        SELECT 
            COUNT(DISTINCT p.project_id) as num_projects,
            COUNT(DISTINCT s.subject_id) as num_subjects,
            COUNT(DISTINCT sa.sample_id) as num_samples,
            COUNT(DISTINCT s.condition) as num_conditions,
            COUNT(DISTINCT s.treatment) as num_treatments
        FROM projects p
        JOIN subjects s ON p.project_id = s.project_id
        JOIN samples sa ON s.subject_id = sa.subject_id
        """

        return pd.read_sql_query(query, self.conn)

    def close(self):
        """Close database connection."""
        self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def main():
    """Test the database functionality."""
    # Test database creation and data loading
    db = CytometryDatabase("test_cytometry.db")

    try:
        # Load data (assuming CSV is in data folder)
        csv_path = "data/cell-count.csv"  # Update path as needed
        if os.path.exists(csv_path):
            db.load_data_from_csv(csv_path)

            # Display summary
            summary = db.get_sample_summary()
            print("\nData Summary:")
            print(summary)
        else:
            print(f"CSV file not found at {csv_path}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()