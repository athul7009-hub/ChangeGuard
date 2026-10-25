
import ollama

response = ollama.chat(
    model="qwen3:8b",
    messages=[
        {
            "role": "user",
            "content": (
                "Explain in two simple sentences "
                "why testing code changes is important."
            ),
        }
    ],
)

print(response["message"]["content"])
