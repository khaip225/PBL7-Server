"""Prototype visualization utilities.

Generates t-SNE plots of prototype positions and cosine similarity evolution
across FL rounds for monitoring prototype alignment training.
"""

import numpy as np
import os


def compute_prototype_similarities(prototype_positions):
    """Compute pairwise cosine similarity matrix for all prototypes.

    Args:
        prototype_positions: dict with keys 'all' (5, 256) and 'names'

    Returns:
        dict with similarity values for key ontology pairs
    """
    all_protos = prototype_positions['all']
    # L2-normalize
    norms = np.linalg.norm(all_protos, axis=1, keepdims=True)
    normalized = all_protos / (norms + 1e-8)
    sim_matrix = normalized @ normalized.T

    names = prototype_positions.get('names', [])
    result = {'similarity_matrix': sim_matrix.tolist()}

    for i, n1 in enumerate(names):
        for j, n2 in enumerate(names):
            if i < j:
                result[f"{n1}_{n2}"] = float(sim_matrix[i, j])

    return result


def compute_ontology_alignment_score(prototype_positions):
    """Score how well prototypes align with ontology constraints.

    Positive: crackle-pneumonia, crackle-fibrosis, wheeze-copd (should be high)
    Negative: crackle-copd, wheeze-pneumonia, wheeze-fibrosis (should be low)
    """
    all_protos = prototype_positions['all']
    norms = np.linalg.norm(all_protos, axis=1, keepdims=True)
    normalized = all_protos / (norms + 1e-8)
    sim = normalized @ normalized.T

    positive_pairs = [(3, 0), (3, 2), (4, 1)]  # crackle-pneu, crackle-fibr, wheeze-copd
    negative_pairs = [(3, 1), (4, 0), (4, 2)]

    pos_score = np.mean([sim[a, d] for a, d in positive_pairs])
    neg_score = np.mean([sim[a, d] for a, d in negative_pairs])

    return {
        'ontology_alignment_score': float(pos_score - neg_score),
        'positive_mean_similarity': float(pos_score),
        'negative_mean_similarity': float(neg_score),
    }


def save_prototype_evolution(round_history, output_dir):
    """Save prototype evolution data as JSON for external visualization.

    Args:
        round_history: list of dicts from get_prototype_positions() per round
        output_dir: directory to save JSON files
    """
    import json
    os.makedirs(output_dir, exist_ok=True)

    evolution = {
        'rounds': [],
        'similarities': [],
        'alignment_scores': [],
    }

    for i, positions in enumerate(round_history):
        evolution['rounds'].append({
            'round': i,
            'positions': positions['all'].tolist(),
            'names': positions['names'],
        })
        evolution['similarities'].append(compute_prototype_similarities(positions))
        evolution['alignment_scores'].append(compute_ontology_alignment_score(positions))

    path = os.path.join(output_dir, 'prototype_evolution.json')
    with open(path, 'w') as f:
        json.dump(evolution, f, indent=2)

    return path
