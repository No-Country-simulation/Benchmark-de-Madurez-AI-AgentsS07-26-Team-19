#!/bin/sh
# Arranca Ollama y descarga el modelo la primera vez (cacheado tras ello).
set -e

MODEL="${AI_MODEL:-hf.co/mradermacher/NeuralQwen-2.5-1.5B-Spanish-GGUF:Q4_K_M}"

# Servidor en segundo plano mientras se asegura el modelo.
ollama serve &
SERVER_PID=$!

# Esperar a que el socket esté listo.
for i in $(seq 1 60); do
    if ollama list >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

# Descargar el modelo (idempotente; si ya está en el volumen, no descarga nada).
echo "AI model: pulling $MODEL"
ollama pull "$MODEL"
echo "AI model: ready"

# Ejecutar en primer plano para que el contenedor viva hasta señal.
wait "$SERVER_PID"