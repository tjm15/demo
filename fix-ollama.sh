#!/bin/bash
# Fix stuck Ollama process

echo "=== Ollama Status ==="
ps aux | grep ollama | grep -v grep

echo ""
echo "=== Killing stuck Ollama processes ==="
pkill -9 ollama
sleep 2

echo ""
echo "=== Starting fresh Ollama ==="
ollama serve > /tmp/ollama.log 2>&1 &
sleep 3

echo ""
echo "=== Testing Ollama ==="
curl -s http://127.0.0.1:11434/api/tags | jq '.models[].name' 2>/dev/null || echo "Ollama not responding yet"

echo ""
echo "=== Available models ==="
ollama list

echo ""
echo "Ollama logs available at: /tmp/ollama.log"
echo ""
echo "To test with a smaller/faster model:"
echo "  export LLM_MODEL=gemma3:27b"
echo "  # or"
echo "  ollama pull llama3.2:3b"
echo "  export LLM_MODEL=llama3.2:3b"
echo ""
echo "To bypass LLM entirely for testing:"
echo "  export DISABLE_LLM=true"
echo "  # Then restart kernel"
