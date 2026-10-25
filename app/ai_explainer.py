
import ollama


def explain_impact(impact_data: dict) -> str:
    """Use Qwen3 to explain ChangeGuard's impact analysis."""

    prompt = f"""
    You are the AI explanation assistant for ChangeGuard.

    Explain this Python code-change impact analysis
    in simple language for a beginner developer.

    Explain:
    1. Which files are affected and why.
    2. Which tests should be run.
    3. What risks the developer should check.

    Only use the information provided.
    Do not invent dependencies or claim that tests passed.

    Impact analysis:
    {impact_data}
    """

    response = ollama.chat(
        model="qwen3:8b",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return response["message"]["content"]
