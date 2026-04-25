from functools import lru_cache
from textwrap import dedent

from fastapi import HTTPException
from google import genai

from config import get_settings


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


def should_use_demo_fallback(message: str) -> bool:
    settings = get_settings()
    mode = settings.ai_fallback_mode

    if mode == "off":
        return False
    if mode == "demo":
        return True

    lowered = message.lower()
    return any(
        token in lowered
        for token in (
            "resource_exhausted",
            "quota",
            "429",
            "not_found",
            "model",
            "api key",
            "timed out",
            "timeout",
            "service unavailable",
        )
    )


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
    except RuntimeError as exc:
        message = str(exc)
        lowered = message.lower()
        if should_use_demo_fallback(message):
            if any(token in lowered for token in ("resource_exhausted", "quota", "429")):
                reason = "quota exhaustion"
            elif "missing gemini_api_key" in lowered or "api key" in lowered:
                reason = "configuration issue"
            else:
                reason = "provider issue"
            return build_demo_response(action_key, code, language, reason)
        raise HTTPException(status_code=500, detail=message) from exc
    except Exception as exc:
        message = str(exc)
        lowered = message.lower()

        if should_use_demo_fallback(message):
            reason = "quota exhaustion" if any(
                token in lowered for token in ("resource_exhausted", "quota", "429")
            ) else "provider issue"
            return build_demo_response(action_key, code, language, reason)

        raise HTTPException(
            status_code=502,
            detail="The AI service could not process this request right now.",
        ) from exc

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
