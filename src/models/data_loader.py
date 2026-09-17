"""
Module: src/models/data_loader.py
Patient-safe split and feature matrix loader for ML training and evaluation.

Loads feature matrices and target labels aligned by landmark_id across train, validation, and test splits.
Strictly selects the 81 active clinical ML predictors, excluding metadata and network placeholder features.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import duckdb

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.features.pipeline import (
    IDENTIFIER_COLUMNS,
    NETWORK_FEATURE_COLUMNS,
    get_baseline_feature_columns
)
from src.data.labels import TARGET_41_DISEASES, CONDITION_METADATA


class DatasetSplit:
    """Container holding feature matrix X, multi-target matrix Y, landmark IDs, and patient IDs for a split."""
    def __init__(
        self,
        name: str,
        X: np.ndarray,
        Y: np.ndarray,
        landmark_ids: List[str],
        person_ids: np.ndarray,
        feature_names: List[str],
        target_concept_ids: List[int]
    ):
        self.name = name
        self.X = X
        self.Y = Y
        self.landmark_ids = landmark_ids
        self.person_ids = person_ids
        self.feature_names = feature_names
        self.target_concept_ids = target_concept_ids
        self.target_col_to_idx = {cid: idx for idx, cid in enumerate(target_concept_ids)}

    def get_target_vector(self, target_concept_id: int) -> np.ndarray:
        idx = self.target_col_to_idx[target_concept_id]
        return self.Y[:, idx]

    @property
    def n_samples(self) -> int:
        return self.X.shape[0]

    @property
    def n_features(self) -> int:
        return self.X.shape[1]

    @property
    def n_targets(self) -> int:
        return self.Y.shape[1]


def load_dataset_splits(
    features_parquet: str = "data/parquet/features_inpatient_ed.parquet",
    splits_parquet: str = "data/parquet/splits_inpatient_ed.parquet",
    target_concept_ids: Optional[List[int]] = None,
    max_samples_per_split: Optional[int] = None,
    random_seed: int = 42
) -> Tuple[DatasetSplit, DatasetSplit, DatasetSplit]:
    """
    Loads Train, Validation, and Test dataset splits with exact 81 baseline features.
    
    Args:
        features_parquet: Path to feature matrix parquet.
        splits_parquet: Path to split assignment parquet.
        target_concept_ids: Optional list of target concept IDs to load (defaults to all 41).
        max_samples_per_split: Optional cap on rows per split for rapid smoke testing.
        random_seed: Deterministic random seed for sample slicing if capped.
        
    Returns:
        Tuple of (train_split, val_split, test_split).
    """
    if target_concept_ids is None:
        target_concept_ids = TARGET_41_DISEASES

    feature_cols = get_baseline_feature_columns(TARGET_41_DISEASES)
    target_cols = [f"target_{cid}" for cid in target_concept_ids]

    con = duckdb.connect()

    # Join features with split table on landmark_id
    con.execute(f"""
        CREATE OR REPLACE TEMP VIEW joined_split_data AS
        SELECT 
            s.split,
            f.person_id,
            f.landmark_id,
            {", ".join([f"f.{c}" for c in feature_cols])},
            {", ".join([f"s.{t}" for t in target_cols])}
        FROM '{features_parquet}' f
        JOIN '{splits_parquet}' s ON f.landmark_id = s.landmark_id
    """)

    splits_dict = {}
    for split_name in ["train", "val", "test"]:
        limit_clause = f"LIMIT {max_samples_per_split}" if max_samples_per_split is not None else ""
        
        # Extract metadata
        meta_rows = con.execute(f"""
            SELECT landmark_id, person_id 
            FROM joined_split_data 
            WHERE split = '{split_name}'
            ORDER BY person_id, landmark_id
            {limit_clause}
        """).fetchall()

        landmark_ids = [r[0] for r in meta_rows]
        person_ids = np.array([r[1] for r in meta_rows], dtype=np.int64)

        # Extract X features
        x_query = f"""
            SELECT {", ".join(feature_cols)}
            FROM joined_split_data
            WHERE split = '{split_name}'
            ORDER BY person_id, landmark_id
            {limit_clause}
        """
        x_raw = con.execute(x_query).fetchall()
        X = np.array(x_raw, dtype=np.float32)

        # Extract Y targets
        y_query = f"""
            SELECT {", ".join(target_cols)}
            FROM joined_split_data
            WHERE split = '{split_name}'
            ORDER BY person_id, landmark_id
            {limit_clause}
        """
        y_raw = con.execute(y_query).fetchall()
        Y = np.array(y_raw, dtype=np.int32)

        splits_dict[split_name] = DatasetSplit(
            name=split_name,
            X=X,
            Y=Y,
            landmark_ids=landmark_ids,
            person_ids=person_ids,
            feature_names=feature_cols,
            target_concept_ids=target_concept_ids
        )

    return splits_dict["train"], splits_dict["val"], splits_dict["test"]
