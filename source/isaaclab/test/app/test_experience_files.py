# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path


def test_headless_experience_loads_omni_usd():
    app_file = Path(__file__).parents[4] / "apps" / "isaaclab.python.headless.kit"

    content = app_file.read_text(encoding="utf-8")

    assert '"omni.usd" = {}' in content


def test_gui_experience_loads_omni_usd():
    app_file = Path(__file__).parents[4] / "apps" / "isaaclab.python.kit"

    content = app_file.read_text(encoding="utf-8")

    assert '"omni.usd" = {}' in content
