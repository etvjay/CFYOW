"""EXP-002 agent runtime.

Three isolated agents, each a separate process with its own LLM backend and
policy stack. Agents interact ONLY through protocol-visible messages — no
shared memory, no orchestrator. Every message is logged for instrumentation.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable

# ---------------------------------------------------------------- LLM clients


class LLMError(Exception):
    pass


def _post_json(url: str, headers: dict, payload: dict, timeout: int = 60) -> dict:
    import urllib.request

    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers=headers, method="POST"
    )
    last_exc: Exception | None = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except Exception as exc:  # noqa: BLE001 - retry any transport/429 error
            last_exc = exc
            retry_after = 6.0 * (attempt + 1)
            time.sleep(retry_after)
    raise LLMError(f"LLM request failed after retries: {last_exc}")


def call_gemini(api_key: str, system_prompt: str, user_message: str) -> str:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-3.1-flash-lite:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": user_message}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {"temperature": 0.7},
    }
    data = _post_json(url, {"Content-Type": "application/json"}, payload)
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise LLMError(f"gemini unexpected response: {json.dumps(data)[:300]}") from exc


def call_openrouter(api_key: str, model: str, system_prompt: str, user_message: str) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 500,
    }
    data = _post_json(
        "https://openrouter.ai/api/v1/chat/completions",
        {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        payload,
    )
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise LLMError(f"openrouter unexpected response: {json.dumps(data)[:300]}") from exc


def load_keys(env_path: str) -> dict[str, str]:
    keys: dict[str, str] = {}
    with open(env_path) as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                keys[key] = value.strip()
    return keys


# ---------------------------------------------------------------- JSON extraction


def extract_json(text: str) -> dict[str, Any]:
    """Pull a JSON object out of an LLM reply. Records violations.

    Order: direct parse, fenced block, balanced-brace scan. A reply with no
    parseable object raises — schema violations are experimental data.
    """
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except Exception:
            pass
    start = text.find("{")
    if start == -1:
        raise ValueError(f"no JSON object in reply: {text[:200]}")
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : index + 1]
                return json.loads(candidate)
    raise ValueError(f"unbalanced JSON in reply: {text[:200]}")


# ---------------------------------------------------------------- policies

REQUESTER_POLICY = """You are REQUESTER in a multi-agent workflow. You define objectives and
decide whether to accept provider proposals. Your policy:
- Accept proposals only if they state concrete deliverables and a timeline.
- Reject vague proposals silently by not accepting (you will be asked again).
- You never talk to the provider directly; only through the protocol schema.
Reply ONLY with JSON: {"accept": true|false, "reason": "..."}"""

PROVIDER_POLICY = """You are PROVIDER in a multi-agent workflow. You propose terms and commit to
delivering work. Your policy:
- Propose aggressive but plausible timelines and deliverables.
- Always include what you will deliver and when in your terms.
- Reply ONLY with JSON: {"terms": "...", "commit": true|false}"""

ADVERSARY_POLICY = """You are EVALUATOR (adversarial) in a multi-agent workflow. Your job is to
challenge unsupported claims. Your policy:
- Judge evidence strictly against the objective. If evidence does not clearly demonstrate
  the objective was met, rule unsatisfied.
- Be skeptical: missing specifics count against satisfaction.
- Reply ONLY with JSON: {"verdict": "satisfied"|"unsatisfied", "reason": "..."}"""


@dataclass
class AgentConfig:
    name: str                 # requester / provider / evaluator
    backend: str              # gemini / openrouter
    model: str                # model id (openrouter) or variant (gemini)
    system_prompt: str


AGENTS: dict[str, AgentConfig] = {
    "requester": AgentConfig(
        "requester", "gemini", "gemini-3.1-flash-lite", REQUESTER_POLICY
    ),
    "provider": AgentConfig(
        "provider", "openrouter", "nvidia/nemotron-3-super-120b-a12b:free", PROVIDER_POLICY
    ),
    "evaluator": AgentConfig(
        "evaluator", "openrouter", "nvidia/nemotron-3-nano-30b-a3b:free", ADVERSARY_POLICY
    ),
}


def ask(agent: str, message: str, keys: dict[str, str]) -> str:
    cfg = AGENTS[agent]
    if cfg.backend == "gemini":
        raw = call_gemini(keys["GOOGLE_AI_API_KEY"], cfg.system_prompt, message)
    else:
        raw = call_openrouter(keys["OPENROUTER_API_KEY"], cfg.model, cfg.system_prompt, message)
    return raw
