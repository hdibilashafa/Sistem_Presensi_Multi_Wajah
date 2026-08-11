
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')                                                              
import matplotlib.pyplot as plt
from config import Config

THRESHOLD_RANGE = np.arange(0.1, 0.95, 0.05)                         


def compute_roc(genuine_scores, impostor_scores):
    roc_table = []

    for t in THRESHOLD_RANGE:
                                                                      
        tp = int(np.sum(genuine_scores >= t))
        fn = int(np.sum(genuine_scores < t))

                                                                 
        fp = int(np.sum(impostor_scores >= t))
        tn = int(np.sum(impostor_scores < t))

        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        roc_table.append({
            'threshold': round(float(t), 2),
            'tp': tp, 'tn': tn, 'fp': fp, 'fn': fn,
            'tpr': round(tpr, 4),
            'fpr': round(fpr, 4)
        })

    auc_value = _compute_auc(roc_table)
    return roc_table, auc_value


def _compute_auc(roc_table):
    sorted_table = sorted(roc_table, key=lambda r: r['fpr'])
    fpr_vals = [r['fpr'] for r in sorted_table]
    tpr_vals = [r['tpr'] for r in sorted_table]
    auc_value = np.trapz(tpr_vals, fpr_vals)
    return float(auc_value)


def find_optimal_threshold(roc_table):
    best = None
    for row in roc_table:
        j = row['tpr'] - row['fpr']
        if best is None or j > best['youden_index']:
            best = {
                'threshold': row['threshold'],
                'tpr': row['tpr'],
                'fpr': row['fpr'],
                'youden_index': j
            }
    return best


def plot_roc_curve(roc_table, auc_value, optimal):
    sorted_table = sorted(roc_table, key=lambda r: r['fpr'])
    fpr_vals = [r['fpr'] for r in sorted_table]
    tpr_vals = [r['tpr'] for r in sorted_table]

    plt.figure(figsize=(6, 6))
    plt.plot(fpr_vals, tpr_vals, marker='o', linewidth=2, label=f'Kurva ROC (AUC = {auc_value:.4f})')
    plt.plot([0, 1], [0, 1], linestyle='--', color='gray', label='Random Guess (AUC = 0.5)')
    plt.scatter([optimal['fpr']], [optimal['tpr']], color='red', s=100, zorder=5,
                label=f"Threshold Optimal = {optimal['threshold']}")

    plt.xlabel('False Positive Rate (FPR)')
    plt.ylabel('True Positive Rate (TPR)')
    plt.title('Kurva ROC - Penentuan Threshold Optimal')
    plt.legend(loc='lower right')
    plt.grid(alpha=0.3)
    plt.tight_layout()

    output_dir = os.path.join(Config.BASE_DIR, 'static', 'img')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'roc_curve.png')
    plt.savefig(output_path, dpi=120)
    plt.close()

    return output_path
