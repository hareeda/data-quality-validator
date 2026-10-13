from ollama import chat

response = chat(
    model="llama3.2",
    messages=[
        {
            "role": "user",
            "content": "What are the five dimensions of data quality?"
        }
    ]
)

print(response["message"]["content"])