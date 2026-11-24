#!/usr/bin/env bash
# Quick smoke test (critical path only) on the latest build (v1.2).
cd "$(dirname "$0")"
FIX_BUGS=2 exec venv/bin/python -m pytest -m smoke "$@"
