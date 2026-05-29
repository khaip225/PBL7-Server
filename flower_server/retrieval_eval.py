"""Cross-modal retrieval evaluation.

Computes Audio->Image and Image->Audio retrieval metrics
using cosine similarity in the shared 256-d embedding space.
"""

import numpy as np
import torch
import torch.nn.functional as F


def compute_retrieval_metrics(image_embeddings, audio_embeddings,
                               image_labels, audio_labels, k_values=(1, 5)):
    """Evaluate cross-modal retrieval.

    Args:
        image_embeddings: (N_img, D) L2-normalized
        audio_embeddings: (N_aud, D) L2-normalized
        image_labels: (N_img, 3) multi-label disease labels
        audio_labels: (N_aud, 2) multi-label acoustic labels
        k_values: recall cutoff values

    Returns:
        dict with Recall@k, mAP, NDCG for both directions
    """
    # Cosine similarity matrices
    sim = torch.matmul(audio_embeddings, image_embeddings.T)  # (N_aud, N_img)

    # Relevance: audio crackle matches image pneumonia or fibrosis
    # audio wheeze matches image copd
    crackle_relevance = (image_labels[:, 0] > 0.5) | (image_labels[:, 2] > 0.5)  # Pneumonia or Fibrosis
    wheeze_relevance = image_labels[:, 1] > 0.5  # COPD

    relevance_a2i = []
    for i in range(len(audio_embeddings)):
        has_crackle = audio_labels[i, 0] > 0.5
        has_wheeze = audio_labels[i, 1] > 0.5
        if has_crackle and has_wheeze:
            rel = crackle_relevance | wheeze_relevance
        elif has_crackle:
            rel = crackle_relevance
        elif has_wheeze:
            rel = wheeze_relevance
        else:
            rel = torch.zeros(len(image_embeddings), dtype=torch.bool)
        relevance_a2i.append(rel.float())
    relevance_a2i = torch.stack(relevance_a2i)  # (N_aud, N_img)

    results = {}
    results.update(_compute_direction(sim, relevance_a2i, k_values, "Audio_to_Image"))

    # Image -> Audio
    sim_i2a = sim.T  # (N_img, N_aud)

    audio_has_crackle = audio_labels[:, 0] > 0.5
    audio_has_wheeze = audio_labels[:, 1] > 0.5
    relevance_i2a = []
    for i in range(len(image_embeddings)):
        has_pneu = image_labels[i, 0] > 0.5
        has_copd = image_labels[i, 1] > 0.5
        has_fibr = image_labels[i, 2] > 0.5
        rel = torch.zeros(len(audio_embeddings))
        if has_pneu or has_fibr:
            rel = rel + audio_has_crackle.float()
        if has_copd:
            rel = rel + audio_has_wheeze.float()
        rel = (rel > 0).float()
        relevance_i2a.append(rel)
    relevance_i2a = torch.stack(relevance_i2a)

    results.update(_compute_direction(sim_i2a, relevance_i2a, k_values, "Image_to_Audio"))

    return results


def _compute_direction(sim_matrix, relevance, k_values, name):
    """Compute metrics for one retrieval direction."""
    results = {}
    N = sim_matrix.shape[0]

    # Recall@k
    for k in k_values:
        _, topk_indices = sim_matrix.topk(k, dim=1)
        recall = 0.0
        for i in range(N):
            if relevance[i].sum() > 0:
                hits = relevance[i][topk_indices[i]].sum().item()
                recall += min(hits, 1.0) / max(relevance[i].sum().item(), 1.0)
        results[f"{name}_Recall@{k}"] = float(recall / N) if N > 0 else 0.0

    # mAP
    sorted_indices = sim_matrix.argsort(dim=1, descending=True)
    ap_sum = 0.0
    valid_queries = 0
    for i in range(N):
        if relevance[i].sum() == 0:
            continue
        valid_queries += 1
        rel_sorted = relevance[i][sorted_indices[i]]
        precisions = torch.cumsum(rel_sorted, dim=0) / torch.arange(1, len(rel_sorted) + 1, device=rel_sorted.device)
        ap = (precisions * rel_sorted).sum() / max(relevance[i].sum(), 1.0)
        ap_sum += ap.item()
    results[f"{name}_mAP"] = float(ap_sum / max(valid_queries, 1))

    # NDCG@5
    k5 = min(5, sim_matrix.shape[1])
    ndcg_sum = 0.0
    valid_ndcg = 0
    for i in range(N):
        if relevance[i].sum() == 0:
            continue
        valid_ndcg += 1
        _, topk = sim_matrix[i].topk(k5)
        rel_topk = relevance[i][topk].float()
        dcg = (rel_topk / torch.log2(torch.arange(2, k5 + 2, device=rel_topk.device))).sum()
        ideal_rel = relevance[i].float().sort(descending=True)[0][:k5]
        idcg = (ideal_rel / torch.log2(torch.arange(2, k5 + 2, device=ideal_rel.device))).sum()
        ndcg = dcg / (idcg + 1e-8)
        ndcg_sum += ndcg.item()
    results[f"{name}_NDCG@5"] = float(ndcg_sum / max(valid_ndcg, 1))

    return results
