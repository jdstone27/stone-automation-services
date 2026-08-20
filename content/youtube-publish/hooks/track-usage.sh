#!/bin/bash
echo "{\"ts\":\"$(date -u +%FT%TZ)\",\"input\":$(cat)}" >> "${CLAUDE_PLUGIN_ROOT}/usage-log.jsonl"
