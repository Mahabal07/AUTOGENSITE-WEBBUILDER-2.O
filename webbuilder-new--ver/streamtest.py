from flask import Flask, render_template, request, jsonify, send_from_directory, stream_with_context, Response
import os
import random
import string
import re
import google.generativeai as genai

app = Flask(__name__)

# Configure Gemini API
genai.configure(api_key="AIzaSyBZCIJ0OKe3TOA1MDQy56PxHGR3Af4DkPA")
model = genai.GenerativeModel('gemini-pro')

# Function to generate a random folder name
def generate_random_folder_name(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Function to extract code sections from the response
def extract_code_sections(response):
    sections = {"html": "", "css": "", "js": ""}
    
    # Regular expressions to match code blocks
    html_pattern = re.compile(r'```html:?(.*?)```', re.DOTALL | re.IGNORECASE)
    css_pattern = re.compile(r'```css:?(.*?)```', re.DOTALL | re.IGNORECASE)
    js_pattern = re.compile(r'```javascript(.*?)```', re.DOTALL | re.IGNORECASE)
    
    # Search for HTML, CSS, JS code blocks
    html_match = html_pattern.search(response)
    css_match = css_pattern.search(response)
    js_match = js_pattern.search(response)
    
    if html_match:
        sections["html"] = html_match.group(1).strip()
    if css_match:
        sections["css"] = css_match.group(1).strip()
    if js_match:
        sections["js"] = js_match.group(1).strip()
    
    return sections

# Function to generate code in stream mode
def stream_code_generation(prompt):
    response_stream = model.generate_content(prompt)

    html_content = ""
    css_content = ""
    js_content = ""
    
    for completion in response_stream:
        chunk = completion.text or ""
        print(chunk , end="")
        yield chunk
        html_content += chunk
        

    code_sections = extract_code_sections(html_content)
    return code_sections

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle stream code generation
@app.route('/generate', methods=['POST'])
def generate():
    prompt = request.json.get('prompt')

    @stream_with_context
    def stream():
        # Generate the folder name and path
        folder_name = generate_random_folder_name()
        folder_path = os.path.join('generated_folders', folder_name)
        os.makedirs(folder_path, exist_ok=True)

        # Create the index.html file
        with open(os.path.join(folder_path, 'index.html'), 'w', encoding='utf-8') as html_file:
            html_file.write('<!DOCTYPE html>\n<html>\n<head>\n<title>Live Generation</title>\n</head>\n<body>\n')
            html_file.write('<div id="content">\n')
            html_file.flush()

            # Stream the code generation
            code_sections = stream_code_generation(prompt)
            for chunk in code_sections:
                html_file.write(chunk)
                html_file.flush()
                yield chunk

            html_file.write('\n</div>\n</body>\n</html>')
            html_file.flush()

        # Close the stream
        yield '[DONE]'

    return Response(stream(), content_type='text/html')

# Route to serve the generated files
@app.route('/view/<folder>/<path:filename>')
def view(folder, filename):
    return send_from_directory(os.path.join('generated_folders', folder), filename)

# Route to handle retrying after multiple failures
@app.route('/retry', methods=['POST'])
def retry_generation():
    global code_generation_failures
    prompt = request.json.get('prompt')

    if prompt in code_generation_failures:
        code_generation_failures[prompt] += 1
    else:
        code_generation_failures[prompt] = 1

    return jsonify({"retry": True})

# URL generator for Flask-Frozen
@app.route('/<path:filename>.html')
def static_page(filename):
    return render_template(f'{filename}.html')

def freeze_config(app):
    @app.route('/index.html')
    def frozen_index():
        return render_template('index.html')

def main():
    app.run(debug=True)

if __name__ == "__main__":
    main()
