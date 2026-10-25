#!/bin/sh
# Builds Fork's base checkpoint inside a fresh python:3.12-slim sandbox (task B1).
# Run from /work, where SandboxManager.base() has already uploaded forklib/ and this file.
# Versions match requirements-dev.lock so sandbox results equal local results.
set -eu
python -m pip install --quiet --no-cache-dir \
  "numpy==2.5.4" "pytest==9.1.1" "pytest-json-report==1.5.0"
mkdir -p /work/out
python - <<'PY'
import numpy, pytest, forklib
print("base ok", numpy.__version__, pytest.__version__)
PY
