from g4f.client import Client

client = Client()

chat_completion = client.chat.completions.create(model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello , reply in enlish only , write a paragraph on india , about 500 words"}], stream=True)

for completion in chat_completion:
    print(completion.choices[0].delta.content or "", end="", flush=True)
