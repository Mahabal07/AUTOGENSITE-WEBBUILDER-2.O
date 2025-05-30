from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import random
import string
import re
from g4f.client import Client

app = Flask(__name__)

# Counter to track code generation failures
code_generation_failures = {}

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

# Function to check if the HTML content is complete
def is_complete_html(html_content):
    return re.search(r'<html[^>]*>', html_content, re.IGNORECASE) and re.search(r'</html>', html_content, re.IGNORECASE)

# Function to check if the CSS content is present
def is_css_present(css_content):
    return bool(css_content.strip())

# Function to check if the JS content is present
def is_js_present(js_content):
    return bool(js_content.strip())

# Function to check if the HTML content contains <div> tags
def contains_div_tags(html_content):
    return bool(re.search(r'<div[^>]*>', html_content, re.IGNORECASE))

# Function to handle the creation and regeneration of files
def create_files(code_sections, folder_name):
    folder_path = os.path.join('generated_folders', folder_name)
    
    # Create the folder
    os.makedirs(folder_path, exist_ok=True)
    
    # Write HTML content to index.html
    with open(os.path.join(folder_path, 'index.html'), 'w', encoding='utf-8') as html_file:
        html_content = code_sections["html"]
        
        # Check if <head> tag exists and if the stylesheet link is already present
        head_tag_index = html_content.find('</head>')
        if head_tag_index != -1:
            # Check if the <link> tag for the stylesheet is present
            if '<link rel="stylesheet" href="styles.css">' not in html_content:
                # Insert the <link> tag inside <head>
                html_content = html_content[:head_tag_index] + '<link rel="stylesheet" href="styles.css">\n' + html_content[head_tag_index:]
        else:
            # If <head> tag does not exist, just append the <link> tag at the beginning
            html_content = '<link rel="stylesheet" href="styles.css">\n' + html_content
        
        # Check if <script> tag exists and add if not
        if '<script src="script.js"></script>' not in html_content:
            body_tag_index = html_content.find('</body>')
            if body_tag_index != -1:
                html_content = html_content[:body_tag_index] + '<script src="script.js"></script>\n' + html_content[body_tag_index:]
            else:
                # If </body> tag does not exist, just append the <script> tag at the end
                html_content += '<script src="script.js"></script>'
        
        html_file.write(html_content)
    
    # Write CSS content to styles.css
    with open(os.path.join(folder_path, 'styles.css'), 'w', encoding='utf-8') as css_file:
        css_file.write(code_sections["css"])
    
    # Write JavaScript content to script.js
    with open(os.path.join(folder_path, 'script.js'), 'w', encoding='utf-8') as js_file:
        js_file.write(code_sections["js"])

def regenerate_section(client, prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Function to enhance the prompt
def enhance_prompt(prompt):
    client = Client()
    enhancement_prompt = prompt + ' enhance this prompt in 50 words, and provide the enhanced prompt like, your enhanced prompt is :'
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": enhancement_prompt}]
    )
    
    response_content = response.choices[0].message.content
    
    # Extract the enhanced prompt
    start_delimiter = "your enhanced prompt is :"
    start_index = response_content.find(start_delimiter)
    
    if start_index != -1:
        start_index += len(start_delimiter)
        enhanced_prompt = response_content[start_index:].strip()
    else:
        enhanced_prompt = prompt  # Fallback to original prompt if extraction fails
    
    return enhanced_prompt

# Function to regenerate code with a modified prompt
def regenerate_code(prompt):
    client = Client()
    retry = True

    while retry:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )

        response_content = response.choices[0].message.content

        if "您的ip已由于触发防滥用检测而被封禁" in response_content:
            continue
        else:
            retry = False

    return response_content

# Route to generate code
@app.route('/generate', methods=['POST'])
def generate():
    global code_generation_failures
    original_prompt = request.json.get('prompt')
    
    # Enhance the prompt
    enhanced_prompt = enhance_prompt(original_prompt)
    
    base_prompt = ''' Please create a cutting-edge, visually stunning web page using HTML5, Tailwind CSS, and JavaScript. Ensure a futuristic, dark-mode design with animated gradients and parallax scrolling effects. Implement a responsive layout with distinct sections: a fixed header with frosted glass effect and animated SVG logo, an eye-catching hero section with 3D animations, multiple content sections showcasing various layouts and interactive elements, and a multi-column footer. Include advanced features like a live chat widget, dark mode toggle, infinite scrolling, and data visualizations using Chart.js. Integrate free APIs (e.g., REST Countries) for dynamic content. Add micro-interactions, custom animations, and a simple interactive game or puzzle. Ensure accessibility with ARIA attributes and semantic HTML. Use Tailwind CSS for primary styling, supplemented by custom CSS for enhanced effects. Include the Tailwind CSS CDN link. Implement modern JavaScript (ES6+) for functionality, including localStorage for user preferences. Optimize performance with lazy loading and efficient asset management. Provide high-quality SVGs, optimized images, and custom web fonts. Include detailed code comments and a README file. Please provide the complete, well-structured HTML, CSS (including Tailwind configurations), and JavaScript code separately, ensuring all external resources are properly linked and functional.'''

    prompt = enhanced_prompt + base_prompt

    # Check if there have been more than 3 failures for the same page
    if prompt in code_generation_failures and code_generation_failures[prompt] >= 3:
        return jsonify({"retry": True})

    while True:
        response_content = regenerate_code(prompt)
        code_sections = extract_code_sections(response_content)

        # Check if HTML content needs regeneration
        if not is_complete_html(code_sections["html"]) or not contains_div_tags(code_sections["html"]):
            print("Incomplete HTML or missing <div> tags detected. Regenerating HTML, CSS, and JavaScript...")
            prompt_html = "Incomplete HTML or missing <div> tags detected. Regenerat HTML, CSS, and JavaScript"
            code_sections = extract_code_sections(regenerate_code(prompt_html))
            continue

        if not is_css_present(code_sections["css"]):
            print("Missing CSS detected. Regenerating CSS...")
            prompt_css = prompt + " Please regenerate the CSS code."
            code_sections["css"] = extract_code_sections(regenerate_code(prompt_css))["css"]
            continue

        if not is_js_present(code_sections["js"]):
            print("Missing JavaScript detected. Regenerating JavaScript...")
            prompt_js = prompt + " Please regenerate the JavaScript code."
            code_sections["js"] = extract_code_sections(regenerate_code(prompt_js))["js"]
            continue

        break

    folder_name = generate_random_folder_name()
    create_files(code_sections, folder_name)

    # Reset failure count on successful generation
    if prompt in code_generation_failures:
        del code_generation_failures[prompt]

    return jsonify({"folder": folder_name})

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