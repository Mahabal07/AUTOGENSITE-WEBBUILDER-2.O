import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key="AIzaSyBZCIJ0OKe3TOA1MDQy56PxHGR3Af4DkPA")
model = genai.GenerativeModel('gemini-pro')

response = model.generate_content(
    "Hello",
    generation_config=genai.GenerateContentConfig(max_output_tokens=100),
)
print(response.text)