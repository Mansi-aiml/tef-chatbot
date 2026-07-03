from app.services.llm import chat_completion

_SYSTEM_PROMPT = (
    "Rate how confident you are that the given answer correctly and fully "
    "resolves the given question, on a scale from 0.0 (not confident) to "
    "1.0 (fully confident). Respond with only the number."
)


def score_confidence(query: str, answer: str) -> float:
    user_prompt = f"Question: {query}\n\nAnswer: {answer}"
    raw = chat_completion(_SYSTEM_PROMPT, user_prompt).strip()
    try:
        return max(0.0, min(1.0, float(raw)))
    except ValueError:
        return 0.0
