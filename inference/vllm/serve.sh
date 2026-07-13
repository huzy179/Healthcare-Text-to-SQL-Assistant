#!/usr/bin/env bash
set -euo pipefail

MODEL_PATH="${MODEL_PATH:-./finetune/outputs/merged_model}"
PORT="${PORT:-8000}"

python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL_PATH" \
  --served-model-name "${VLLM_MODEL:-healthcare-text-to-sql-model}" \
  --host 0.0.0.0 \
  --port "$PORT"
