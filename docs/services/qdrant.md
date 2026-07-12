# Qdrant

Files:
- `services/qdrant/compose.yaml`

Run notes:
- Qdrant API is exposed on port `6333`.
- The container persists storage under `./storage` in the compose directory.
- Restart the stack after image or storage changes.
- This is the vector store used by local apps such as Open WebUI.
