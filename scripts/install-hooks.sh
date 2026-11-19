#!/usr/bin/env bash
# Use the repo's hooks (.githooks/) for this clone. Needs only git and python3.
set -euo pipefail
cd "$(dirname "$0")/.."
git config core.hooksPath .githooks
echo "Hooks enabled: $(git config core.hooksPath)"
