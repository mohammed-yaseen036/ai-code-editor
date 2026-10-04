from dataclasses import dataclass
from functools import lru_cache
from logging import getLogger
from textwrap import dedent

import httpx
from fastapi import HTTPException
from google import genai
from google.genai import errors

from config import MissingAIKeyError, get_settings

logger = getLogger(__name__)

TRANSIENT_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})
TRANSIENT_STATUS_NAMES = frozenset(
    {
        "RESOURCE_EXHAUSTED",
        "INTERNAL",
        "UNAVAILABLE",
        "DEADLINE_EXCEEDED",
    }
)

GENERIC_CLIENT_MESSAGE = "The AI service could not process this request right now."
CREDENTIALS_CLIENT_MESSAGE = (
    "The AI service rejected the configured credentials. Check GEMINI_API_KEY."
)


@dataclass(frozen=True)
class FallbackDecision:
    use_fallback: bool
    reason: str = ""


@lru_cache
def get_ai_client() -> genai.Client:
    settings = get_settings()
    settings.require_gemini()
    return genai.Client(api_key=settings.gemini_api_key)


def build_prompt(action: str, code: str, language: str) -> str:
    return dedent(
        f"""
        You are an expert software engineer helping inside an AI code editor.

        Task:
        {action}

        Language:
        {language}

        Instructions:
        - Keep the response concise and practical.
        - Preserve the user's intent.
        - Use Markdown code fences when returning code.
        - If there is a bug or risk, explain the root cause briefly.

        User code:
        ```{language}
        {code}
        ```
        """
    ).strip()


def is_transient_ai_error(exc: BaseException) -> bool:
    """Report whether an AI failure is worth retrying later.

    Only capacity, server-side, and network faults qualify. Client-side problems
    such as a bad API key (401/403), an unknown model (404), or a malformed
    request (400) are configuration or input bugs and must surface as errors
    instead of being masked by the demo fallback.
    """
    if isinstance(exc, (TimeoutError, httpx.TimeoutException, httpx.NetworkError)):
        return True

    if isinstance(exc, errors.APIError):
        if exc.code in TRANSIENT_STATUS_CODES:
            return True
        return (exc.status or "").upper() in TRANSIENT_STATUS_NAMES

    return False


def classify_ai_error(exc: BaseException) -> FallbackDecision:
    settings = get_settings()
    mode = settings.ai_fallback_mode

    if mode == "off":
        return FallbackDecision(False)

    if mode == "demo":
        return FallbackDecision(True, "demo mode is forced on")

    if isinstance(exc, MissingAIKeyError):
        return FallbackDecision(True, "GEMINI_API_KEY is not configured")

    if not is_transient_ai_error(exc):
        return FallbackDecision(False)

    if isinstance(exc, errors.APIError):
        if exc.code == 429 or (exc.status or "").upper() == "RESOURCE_EXHAUSTED":
            return FallbackDecision(True, "quota exhaustion")
        return FallbackDecision(True, "temporary provider outage")

    return FallbackDecision(True, "network timeout")


def client_message_for(exc: BaseException) -> str:
    """Log the provider failure in full and return a message safe to expose.

    Raw provider errors can contain key fragments and internal detail, so they
    stay in the server log instead of travelling back to the browser.
    """
    logger.error("Gemini request failed: %s: %s", type(exc).__name__, exc)

    if isinstance(exc, errors.APIError):
        if exc.code in (401, 403):
            return CREDENTIALS_CLIENT_MESSAGE
        if exc.code == 404:
            return (
                f"The configured AI model '{get_settings().gemini_model}' is not "
                "available for this API key."
            )

    return GENERIC_CLIENT_MESSAGE


def comment_for_language(language: str) -> str:
    if language.lower() == "python":
        return "#"
    return "//"


def complete_code_locally(code: str, language: str) -> str:
    source = code.rstrip()
    comment = comment_for_language(language)

    if language.lower() == "python" and source.endswith(":"):
        return f"{source}\n    pass"

    if language.lower() in {"javascript", "typescript"} and source.endswith("{"):
        return f"{source}\n  {comment} Continue implementation here.\n}}"

    return f"{source}\n\n{comment} Continue implementation here."


def fix_code_locally(code: str, language: str) -> tuple[str, list[str]]:
    source = code.rstrip()
    notes = []
    fixed = source

    if language.lower() == "python":
        lines = source.splitlines()
        adjusted = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("def ", "if ", "for ", "while ", "class ", "elif ", "else")):
                if stripped and not stripped.endswith(":"):
                    adjusted.append(f"{line}:")
                    notes.append("Added a missing colon to a Python control or definition line.")
                    continue
            adjusted.append(line)

        fixed = "\n".join(adjusted)

        if "print " in fixed and "print(" not in fixed:
            fixed = fixed.replace("print ", "print(") + ")"
            notes.append("Converted legacy print syntax to function-call syntax.")

    if not notes:
        notes.append("Reviewed the snippet and returned a cleaned version for another test run.")

    return fixed, notes


def explain_code_locally(code: str, language: str) -> str:
    lines = [line for line in code.splitlines() if line.strip()]
    preview = lines[0].strip() if lines else "the provided snippet"
    sections = [
        "Demo fallback mode is active because the Gemini API is unavailable right now.",
        "\n".join(
            [
                f"Language: {language}",
                "Summary:",
                f"- This snippet starts with: `{preview}`",
                f"- It contains {len(lines)} non-empty line(s).",
                "- It appears to define logic that can be edited, tested, and sent back through the assistant once live AI quota is available.",
            ]
        ),
        "\n".join(
            [
                "Practical reading:",
                "- Inputs are accepted through the variables or function parameters in the snippet.",
                "- The code then performs its main logic step by step.",
                "- The final expression or return value produces the output.",
            ]
        ),
    ]
    return "\n\n".join(sections)


def build_demo_response(action_key: str, code: str, language: str, reason: str) -> str:
    header = (
        "Demo fallback mode is active because the live Gemini service is unavailable "
        f"right now ({reason})."
    )

    if action_key == "complete":
        completed = complete_code_locally(code, language)
        return "\n\n".join(
            [
                header,
                "Suggested completion:",
                f"```{language}\n{completed}\n```",
            ]
        )

    if action_key == "fix":
        fixed_code, notes = fix_code_locally(code, language)
        note_lines = "\n".join(f"- {note}" for note in notes)
        return "\n\n".join(
            [
                header,
                "Suggested fix:",
                note_lines,
                f"```{language}\n{fixed_code}\n```",
            ]
        )

    return explain_code_locally(code, language)


def generate_ai_response(action_key: str, action: str, code: str, language: str) -> str:
    if not code.strip():
        raise HTTPException(status_code=400, detail="Please provide some code first.")

    settings = get_settings()

    try:
        response = get_ai_client().models.generate_content(
            model=settings.gemini_model,
            contents=build_prompt(action, code, language),
        )
    except MissingAIKeyError as exc:
        decision = classify_ai_error(exc)
        if decision.use_fallback:
            return build_demo_response(action_key, code, language, decision.reason)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        decision = classify_ai_error(exc)
        if decision.use_fallback:
            return build_demo_response(action_key, code, language, decision.reason)
        raise HTTPException(status_code=502, detail=client_message_for(exc)) from exc

    text = (response.text or "").strip()
    if not text:
        raise HTTPException(
            status_code=502,
            detail="The AI service returned an empty response.",
        )

    return text


def get_code_completion(code: str, language: str) -> str:
    return generate_ai_response(
        "complete",
        "Complete the code and continue from the current intent.",
        code,
        language,
    )


def get_bug_fix(code: str, language: str) -> str:
    return generate_ai_response(
        "fix",
        "Fix the bug, explain the issue, and show the corrected code.",
        code,
        language,
    )


def get_code_explanation(code: str, language: str) -> str:
    return generate_ai_response(
        "explain",
        "Explain what the code does in simple terms.",
        code,
        language,
    )
