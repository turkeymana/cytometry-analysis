import os
import pytest
from src.database import CytometryDatabase

def test_database_creation_and_loading():
    db_path = "test_cytometry.db"
    csv_path = "data/cell-count.csv"
    db = CytometryDatabase(db_path)
    try:
        db.load_data_from_csv(csv_path)
        summary = db.get_sample_summary()
        assert summary['num_samples'][0] > 0
    finally:
        db.close()
        if os.path.exists(db_path):
            os.remove(db_path)
