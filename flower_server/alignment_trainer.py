"""Prototype alignment training orchestrator.

Combines 5 loss components:
1. Supervised contrastive: image -> disease prototypes
2. Supervised contrastive: audio -> acoustic prototypes
3. Prototype consistency loss
4. Ontology regularization loss
5. Hard negative mining loss (cross-modal)
"""

import sys
import os
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.prototypes import (
    DiseasePrototypes, AcousticPrototypes, OntologyBridge,
    supervised_contrastive_loss, prototype_consistency_loss,
    ontology_regularization_loss, EmbeddingMemoryBank,
)


class PrototypeAlignmentTrainer:
    def __init__(self, image_model, audio_model, device, temperature=0.07, queue_size=1024):
        self.image_model = image_model
        self.audio_model = audio_model
        self.device = device
        self.temperature = temperature

        self.disease_protos = DiseasePrototypes(embedding_dim=256).to(device)
        self.acoustic_protos = AcousticPrototypes(embedding_dim=256).to(device)
        self.memory_bank = EmbeddingMemoryBank(dim=256, queue_size=queue_size)

    def train_step(self, image_batch, image_labels, audio_batch, audio_labels):
        """One alignment training step.

        Args:
            image_batch: (B, 3, 224, 224) X-ray images
            image_labels: (B, 3) multi-label [pneumonia, copd, fibrosis]
            audio_batch: (B, 3, 224, 224) mel spectrogram images
            audio_labels: (B, 2) multi-label [crackle, wheeze]

        Returns:
            total_loss, loss_dict
        """
        image_batch = image_batch.to(self.device)
        image_labels = image_labels.to(self.device)
        audio_batch = audio_batch.to(self.device)
        audio_labels = audio_labels.to(self.device)

        # 1. Get normalized embeddings
        img_emb = self.image_model.get_embedding(image_batch)
        aud_emb = self.audio_model.get_embedding(audio_batch)

        # 2. Get current prototypes
        disease_protos = self.disease_protos()
        acoustic_protos = self.acoustic_protos()

        # 3. Supervised contrastive: image -> disease prototypes
        loss_img = supervised_contrastive_loss(
            img_emb, image_labels, disease_protos, self.temperature
        )

        # 4. Supervised contrastive: audio -> acoustic prototypes
        loss_aud = supervised_contrastive_loss(
            aud_emb, audio_labels, acoustic_protos, self.temperature
        )

        # 5. Prototype consistency loss
        loss_proto = prototype_consistency_loss(disease_protos, acoustic_protos)

        # 6. Ontology regularization
        loss_onto = ontology_regularization_loss(disease_protos, acoustic_protos)

        # 7. Hard negative mining from memory bank (cross-modal)
        hard_img = self.memory_bank.get_hard_negatives(img_emb, modality='image')
        hard_aud = self.memory_bank.get_hard_negatives(aud_emb, modality='audio')
        loss_hard = torch.tensor(0.0, device=self.device)
        if hard_img is not None and hard_img.shape[0] > 0:
            sim = torch.matmul(img_emb, hard_img.T) / self.temperature
            loss_hard = loss_hard + sim.mean()
        if hard_aud is not None and hard_aud.shape[0] > 0:
            sim = torch.matmul(aud_emb, hard_aud.T) / self.temperature
            loss_hard = loss_hard + sim.mean()

        # 8. Total loss
        total = loss_img + loss_aud + 0.3 * loss_proto + 0.2 * loss_onto + 0.1 * loss_hard

        # 9. Update memory bank
        self.memory_bank.enqueue_image(img_emb, image_labels)
        self.memory_bank.enqueue_audio(aud_emb, audio_labels)

        loss_dict = {
            "loss_img": loss_img.item(),
            "loss_aud": loss_aud.item(),
            "loss_proto": loss_proto.item(),
            "loss_onto": loss_onto.item(),
            "loss_hard": loss_hard.item(),
            "total": total.item(),
        }
        return total, loss_dict

    def get_prototype_positions(self):
        """Return current prototype positions for visualization."""
        disease = self.disease_protos().detach().cpu()
        acoustic = self.acoustic_protos().detach().cpu()
        all_protos = torch.cat([disease, acoustic], dim=0)
        return {
            "disease": disease.numpy(),
            "acoustic": acoustic.numpy(),
            "all": all_protos.numpy(),
            "names": ["P_pneumonia", "P_copd", "P_fibrosis", "P_crackle", "P_wheeze"],
        }

    def get_prototype_similarities(self):
        """Cross-modal prototype similarity matrix."""
        disease = self.disease_protos()
        acoustic = self.acoustic_protos()
        sim = torch.matmul(acoustic, disease.T)
        return {
            "crackle_pneumonia": float(sim[0, 0]),
            "crackle_copd": float(sim[0, 1]),
            "crackle_fibrosis": float(sim[0, 2]),
            "wheeze_pneumonia": float(sim[1, 0]),
            "wheeze_copd": float(sim[1, 1]),
            "wheeze_fibrosis": float(sim[1, 2]),
        }
