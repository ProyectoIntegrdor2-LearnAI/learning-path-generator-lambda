import json
import logging
import os
import random
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)


class BedrockClient:
    def __init__(self) -> None:
        self._embedding_model = os.getenv("EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0")
        self._nova_model = os.getenv("NOVA_MODEL", "amazon.nova-lite-v1:0")
        self._nova_temperature = float(os.getenv("NOVA_TEMPERATURE", "0.7"))
        config = Config(
            region_name="us-east-2",
            retries={"max_attempts": 3, "mode": "standard"},
            read_timeout=25,
            connect_timeout=5,
            max_pool_connections=10,
        )
        self._client = boto3.client("bedrock-runtime", region_name="us-east-2", config=config)

    def generate_embedding(self, text: str) -> List[float]:
        return self._cached_embedding(text)

    @lru_cache(maxsize=1000)
    def _cached_embedding(self, text: str) -> List[float]:
        return self._invoke_with_retry(self._invoke_embedding, text)

    def invoke_nova(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> Dict[str, Any]:
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": user_prompt}],
                },
            ],
            "inferenceConfig": {
                "temperature": self._nova_temperature,
                "maxTokens": max_tokens,
                "topP": 0.9,
            },
        }
        return self._invoke_with_retry(self._invoke_nova, payload)

    def _invoke_with_retry(self, func, *args):
        attempts = 0
        backoff = 1.0
        last_error: Optional[Exception] = None
        while attempts < 4:
            try:
                return func(*args)
            except (ClientError, BotoCoreError) as exc:
                last_error = exc
                attempts += 1
                if attempts >= 4:
                    break
                sleep_for = backoff * (2 ** (attempts - 1)) * random.uniform(0.75, 1.25)
                logger.warning(
                    json.dumps(
                        {
                            "event": "bedrock_retry",
                            "attempt": attempts,
                            "sleep_for": sleep_for,
                            "error": str(exc),
                        }
                    )
                )
                time.sleep(sleep_for)
        assert last_error is not None
        raise last_error

    def _invoke_embedding(self, text: str) -> List[float]:
        request_body = json.dumps({"inputText": text})
        response = self._client.invoke_model(
            modelId=self._embedding_model,
            contentType="application/json",
            accept="application/json",
            body=request_body,
        )
        payload = json.loads(response["body"].read())
        embedding = payload.get("embedding")
        if not embedding:
            raise ValueError("Bedrock embedding response missing 'embedding' field")
        if len(embedding) != int(os.getenv("EMBEDDING_DIM", "1024")):
            raise ValueError("Unexpected embedding dimension returned by Bedrock")
        return embedding

    def _invoke_nova(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self._client.invoke_model(
            modelId=self._nova_model,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload),
        )
        content = json.loads(response["body"].read())
        if "output" in content:
            # Some responses wrap output differently; prefer unified structure
            return content["output"]
        return content


_bedrock_client: BedrockClient | None = None


def get_bedrock_client() -> BedrockClient:
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient()
    return _bedrock_client
