#!/usr/bin/env bash

# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

# Exit on error.
set -e

# Get repo directory.
export ISAACLAB_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Find python to run CLI.
if [ -n "$VIRTUAL_ENV" ]; then
    python_exe="$VIRTUAL_ENV/bin/python"
elif [ -n "$CONDA_PREFIX" ]; then
    python_exe="$CONDA_PREFIX/bin/python"
elif [ -f "$ISAACLAB_PATH/env_isaaclab/bin/python" ]; then
    python_exe="$ISAACLAB_PATH/env_isaaclab/bin/python"
elif [ -f "$ISAACLAB_PATH/_isaac_sim/python.sh" ]; then
    python_exe="$ISAACLAB_PATH/_isaac_sim/python.sh"
else
    # Fallback to system python
    python_exe="python3"
fi

# Add source/isaaclab to PYTHONPATH so we can import isaaclab.cli.
if [ -n "${PYTHONPATH:-}" ]; then
    export PYTHONPATH="$ISAACLAB_PATH/source/isaaclab:$PYTHONPATH"
else
    export PYTHONPATH="$ISAACLAB_PATH/source/isaaclab"
fi

# Let Kit associate direct wrapper launches with the Isaac Sim desktop icon.
export RESOURCE_NAME="${RESOURCE_NAME:-IsaacSim}"

# If a local Isaac Sim binary is present, source its env setup so that
# PYTHONPATH/PATH/EXP_PATH are correct without depending on a conda
# activate.d hook (those don't fire reliably under e.g. `conda run`).
if [ -d "$ISAACLAB_PATH/_isaac_sim" ]; then
    if [ -f "$ISAACLAB_PATH/_isaac_sim/setup_conda_env.sh" ]; then
        # shellcheck disable=SC1091
        . "$ISAACLAB_PATH/_isaac_sim/setup_conda_env.sh" >/dev/null 2>&1 || true
    elif [ -f "$ISAACLAB_PATH/_isaac_sim/setup_python_env.sh" ]; then
        export CARB_APP_PATH="$ISAACLAB_PATH/_isaac_sim/kit"
        export ISAAC_PATH="$ISAACLAB_PATH/_isaac_sim"
        export EXP_PATH="$ISAACLAB_PATH/_isaac_sim/apps"

        _isaaclab_source_setup_python_env() {
            if [ -n "${ZSH_VERSION:-}" ]; then
                emulate -L zsh -o KSH_ARRAYS
                typeset -a BASH_SOURCE
                BASH_SOURCE=("$ISAACLAB_PATH/_isaac_sim/setup_python_env.sh")
            fi
            # shellcheck disable=SC1091
            . "$ISAACLAB_PATH/_isaac_sim/setup_python_env.sh"
        }
        _isaaclab_source_setup_python_env
        unset -f _isaaclab_source_setup_python_env

        _isaaclab_strip_path_entries() {
            if [ -n "${ZSH_VERSION:-}" ]; then
                emulate -L sh
            fi
            _isaaclab_var_name="$1"
            _isaaclab_reject_prefix="$2"
            eval "_isaaclab_path_value=\${$_isaaclab_var_name-}"
            _isaaclab_new_path=""
            _isaaclab_old_ifs="$IFS"
            IFS=":"
            for _isaaclab_entry in $_isaaclab_path_value; do
                [ -z "$_isaaclab_entry" ] && continue
                case "$_isaaclab_entry" in
                    "$_isaaclab_reject_prefix"|$_isaaclab_reject_prefix/*) continue ;;
                esac
                if [ -n "$_isaaclab_new_path" ]; then
                    _isaaclab_new_path="$_isaaclab_new_path:$_isaaclab_entry"
                else
                    _isaaclab_new_path="$_isaaclab_entry"
                fi
            done
            IFS="$_isaaclab_old_ifs"
            export "$_isaaclab_var_name=$_isaaclab_new_path"
            unset _isaaclab_var_name _isaaclab_reject_prefix _isaaclab_path_value
            unset _isaaclab_new_path _isaaclab_old_ifs _isaaclab_entry
        }
        _isaaclab_strip_path_entries PYTHONPATH "$ISAACLAB_PATH/_isaac_sim/kit/python/lib/python3.12"
        unset -f _isaaclab_strip_path_entries
    else
        echo "[WARNING] _isaac_sim is present but no supported Isaac Sim env setup script was found; Isaac Sim env vars not exported." >&2
        echo "[WARNING] Re-extract the Isaac Sim binary zip if you intend to use the bundled binary." >&2
    fi
fi

# Execute CLI.
exec "$python_exe" -c "from isaaclab.cli import cli; cli()" "$@"
