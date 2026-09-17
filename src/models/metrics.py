"""
Module: src/models/metrics.py
Comprehensive Evaluation Metric Harness implementing Section 9 of COMORBIDITY_ENSEMBLE_ML_PLAN.md.

Computes:
1. Primary Metric: AUPRC (Average Precision Score) per disease and Macro-AUPRC across all K targets.
2. Ranking Metrics: Precision@K, Recall@K, and MAP@K (K = 3, 5, 10) evaluated across all modeled diseases per patient snapshot.
3. Secondary Metrics: AUROC, Brier Score, and tuned-threshold F1.
4. Tiered Performance: Macro-averages stratified across High, Medium, and Low prevalence tiers.
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from sklearn.metrics import average_precision_score, roc_auc_score, brier_score_loss, f1_score


def compute_binary_metrics(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    threshold: Optional[float] = None
) -> Dict[str, float]:
    """
    Computes single-disease binary classification metrics.
    
    Args:
        y_true: 1D binary array of ground truth labels {0, 1}.
        y_pred_proba: 1D array of predicted probabilities in [0.0, 1.0].
        threshold: Decision threshold for F1 score (if None, optimized on current data).
        
    Returns:
        Dict of computed metrics.
    """
    n_pos = int(np.sum(y_true))
    n_total = len(y_true)
    prevalence = float(n_pos / n_total) if n_total > 0 else 0.0

    # If no positive cases or all positive cases, handle edge cases gracefully
    if n_pos == 0 or n_pos == n_total:
        return {
            "n_samples": n_total,
            "n_positive": n_pos,
            "prevalence": round(prevalence, 6),
            "auprc": round(prevalence, 6),
            "auroc": 0.5,
            "brier_score": round(float(brier_score_loss(y_true, y_pred_proba)), 6),
            "f1_tuned": 0.0,
            "tuned_threshold": 0.5
        }

    # 1. AUPRC (Primary Metric)
    auprc = float(average_precision_score(y_true, y_pred_proba))

    # 2. AUROC
    try:
        auroc = float(roc_auc_score(y_true, y_pred_proba))
    except ValueError:
        auroc = 0.5

    # 3. Brier Score (Calibration Metric)
    brier = float(brier_score_loss(y_true, y_pred_proba))

    # 4. Optimal Threshold & F1
    if threshold is None:
        best_f1 = 0.0
        best_t = 0.5
        for t in np.linspace(0.01, 0.99, 99):
            preds = (y_pred_proba >= t).astype(int)
            score = f1_score(y_true, preds, zero_division=0)
            if score > best_f1:
                best_f1 = score
                best_t = t
        tuned_f1 = float(best_f1)
        used_threshold = float(best_t)
    else:
        preds = (y_pred_proba >= threshold).astype(int)
        tuned_f1 = float(f1_score(y_true, preds, zero_division=0))
        used_threshold = float(threshold)

    return {
        "n_samples": n_total,
        "n_positive": n_pos,
        "prevalence": round(prevalence, 6),
        "auprc": round(auprc, 6),
        "auroc": round(auroc, 6),
        "brier_score": round(brier, 6),
        "f1_tuned": round(tuned_f1, 6),
        "tuned_threshold": round(used_threshold, 4)
    }


def compute_ranking_metrics_at_k(
    Y_true: np.ndarray,
    Y_pred_proba: np.ndarray,
    k_values: List[int] = [3, 5, 10]
) -> Dict[str, float]:
    """
    Computes per-patient multi-disease ranking metrics across all K targets:
    Precision@K, Recall@K, and MAP@K.
    
    Args:
        Y_true: 2D binary matrix (n_samples, n_targets) of ground truth.
        Y_pred_proba: 2D probability matrix (n_samples, n_targets).
        k_values: List of K thresholds.
        
    Returns:
        Dict mapping metric names (e.g. 'precision_at_3', 'recall_at_5', 'map_at_10') to mean scores.
    """
    n_samples, n_targets = Y_true.shape
    ranking_results = {}

    # Sort target indices in descending order of predicted risk per patient
    top_indices = np.argsort(-Y_pred_proba, axis=1)

    for k in k_values:
        k_eff = min(k, n_targets)
        p_at_k = []
        r_at_k = []
        ap_at_k = []

        for i in range(n_samples):
            true_positives_idx = set(np.where(Y_true[i] == 1)[0])
            n_actual_pos = len(true_positives_idx)
            
            if n_actual_pos == 0:
                continue  # Skip patients with zero incident comorbidity events in evaluation window

            pred_top_k = top_indices[i, :k_eff]
            hits = [1 if idx in true_positives_idx else 0 for idx in pred_top_k]
            n_hits = sum(hits)

            # Precision@K = (# hits in top K) / K
            p_at_k.append(n_hits / k_eff)

            # Recall@K = (# hits in top K) / (total true positives)
            r_at_k.append(n_hits / n_actual_pos)

            # Average Precision @ K
            cum_hits = 0
            prec_sum = 0.0
            for rank_idx, hit in enumerate(hits):
                if hit:
                    cum_hits += 1
                    prec_sum += cum_hits / (rank_idx + 1)
            ap_at_k.append(prec_sum / min(n_actual_pos, k_eff) if min(n_actual_pos, k_eff) > 0 else 0.0)

        ranking_results[f"precision_at_{k}"] = round(float(np.mean(p_at_k)), 6) if p_at_k else 0.0
        ranking_results[f"recall_at_{k}"] = round(float(np.mean(r_at_k)), 6) if r_at_k else 0.0
        ranking_results[f"map_at_{k}"] = round(float(np.mean(ap_at_k)), 6) if ap_at_k else 0.0

    return ranking_results


def evaluate_multitarget_predictions(
    Y_true: np.ndarray,
    Y_pred_proba: np.ndarray,
    target_concept_ids: List[int],
    condition_metadata: Optional[Dict[int, Tuple[str, str, bool]]] = None
) -> Dict[str, Any]:
    """
    Evaluates complete multi-target prediction outputs across individual targets,
    macro averages, prevalence tiers, and multi-disease ranking metrics.
    """
    per_target_metrics = {}
    auprc_list = []
    auroc_list = []
    brier_list = []
    f1_list = []

    # Prevalence tier tracking
    tier_auprc = {"high": [], "medium": [], "low": []}

    for idx, cid in enumerate(target_concept_ids):
        y_t = Y_true[:, idx]
        y_p = Y_pred_proba[:, idx]
        metrics = compute_binary_metrics(y_t, y_p)
        per_target_metrics[str(cid)] = metrics

        auprc_list.append(metrics["auprc"])
        auroc_list.append(metrics["auroc"])
        brier_list.append(metrics["brier_score"])
        f1_list.append(metrics["f1_tuned"])

        # Classify into prevalence tiers (High: > 0.5%, Medium: 0.1%-0.5%, Low: < 0.1%)
        prev = metrics["prevalence"]
        if prev >= 0.005:
            tier_auprc["high"].append(metrics["auprc"])
        elif prev >= 0.001:
            tier_auprc["medium"].append(metrics["auprc"])
        else:
            tier_auprc["low"].append(metrics["auprc"])

    # Multi-disease ranking metrics
    ranking_metrics = compute_ranking_metrics_at_k(Y_true, Y_pred_proba, k_values=[3, 5, 10])

    summary = {
        "macro_metrics": {
            "macro_auprc": round(float(np.mean(auprc_list)), 6) if auprc_list else 0.0,
            "macro_auroc": round(float(np.mean(auroc_list)), 6) if auroc_list else 0.0,
            "macro_brier_score": round(float(np.mean(brier_list)), 6) if brier_list else 0.0,
            "macro_f1": round(float(np.mean(f1_list)), 6) if f1_list else 0.0,
            "n_targets": len(target_concept_ids)
        },
        "prevalence_tier_auprc": {
            "high_prevalence_macro_auprc": round(float(np.mean(tier_auprc["high"])), 6) if tier_auprc["high"] else 0.0,
            "medium_prevalence_macro_auprc": round(float(np.mean(tier_auprc["medium"])), 6) if tier_auprc["medium"] else 0.0,
            "low_prevalence_macro_auprc": round(float(np.mean(tier_auprc["low"])), 6) if tier_auprc["low"] else 0.0,
            "tier_counts": {
                "high": len(tier_auprc["high"]),
                "medium": len(tier_auprc["medium"]),
                "low": len(tier_auprc["low"])
            }
        },
        "ranking_metrics": ranking_metrics,
        "per_target": per_target_metrics
    }

    return summary
