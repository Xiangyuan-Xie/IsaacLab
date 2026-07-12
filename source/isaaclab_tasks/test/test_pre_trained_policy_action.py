# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for the pre-trained policy action term."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import torch


class _ActionTerm:
    def __init__(self, cfg, env) -> None:
        self.cfg = cfg
        self._env = env
        self.num_envs = env.num_envs
        self.device = env.device

    def reset(self, env_ids=None) -> None:
        pass


class _ObservationManager:
    def __init__(self, cfg, env) -> None:
        self.cfg = cfg
        self.env = env
        self.reset_env_ids = None

    def compute_group(self, _name: str) -> torch.Tensor:
        return self.env.low_level_observations

    def reset(self, env_ids=None) -> None:
        self.reset_env_ids = env_ids


class _LowLevelAction(_ActionTerm):
    def __init__(self, cfg, env) -> None:
        super().__init__(cfg, env)
        self.action_dim = cfg.action_dim
        self.processed = []
        self.apply_count = 0
        self.reset_env_ids = None

    def process_actions(self, actions: torch.Tensor) -> None:
        self.processed.append(actions.clone())

    def apply_actions(self) -> None:
        self.apply_count += 1

    def reset(self, env_ids=None) -> None:
        self.reset_env_ids = env_ids


class _Policy:
    def __init__(self, action_dim: int, explicit_state: bool) -> None:
        self.action_dim = action_dim
        self.explicit_state = explicit_state
        self.calls = []

    def to(self, _device: str):
        return self

    def eval(self):
        return self

    def __call__(self, observations: torch.Tensor, hidden_state: torch.Tensor | None = None):
        self.calls.append((observations.clone(), None if hidden_state is None else hidden_state.clone()))
        actions = observations[:, : self.action_dim]
        if self.explicit_state:
            return actions, hidden_state + 1.0
        return actions


def _load_action_module(monkeypatch):
    managers = types.ModuleType("isaaclab.managers")
    managers.ActionTerm = _ActionTerm
    managers.ObservationManager = _ObservationManager

    math = types.ModuleType("isaaclab.utils.math")
    markers = types.ModuleType("isaaclab.markers")
    markers.VisualizationMarkers = object
    marker_cfg = types.ModuleType("isaaclab.markers.config")
    marker_cfg.BLUE_ARROW_X_MARKER_CFG = object()
    marker_cfg.GREEN_ARROW_X_MARKER_CFG = object()
    assets = types.ModuleType("isaaclab.utils.assets")
    assets.check_file_path = lambda _path: True
    assets.read_file = lambda _path: b"policy"

    isaaclab = types.ModuleType("isaaclab")
    isaaclab.__path__ = []
    utils = types.ModuleType("isaaclab.utils")
    utils.__path__ = []
    utils.math = math
    marker_package = types.ModuleType("isaaclab.markers")
    marker_package.__path__ = []
    marker_package.VisualizationMarkers = object

    package_name = "_pre_trained_policy_action_test"
    package = types.ModuleType(package_name)
    package.__path__ = []
    cfg_module = types.ModuleType(f"{package_name}.pre_trained_policy_action_cfg")
    cfg_module.PreTrainedPolicyActionCfg = object

    for name, module in {
        "isaaclab": isaaclab,
        "isaaclab.managers": managers,
        "isaaclab.utils": utils,
        "isaaclab.utils.math": math,
        "isaaclab.utils.assets": assets,
        "isaaclab.markers": marker_package,
        "isaaclab.markers.config": marker_cfg,
        package_name: package,
        f"{package_name}.pre_trained_policy_action_cfg": cfg_module,
    }.items():
        monkeypatch.setitem(sys.modules, name, module)

    source_path = (
        Path(__file__).parents[1]
        / "isaaclab_tasks"
        / "manager_based"
        / "navigation"
        / "mdp"
        / "pre_trained_policy_action.py"
    )
    module_name = f"{package_name}.pre_trained_policy_action"
    spec = importlib.util.spec_from_file_location(module_name, source_path)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _make_cfg(*, action_dim: int = 3, state_shape: tuple[int, int] | None = None, low_level_decimation: int = 2):
    observations = SimpleNamespace(actions=SimpleNamespace(), velocity_commands=SimpleNamespace())
    return SimpleNamespace(
        asset_name="robot",
        policy_path="policy.jit",
        action_dim=action_dim,
        recurrent_state_shape=state_shape,
        low_level_decimation=low_level_decimation,
        low_level_actions=SimpleNamespace(class_type=_LowLevelAction, action_dim=2),
        low_level_observations=observations,
    )


def _make_env(num_envs: int = 3):
    return SimpleNamespace(
        num_envs=num_envs,
        device="cpu",
        scene={"robot": SimpleNamespace()},
        low_level_observations=torch.arange(num_envs * 4, dtype=torch.float32).view(num_envs, 4),
        episode_length_buf=torch.ones(num_envs),
    )


def test_legacy_single_input_policy_remains_compatible(monkeypatch) -> None:
    """Single-input policies should preserve navigation behavior and decimation."""
    module = _load_action_module(monkeypatch)
    policy = _Policy(action_dim=2, explicit_state=False)
    monkeypatch.setattr(torch.jit, "load", lambda _file: policy)
    action = module.PreTrainedPolicyAction(_make_cfg(), _make_env())

    action.process_actions(torch.ones(3, 3))
    for _ in range(5):
        action.apply_actions()

    assert action.action_dim == 3
    assert len(policy.calls) == 3
    assert action._low_level_action_term.apply_count == 5


def test_explicit_state_policy_supports_custom_action_dim_and_partial_reset(monkeypatch) -> None:
    """Explicit GRU state should be caller-owned and reset per environment."""
    module = _load_action_module(monkeypatch)
    policy = _Policy(action_dim=2, explicit_state=True)
    monkeypatch.setattr(torch.jit, "load", lambda _file: policy)
    action = module.PreTrainedPolicyAction(_make_cfg(action_dim=4, state_shape=(2, 5)), _make_env())

    action.process_actions(torch.ones(3, 4))
    action.apply_actions()
    assert action.action_dim == 4
    assert torch.equal(action.policy_state, torch.ones(2, 3, 5))

    action.reset(env_ids=torch.tensor([1]))

    assert torch.equal(action.policy_state[:, 0], torch.ones(2, 5))
    assert torch.equal(action.policy_state[:, 1], torch.zeros(2, 5))
    assert torch.equal(action.policy_state[:, 2], torch.ones(2, 5))
    assert torch.equal(action.low_level_actions[1], torch.zeros(2))


def test_low_level_observation_binding_is_overridable(monkeypatch) -> None:
    """Specialized actions should be able to replace navigation observation bindings."""
    module = _load_action_module(monkeypatch)
    monkeypatch.setattr(torch.jit, "load", lambda _file: _Policy(action_dim=2, explicit_state=False))

    class SpecializedAction(module.PreTrainedPolicyAction):
        def _bind_low_level_observations(self) -> None:
            self.binding_was_overridden = True

    action = SpecializedAction(_make_cfg(), _make_env())

    assert action.binding_was_overridden
