import time

import ollama
from pydantic import BaseModel, ValidationError

from .config import NUM_CTX, OLLAMA_HOST, OLLAMA_MODEL

_client = ollama.Client(host=OLLAMA_HOST, timeout=150)


def generate(schema: type[BaseModel], system: str, user: str, retries: int = 1,
             model: str | None = None, max_tokens: int = 800):
    model = model or OLLAMA_MODEL
    last = None
    for attempt in range(retries + 1):
        t0 = time.time()
        try:
            resp = _client.chat(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                format=schema.model_json_schema(),
                keep_alive="30m",          # keep the model in memory between calls
                options={"temperature": 0, "num_ctx": NUM_CTX, "num_predict": max_tokens},
            )
        except Exception as e:
            last = e
            print(f"[llm] {schema.__name__} attempt {attempt + 1} failed after {time.time() - t0:.0f}s: {e!r}")
            continue
        print(f"[llm] {schema.__name__} ({model}) {time.time() - t0:.1f}s, "
              f"{getattr(resp, 'eval_count', '?')} output tokens")
        try:
            return schema.model_validate_json(resp.message.content)
        except ValidationError as e:
            last = e
            user += "\n\nYour last output was invalid or cut off. Return short, valid JSON only."
    raise RuntimeError(f"LLM failed to produce valid {schema.__name__}: {last}")