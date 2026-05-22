#!/usr/bin/env bash
set -euo pipefail

# Usage: ./setup-runner.sh <REGISTRATION_TOKEN>
# Get a fresh token from:
#   https://github.com/RobinMatter6/de2-project/settings/actions/runners/new

RUNNER_VERSION="2.334.0"
REPO_URL="https://github.com/RobinMatter6/de2-project"
RUNNER_DIR="$HOME/actions-runner"
TARBALL="actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${TARBALL}"

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <REGISTRATION_TOKEN>" >&2
  exit 1
fi

TOKEN="$1"
NAME="$(hostname)"

if [[ -d "$RUNNER_DIR" ]]; then
  pushd "$RUNNER_DIR" >/dev/null
  [[ -f .service ]] && { sudo ./svc.sh stop || true; sudo ./svc.sh uninstall || true; }
  [[ -f .runner ]]  && { ./config.sh remove --token "$TOKEN" || true; }
  popd >/dev/null
  rm -rf "$RUNNER_DIR"
fi

sudo apt-get update
sudo apt-get install -y curl tar libicu70

mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"
curl -fL -o "$TARBALL" "$URL"
tar xzf "./$TARBALL"
rm -f "$TARBALL"

./config.sh --unattended --replace \
  --url "$REPO_URL" --token "$TOKEN" \
  --name "$NAME" --labels "self-hosted,linux,x64"

sudo ./svc.sh install "$USER"
sudo ./svc.sh start

echo "runner '${NAME}' registered. ${REPO_URL}/settings/actions/runners"