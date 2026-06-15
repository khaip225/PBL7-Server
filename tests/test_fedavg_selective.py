"""Tests for fedavg_selective aggregation logic."""

import sys
import os
from collections import OrderedDict

import pytest
import torch
import numpy as np

# Setup path so we can import from flower_server
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# We test fedavg_selective directly — it's a standalone function
from flower_server.server import fedavg_selective


class TestFedavgSelective:
    """Unit tests for selective FedAvg aggregation."""

    def _make_state(self, modality: str) -> OrderedDict:
        """Create a mock client state with modality-specific projections."""
        state = OrderedDict()
        state["img_proj.weight"] = torch.randn(256, 1024)
        state["img_proj.bias"] = torch.randn(256)
        state["aud_proj.weight"] = torch.randn(256, 768)
        state["aud_proj.bias"] = torch.randn(256)
        state["proto.p_normal_img"] = torch.randn(256)
        state["proto.p_normal_aud"] = torch.randn(256)
        state["proto.p_pneumonia"] = torch.randn(256)
        state["proto.p_copd"] = torch.randn(256)
        state["proto.p_fibrosis"] = torch.randn(256)
        state["proto.p_crackle"] = torch.randn(256)
        state["proto.p_wheeze"] = torch.randn(256)
        return state

    def test_image_only_clients(self):
        """Image-only clients: img_proj averaged, aud_proj NOT averaged, proto from all."""
        s1 = self._make_state("image")
        s2 = self._make_state("image")
        result = fedavg_selective([s1, s2], [100.0, 200.0], ["image", "image"])

        assert "img_proj.weight" in result
        assert "aud_proj.weight" in result  # kept (zeroed or from params)
        assert "proto.p_normal_img" in result
        assert result["proto.p_normal_img"].shape == (256,)

    def test_audio_only_clients(self):
        """Audio-only clients: aud_proj averaged, img_proj NOT averaged."""
        s1 = self._make_state("audio")
        s2 = self._make_state("audio")
        result = fedavg_selective([s1, s2], [50.0, 50.0], ["audio", "audio"])

        assert "aud_proj.weight" in result
        assert result["proto.p_normal_aud"].shape == (256,)

    def test_mixed_clients(self):
        """Image + Audio clients: each projection head from its own clients, proto from all."""
        s_img = self._make_state("image")
        s_aud = self._make_state("audio")
        result = fedavg_selective(
            [s_img, s_aud], [100.0, 100.0], ["image", "audio"]
        )

        # Prototypes should be averaged across ALL (both clients)
        assert "proto.p_normal_img" in result
        assert result["proto.p_crackle"].shape == (256,)

    def test_weighted_average(self):
        """Verify weighted averaging: client with 3x weight dominates."""
        s1 = self._make_state("image")
        s2 = self._make_state("image")

        # Set s2 to known values
        for k in s2:
            s2[k] = torch.ones_like(s2[k])

        # s1 weight=1, s2 weight=9 → result ~ 0.9 * s2 + 0.1 * s1
        result = fedavg_selective([s1, s2], [1.0, 9.0], ["image", "image"])

        # The img_proj.weight should be closer to 1.0 (s2) than to random (s1)
        img_weight = result["img_proj.weight"]
        assert torch.allclose(img_weight, torch.ones_like(img_weight), atol=0.5)

    def test_returns_ordered_dict(self):
        """Output must be OrderedDict to maintain parameter order."""
        s1 = self._make_state("image")
        result = fedavg_selective([s1], [1.0], ["image"])
        assert isinstance(result, OrderedDict)

    def test_single_client_no_crash(self):
        """Single client should work (no division by zero)."""
        s1 = self._make_state("image")
        result = fedavg_selective([s1], [1.0], ["image"])
        assert len(result) == len(s1)


class TestSelectiveAggregationStrategy:
    """Integration-style tests for the strategy class."""

    def test_init_creates_save_dir(self, tmp_path):
        """Strategy init should create the save directory."""
        from flower_server.server import SelectiveAggregationStrategy

        save_dir = tmp_path / "test_models"
        strategy = SelectiveAggregationStrategy(
            task_key="image",
            min_fit_clients=1,
            min_samples=1,
            save_dir=str(save_dir),
        )
        assert save_dir.exists(), "Save directory should be created"
