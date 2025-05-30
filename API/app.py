import logging
import queue
import threading
from flask import Flask, jsonify, request
import os
import random
import string
import re
from g4f.client import Client
from datetime import datetime
from flask_cors import CORS

# Flask app setup
app = Flask(__name__)
CORS(app)

log_level = logging.DEBUG
log_file = 'app.log'
log_file_mode = 'a'
log_format = '%(asctime)s - %(levelname)s - %(message)s'

logging.basicConfig(level=log_level, filename=log_file, filemode=log_file_mode, format=log_format)

# Add console handler if you want logs to also appear in the console
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_handler.setFormatter(logging.Formatter(log_format))
app.logger.addHandler(console_handler)

# Example usage of logging in your app
app.logger.info('Starting Flask app')

# Counter to track code generation failures
code_generation_failures = {}
avoid = "do not add any Chinese word in the response, go with pure English"

# Function to generate a random folder name
def generate_random_folder_name(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Function to extract code sections from the response
def extract_code_sections(response):
    sections = {"html": "", "css": "", "js": ""}
    
    html_pattern = re.compile(r'```html:?(.*?)```', re.DOTALL | re.IGNORECASE)
    css_pattern = re.compile(r'```css:?(.*?)```', re.DOTALL | re.IGNORECASE)
    js_pattern = re.compile(r'```javascript(.*?)```', re.DOTALL | re.IGNORECASE)
    
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

# Function to check if the JS content is present
def is_js_present(js_content):
    return bool(js_content.strip())

# Function to check if the HTML content contains <div> tags
def contains_div_tags(html_content):
    return bool(re.search(r'<div[^>]*>', html_content, re.IGNORECASE))

# Function to regenerate the code
def regenerate_code(prompt):
    client = Client()
    retry = True

    while retry:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        response_content = response.choices[0].message.content

        if "您的ip已由于触发防滥用检测而被封禁" in response_content:
            continue
        else:
            retry = False

    return response_content

# Function to generate a page
def generate_page(page, original_prompt, base_prompt):
    prompt = f"{original_prompt} - {page} page: {base_prompt}"
    
    while True:
        response_content = regenerate_code(prompt)
        code_sections = extract_code_sections(response_content)

        if not is_complete_html(code_sections["html"]) or not contains_div_tags(code_sections["html"]):
            print(f"Incomplete HTML or missing <div> tags detected for {page}. Regenerating...")
            app.logger.info(f"Incomplete HTML or missing <div> tags detected for {page}. Regenerating...")
            continue

        break

    return code_sections


# Functions
# (same as before)

# Generate page route
@app.route('/generate', methods=['POST'])
def generate():
    global code_generation_failures
    original_prompt = request.json.get('prompt')
    app.logger.info('generation started..')
    client = Client()
    
    # Get the page name
    page_prompt = f"Provide a single, concise page name that best represents the website based on the prompt: {original_prompt} and {avoid}"
    page_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": page_prompt}]
    )
    page_name = page_response.choices[0].message.content.strip()
    
    base_prompt = '''Generate a complete, production-ready web page for a page using modern web development best practices. The page should be visually striking, highly functional, and optimized for performance and SEO. Utilize HTML5, Tailwind CSS (via CDN), custom CSS for enhancements, and JavaScript (ES6+). Include the following elements:

    HTML Structure:

Use semantic HTML5 tags for improved accessibility and SEO
Implement proper document structure with appropriate meta tags
Include a responsive viewport meta tag


Styling:

Utilize Tailwind CSS classes for primary layout and design
Implement custom CSS for unique color enhancements and specific styling needs
Create a visually appealing color scheme using a harmonious palette (suatable and best)
Apply gradient backgrounds where appropriate (suatable)
Incorporate subtle, smooth animations to enhance user experience (best applyable)


Custom Elements:

Design and implement custom SVG elements for icons, illustrations, or decorative purposes (provide complete SVG code)
Fetch and display high-quality, relevant images from the Pexels API (include API call in JavaScript , get the pixel api from .env file ())


Layout and Components:

Create a responsive header with logo and navigation menu
Design a visually engaging hero section relevant to the page
Implement content sections with appropriate layout for the page type
Include interactive elements like buttons, forms, or cards with hover effects
Design a footer with copyright info and social media links


Animations and Interactivity:

Add subtle scroll animations for content reveal
Implement smooth transitions for interactive elements
Create micro-interactions for buttons and links


JavaScript Functionality:

Implement any necessary interactive features (e.g., modals, sliders, form validation)
Add event listeners for user interactions
Implement lazy loading for images and heavy content


SEO Optimization:

Generate SEO-optimized content for this page (minimum 300 words)
Include appropriate headings (H1, H2, H3) with relevant keywords
Add meta description and title tags
Implement schema markup relevant to the page content


Performance Optimization:

Minify CSS and JavaScript
Optimize images and use appropriate formats (WebP where supported)
Implement critical CSS for above-the-fold content


Accessibility:

Ensure proper color contrast ratios
Add appropriate ARIA labels and roles
Implement keyboard navigation support


Additional Features:

Implement a simple cookie consent banner
Create a "Back to Top" button that appears on scroll



Provide the complete, production-ready HTML, CSS (both Tailwind classes and custom CSS), and JavaScript code for the this page. Include inline comments explaining key sections and any complex logic.and{avoid}'''

    
    while True:
        response_content = regenerate_code(base_prompt)
        code_sections = extract_code_sections(response_content)

        if not is_complete_html(code_sections["html"]) or not contains_div_tags(code_sections["html"]):
            print(f"Incomplete HTML or missing <div> tags detected for {page_name}. Regenerating...")
            app.logger.info(f"Incomplete HTML or missing <div> tags detected for {page_name}. Regenerating...")
            continue

        break
    
    return jsonify(code_sections)

if __name__ == "__main__":
    app.run(debug=False, port=5000)