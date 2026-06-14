# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path

from isaaclab.cli.commands import envs


def test_conda_shell_hook_supports_isaac_sim_binary_python_env(tmp_path):
    conda_prefix = tmp_path / "env"

    envs._create_conda_envhooks_shell(conda_prefix)

    hook = (conda_prefix / "etc" / "conda" / "activate.d" / "setenv.sh").read_text(encoding="utf-8")

    isaacsim_root = envs.ISAACLAB_ROOT / "_isaac_sim"
    setup_conda_env = isaacsim_root / "setup_conda_env.sh"
    setup_python_env = isaacsim_root / "setup_python_env.sh"

    assert f'export CARB_APP_PATH="{isaacsim_root / "kit"}"' in hook
    assert f'export ISAAC_PATH="{isaacsim_root}"' in hook
    assert f'export EXP_PATH="{isaacsim_root / "apps"}"' in hook
    assert f'export ISAAC_PATH="{isaacsim_root}"' in hook
    assert 'export PYTHONPATH="${PYTHONPATH}:' not in hook
    assert "6312fa25" not in hook
    assert f'[ -f "{setup_conda_env}" ]' in hook
    assert f'[ -f "{setup_python_env}" ]' in hook
    assert f'. "{setup_python_env}"' in hook
    assert "setup_python_env.sh" in hook
    assert "_isaaclab_strip_path_entries" in hook


def test_uv_shell_hook_supports_isaac_sim_binary_python_env(tmp_path):
    env_path = tmp_path / "venv"
    activate = env_path / "bin" / "activate"
    activate.parent.mkdir(parents=True)
    activate.write_text("#!/usr/bin/env bash\n", encoding="utf-8")

    envs._create_uv_envhooks_shell(env_path)

    hook = activate.read_text(encoding="utf-8")

    isaacsim_root = Path(envs.ISAACLAB_ROOT) / "_isaac_sim"
    setup_python_env = isaacsim_root / "setup_python_env.sh"

    assert f'export EXP_PATH="{isaacsim_root / "apps"}"' in hook
    assert f'export ISAAC_PATH="{isaacsim_root}"' in hook
    assert 'export PYTHONPATH="${PYTHONPATH}:' not in hook
    assert "6312fa25" not in hook
    assert f'[ -f "{setup_python_env}" ]' in hook
    assert f'. "{setup_python_env}"' in hook
    assert "setup_python_env.sh" in hook
    assert "_isaaclab_strip_path_entries" in hook
