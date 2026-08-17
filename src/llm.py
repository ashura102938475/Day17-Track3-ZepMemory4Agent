"""Thin LLM wrapper for the demo UI chat reply (NVIDIA NIM or Gemini).

This is the ONLY place the lab calls a generative LLM. Benchmark scoring never
uses an LLM (see LAB.md): retrieval evidence is graded deterministically. Here
the chat model only turns retrieved memory context into a grounded assistant
reply so the mini-product feels real.

Providers (first configured wins):
  1. NVIDIA NIM (OpenAI-compatible) — NVIDIA_API_KEY, defaults to
     nvidia/nemotron-3.5-lightning-30b-a3b at integrate.api.nvidia.com.
  2. Gemini — GEMINI_API_KEY / GOOGLE_API_KEY, model via GEMINI_MODEL.
"""

from __future__ import annotations

from typing import Any

from .config import settings

SYSTEM_INSTRUCTION = (
    "You are the assistant of a personal memory agent for VinUni Lab 17. "
    "Answer the user grounded ONLY in the retrieved memory context provided. "
    "If the context does not contain the answer, say so plainly instead of "
    "inventing facts. Be concise and cite the concrete markers/ids you used. "
    "You may reply in the user's language (Vietnamese or English)."
)


def nvidia_available() -> bool:
    """True when an NVIDIA key is configured. UI uses this to show status."""
    return bool(settings.nvidia_api_key)


def gemini_available() -> bool:
    """True when a key is configured. UI uses this to show status."""
    return bool(settings.gemini_api_key)


def _grounding_text(memory_context: str, user_message: str) -> str:
    return (
        "Retrieved memory context for this turn:\n"
        "-------------------------------------\n"
        f"{memory_context.strip() or '(no memory retrieved)'}\n"
        "-------------------------------------\n\n"
        f"User message: {user_message}"
    )


def _generate_nvidia(
    memory_context: str,
    history: list[dict[str, str]],
    user_message: str,
    *,
    model: str | None = None,
) -> str:
    """Generate a grounded assistant reply through the NVIDIA NIM endpoint."""
    # Lazy import so the rest of the package works without openai installed
    # (tests, report generation, retrieval benchmarks never need it).
    from openai import OpenAI

    client = OpenAI(
        base_url=settings.nvidia_base_url,
        api_key=settings.nvidia_api_key,
    )
    model_name = model or settings.nvidia_model

    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        *history,
        {"role": "user", "content": _grounding_text(memory_context, user_message)},
    ]

    completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.3,
        top_p=0.95,
        max_tokens=4096,
        extra_body={
            "chat_template_kwargs": {"enable_thinking": True},
            "reasoning_budget": 2048,
        },
    )
    return (completion.choices[0].message.content or "").strip()


def _to_contents(history: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Map chat history to google-genai `contents` turns.

    Roles: user -> "user", everything else (assistant/model) -> "model".
    """
    contents: list[dict[str, Any]] = []
    for msg in history:
        role = "user" if msg.get("role") == "user" else "model"
        text = msg.get("content", "")
        if not text:
            continue
        contents.append({"role": role, "parts": [{"text": text}]})
    return contents


def _generate_gemini(
    memory_context: str,
    history: list[dict[str, str]],
    user_message: str,
    *,
    model: str | None = None,
) -> str:
    """Generate a grounded assistant reply with Gemini."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)
    model_name = model or settings.gemini_model

    contents = _to_contents(history)
    contents.append(
        {"role": "user", "parts": [{"text": _grounding_text(memory_context, user_message)}]}
    )

    response = client.models.generate_content(
        model=model_name,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.3,
            max_output_tokens=800,
        ),
    )
    return (getattr(response, "text", "") or "").strip()


def generate_reply(
    memory_context: str,
    history: list[dict[str, str]],
    user_message: str,
    *,
    model: str | None = None,
) -> str:
    """Generate a grounded assistant reply (NVIDIA preferred, Gemini fallback).

    Raises RuntimeError if no provider key is configured, and lets SDK/network
    errors bubble up so the UI can surface them. `history` should include the
    latest user turn or not — `user_message` is appended as the final user turn
    regardless.
    """
    if settings.nvidia_api_key:
        return _generate_nvidia(memory_context, history, user_message, model=model)
    if settings.gemini_api_key:
        return _generate_gemini(memory_context, history, user_message, model=model)
    raise RuntimeError(
        "No LLM key configured. Set NVIDIA_API_KEY (or GEMINI_API_KEY) in "
        ".env to enable chat replies."
    )
