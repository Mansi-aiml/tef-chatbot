import logging
import sys
import threading
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger("app.services.llm")

_client = OpenAI(api_key=settings.openai_api_key)


def estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    return (
        prompt_tokens * settings.llm_input_cost_per_1m
        + completion_tokens * settings.llm_output_cost_per_1m
    ) / 1_000_000


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    calls: int = 0
    # per-caller breakdown, e.g. {"synthesis": {"prompt_tokens": .., ...}}
    by_step: dict[str, dict[str, int]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def add(self, step: str, prompt: int, completion: int) -> None:
        with self._lock:
            self.prompt_tokens += prompt
            self.completion_tokens += completion
            self.total_tokens += prompt + completion
            self.calls += 1
            s = self.by_step.setdefault(step, {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "calls": 0})
            s["prompt_tokens"] += prompt
            s["completion_tokens"] += completion
            s["total_tokens"] += prompt + completion
            s["calls"] += 1

    @property
    def cost_usd(self) -> float:
        return estimate_cost(self.prompt_tokens, self.completion_tokens)

    def to_dict(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "calls": self.calls,
            "cost_usd": round(self.cost_usd, 6),
            "by_step": self.by_step,
        }


_current_usage: ContextVar[TokenUsage | None] = ContextVar("current_usage", default=None)


@contextmanager
def track_usage():
    """Collect token usage of every chat_completion call made inside this block."""
    usage = TokenUsage()
    token = _current_usage.set(usage)
    try:
        yield usage
    finally:
        _current_usage.reset(token)


def chat_completion(
    system_prompt: str,
    user_prompt: str,
    temperature: float | None = None,
) -> str:
    kwargs = {} if temperature is None else {"temperature": temperature}

    response = _client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        **kwargs,
    )

    if response.usage is not None:
        step = sys._getframe(1).f_globals.get("__name__", "unknown").rsplit(".", 1)[-1]
        prompt, completion = response.usage.prompt_tokens, response.usage.completion_tokens
        logger.info(
            "LLM call [%s] model=%s | prompt=%d completion=%d total=%d tokens | cost=$%.6f",
            step, settings.openai_model, prompt, completion, prompt + completion, estimate_cost(prompt, completion),
        )
        usage = _current_usage.get()
        if usage is not None:
            usage.add(step, prompt, completion)

    return response.choices[0].message.content or ""


# # from groq import Groq
# from openai import OpenAI

# from app.core.config import settings

# _client = OpenAI(api_key=settings.openai_api_key)
# # _client = Groq(api_key=settings.groq_api_key)



# def chat_completion(system_prompt: str, user_prompt: str, temperature: float | None = None) -> str:
#     kwargs = {} if temperature is None else {"temperature": temperature}
#     response = _client.chat.completions.create(
#         model=settings.groq_model,
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_prompt},
#         ],
#         **kwargs,
#     )
#     return response.choices[0].message.content or ""
