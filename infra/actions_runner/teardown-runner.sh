#!/usr/bin/env bash
set -euo pipefail

# Usage: ./teardown-runner.sh <REMOVAL_TOKEN>
# Get the token by clicking remove runner:
#  https://github.com/RobinMatter6/de2-project/settings/actions/runners

RUNNER_DIR="$HOME/actions-runner"

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <REMOVAL_TOKEN>" >&2
  exit 1
fi

if [[ ! -d "$RUNNER_DIR" ]]; then
  echo "no runner at $RUNNER_DIR"
  exit 0
fi

cd "$RUNNER_DIR"
[[ -f .service ]] && { sudo ./svc.sh stop || true; sudo ./svc.sh uninstall || true; }
[[ -f .runner ]]  && ./config.sh remove --token "$1"
cd "$HOME"
rm -rf "$RUNNER_DIR"
