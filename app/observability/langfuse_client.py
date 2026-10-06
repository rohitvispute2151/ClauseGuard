import logging
import os
from contextlib import asynccontextmanager
from typing import Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class LangfuseTracker:
    """Safe wrapper for Langfuse tracing with graceful no-op fallback."""

    def __init__(self):
        self.enabled = bool(settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY)
        self.client = None

        if self.enabled:
            # Set environment variables for Langfuse SDK integrations
            os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
            os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
            os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST
            try:
                from langfuse import Langfuse

                self.client = Langfuse(
                    public_key=settings.LANGFUSE_PUBLIC_KEY,
                    secret_key=settings.LANGFUSE_SECRET_KEY,
                    host=settings.LANGFUSE_HOST,
                )
                logger.info(f"Langfuse tracing enabled at {settings.LANGFUSE_HOST}")
            except Exception as exc:
                logger.warning(
                    f"Failed to initialize Langfuse client: {exc}. Tracing running in no-op mode."
                )
                self.enabled = False
        else:
            logger.info("Langfuse credentials not set. Tracing running in no-op mode.")

    @asynccontextmanager
    async def trace_span(
        self,
        name: str,
        input: Any = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Asynchronous context manager for tracing spans."""
        if not self.enabled or not self.client:
            yield {"name": name, "metadata": metadata or {}}
            return

        try:
            with self.client.start_as_current_observation(
                as_type="span",
                name=name,
                input=input,
                metadata=metadata,
            ) as span:
                yield span
        except Exception as exc:
            logger.debug(f"Langfuse span error ({name}): {exc}")
            yield None

    @asynccontextmanager
    async def trace_generation(
        self,
        name: str,
        model: str | None = None,
        input: Any = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Asynchronous context manager for tracing LLM generations."""
        if not self.enabled or not self.client:
            yield {"name": name, "metadata": metadata or {}}
            return

        try:
            with self.client.start_as_current_observation(
                as_type="generation",
                name=name,
                model=model,
                input=input,
                metadata=metadata,
            ) as gen:
                yield gen
        except Exception as exc:
            logger.debug(f"Langfuse generation error ({name}): {exc}")
            yield None

    def flush(self) -> None:
        """Flushes buffered traces to Langfuse."""
        if self.enabled and self.client:
            try:
                self.client.flush()
            except Exception as exc:
                logger.debug(f"Failed to flush Langfuse events: {exc}")

    def get_trace_url(self) -> str | None:
        """Returns the URL of the active trace in the Langfuse UI if available."""
        if self.enabled and self.client:
            try:
                return self.client.get_trace_url()
            except Exception:
                return None
        return None
