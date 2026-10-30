import os

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
EVAL_MODEL = os.getenv("OLLAMA_EVAL_MODEL", OLLAMA_MODEL)