"""LLM client wrapper for Google Gemini."""

import asyncio
import random
from collections.abc import AsyncIterator

from google import genai
from google.genai import types

from ..observability.logging import get_logger
from ..utils.config import get_settings
from ..utils.exceptions import GenerationError

logger = get_logger(__name__)

try:
    from langsmith import get_current_run_tree, traceable
except ImportError:
    def traceable(*args, **kwargs):
        return lambda f: f
    def get_current_run_tree():
        return None


class LLMClient:
    """Async wrapper for Google Gemini LLM API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        provider: str | None = None,
    ):
        """
        Initialize LLM client.

        Args:
            api_key: API key (defaults to settings)
            model: Model name (defaults to settings)
            temperature: Sampling temperature (defaults to settings)
            max_tokens: Max tokens to generate (defaults to settings)
            provider: LLM provider (defaults to "gemini")
        """
        settings = get_settings()
        self.provider = "gemini"
        self.model = model or settings.llm_model
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self.max_tokens = max_tokens or settings.llm_max_tokens

        self._client = None
        self.api_key = (
            api_key
            or settings.gemini_api_key
            or settings.google_api_key
        )
        if self.api_key:
            try:
                self._client = genai.Client(
                    api_key=self.api_key,
                    http_options={"api_version": "v1beta"},
                )
                logger.info(f"Initialized Gemini LLM client with model: {self.model}")
            except Exception as e:
                logger.warning(f"Could not pre-initialize Gemini client: {e}")

    @property
    def client(self):
        """Get or lazily initialize Gemini API client."""
        if self._client is None:
            api_key = self.api_key or get_settings().gemini_api_key or get_settings().google_api_key
            if not api_key:
                raise GenerationError(
                    "No Gemini API key found. Please set GEMINI_API_KEY in your .env file or environment."
                )
            self.api_key = api_key
            self._client = genai.Client(
                api_key=self.api_key,
                http_options={"api_version": "v1beta"},
            )
        return self._client

    @traceable(name="gemini_generate", run_type="llm")
    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop_sequences: list[str] | None = None,
        **kwargs,
    ) -> str:
        """
        Generate text completion.

        Args:
            prompt: User prompt
            system: System prompt (optional)
            temperature: Override default temperature
            max_tokens: Override default max tokens
            stop_sequences: Stop sequences
            **kwargs: Additional API parameters

        Returns:
            Generated text

        Raises:
            GenerationError: If generation fails
        """
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens or self.max_tokens
        max_retries = 3
        backoff_base = 1.0

        for attempt in range(1, max_retries + 1):
            model_to_use = self.model

            try:
                logger.debug(f"Generating completion with model {model_to_use} via {self.provider} (attempt {attempt}/{max_retries})")

                config = types.GenerateContentConfig(
                    temperature=temp,
                    max_output_tokens=tokens,
                    system_instruction=system if system else None,
                    stop_sequences=stop_sequences or None,
                )
                response = await self.client.aio.models.generate_content(
                    model=model_to_use,
                    contents=prompt,
                    config=config,
                )
                generated_text = response.text or ""
                logger.debug(f"Generated {len(generated_text)} characters")

                # Attach token counts & model name to LangSmith trace
                run = get_current_run_tree()
                if run and hasattr(response, "usage_metadata") and response.usage_metadata:
                    um = response.usage_metadata
                    in_toks = getattr(um, "prompt_token_count", 0) or 0
                    out_toks = getattr(um, "candidates_token_count", 0) or 0
                    tot_toks = getattr(um, "total_token_count", 0) or 0
                    usage_dict = {
                        "input_tokens": in_toks,
                        "output_tokens": out_toks,
                        "total_tokens": tot_toks,
                    }
                    run.metadata["ls_model_name"] = model_to_use
                    run.metadata["ls_provider"] = "google_genai"
                    run.metadata["model"] = model_to_use
                    run.metadata["model_name"] = model_to_use
                    run.metadata["usage_metadata"] = usage_dict
                    run.extra["usage_metadata"] = usage_dict

                return generated_text

            except Exception as e:
                err_msg = str(e).lower()
                is_transient = any(
                    sig in err_msg
                    for sig in ["503", "unavailable", "429", "resource_exhausted", "rate limit", "timeout", "high demand"]
                )

                if is_transient and attempt < max_retries:
                    # Check if Google provided a retry delay
                    import re
                    delay_match = re.search(r"retry(?: in|delay'?:\s*'?)(\d+)", err_msg)
                    if delay_match:
                        sleep_time = min(float(delay_match.group(1)) + 1.0, 30.0)
                    else:
                        sleep_time = backoff_base * (2 ** (attempt - 1)) + random.uniform(0.5, 1.5)

                    logger.warning(
                        f"Transient LLM error ({e}). Retrying attempt {attempt + 1}/{max_retries} in {sleep_time:.2f}s..."
                    )
                    await asyncio.sleep(sleep_time)
                    continue

                logger.error(f"Generation failed after {attempt} attempts: {e}")
                raise GenerationError(
                    "LLM generation failed",
                    details={"model": self.model, "provider": self.provider, "error": str(e), "attempts": attempt},
                    original_error=e,
                )

    async def generate_with_context(
        self,
        query: str,
        context: list[str],
        system: str | None = None,
        **kwargs,
    ) -> str:
        """
        Generate response with retrieved context.

        Args:
            query: User query
            context: Retrieved context chunks
            system: System prompt
            **kwargs: Additional generation parameters

        Returns:
            Generated response
        """
        context_text = "\n\n".join(
            [f"Context {i+1}:\n{chunk}" for i, chunk in enumerate(context)]
        )

        prompt = f"""Based on the following context, please answer the question.

{context_text}

Question: {query}

Answer:"""

        return await self.generate(prompt=prompt, system=system, **kwargs)

    async def stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        Stream text completion.

        Args:
            prompt: User prompt
            system: System prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Additional API parameters

        Yields:
            Text chunks

        Raises:
            GenerationError: If streaming fails
        """
        try:
            logger.debug(f"Streaming completion with model {self.model} via {self.provider}")
            temp = temperature if temperature is not None else self.temperature
            tokens = max_tokens or self.max_tokens

            config = types.GenerateContentConfig(
                temperature=temp,
                max_output_tokens=tokens,
                system_instruction=system if system else None,
            )
            response_stream = await self.client.aio.models.generate_content_stream(
                model=self.model,
                contents=prompt,
                config=config,
            )
            async for chunk in response_stream:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            raise GenerationError(
                "LLM streaming failed",
                details={"model": self.model, "provider": self.provider, "error": str(e)},
                original_error=e,
            )

    async def chat(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        **kwargs,
    ) -> str:
        """
        Multi-turn chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: System prompt
            **kwargs: Additional generation parameters

        Returns:
            Generated response
        """
        try:
            logger.debug(f"Chat completion with {len(messages)} messages via {self.provider}")

            contents = []
            for m in messages:
                role = "user" if m.get("role") in ["user", "human"] else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=m.get("content", ""))]
                    )
                )
            config = types.GenerateContentConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                system_instruction=system if system else None,
            )
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
            return response.text or ""

        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise GenerationError(
                "Chat completion failed",
                details={"model": self.model, "provider": self.provider, "error": str(e)},
                original_error=e,
            )


# Global LLM client instance
_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get global LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
