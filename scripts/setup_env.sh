#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Setting up NetBox Sync environment..."
echo "Repository: ${ROOT_DIR}"

python -m venv "${ROOT_DIR}/.venv"
source "${ROOT_DIR}/.venv/bin/activate"

python -m pip install --upgrade pip
pip install -r "${ROOT_DIR}/requirements.txt"
pip install -r "${ROOT_DIR}/requirements-dev.txt"

echo
echo "Environment ready."
echo "Activate with: source ${ROOT_DIR}/.venv/bin/activate"
