import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key="AIzaSyBZCIJ0OKe3TOA1MDQy56PxHGR3Af4DkPA")
model = genai.GenerativeModel('gemini-pro')

chat_completion = model.generate_content(
    "Hello , reply in enlish only , write a paragraph on india , about 500 words"
)

for completion in chat_completion:
    print(completion.text or "", end="", flush=True)
