# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

import builtins

from isaaclab.app import app_launcher


def test_isaac_sim_version_detection_falls_back_to_isaac_path_when_module_missing(tmp_path, monkeypatch):
    isaacsim_root = tmp_path / "isaacsim"
    isaacsim_root.mkdir()
    (isaacsim_root / "VERSION").write_text("6.0.0-rc.59\n", encoding="utf-8")

    monkeypatch.setenv("ISAAC_PATH", str(isaacsim_root))
    monkeypatch.delattr(app_launcher, "isaacsim", raising=False)
    monkeypatch.setattr(app_launcher.importlib.util, "find_spec", lambda name: None)

    launcher = app_launcher.AppLauncher.__new__(app_launcher.AppLauncher)

    assert launcher.is_isaac_sim_version_5() is False


def test_isaac_sim_version_detection_recognizes_version_5_from_isaac_path(tmp_path, monkeypatch):
    isaacsim_root = tmp_path / "isaacsim"
    isaacsim_root.mkdir()
    (isaacsim_root / "VERSION").write_text("5.1.0\n", encoding="utf-8")

    monkeypatch.setenv("ISAAC_PATH", str(isaacsim_root))
    monkeypatch.delattr(app_launcher, "isaacsim", raising=False)
    monkeypatch.setattr(app_launcher.importlib.util, "find_spec", lambda name: None)

    launcher = app_launcher.AppLauncher.__new__(app_launcher.AppLauncher)

    assert launcher.is_isaac_sim_version_5() is True


def test_app_launcher_reports_clear_error_when_simulation_app_is_missing(monkeypatch):
    monkeypatch.delattr(app_launcher, "SimulationApp", raising=False)
    monkeypatch.delattr(app_launcher, "isaacsim", raising=False)

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "isaacsim" or name.startswith("isaacsim."):
            raise ImportError("isaacsim hidden for test")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    try:
        app_launcher.AppLauncher({"headless": True})
    except RuntimeError as exc:
        assert "Isaac Sim Python modules are not importable" in str(exc)
        assert "ISAAC_PATH" in str(exc)
        assert "EXP_PATH" in str(exc)
    else:
        raise AssertionError("Expected AppLauncher to fail before config resolution")
