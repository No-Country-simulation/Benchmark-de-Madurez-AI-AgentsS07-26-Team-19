# Microservicio de IA — Ollama con modelo NeuralQwen-2.5-1.5B-Spanish
# Expone la API nativa de Ollama en el puerto 11434. El modelo se descarga
# una sola vez al primer arranque (GGUF Q4_K_M ~1.12 GB) y queda cacheado
# en el volumen del contenedor.
FROM ollama/ollama:0.5.7

ENV OLLAMA_HOST=0.0.0.0:11434 \
    OLLAMA_KEEP_ALIVE=5m

WORKDIR /app
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 11434

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD ollama list >/dev/null 2>&1 || exit 1

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]