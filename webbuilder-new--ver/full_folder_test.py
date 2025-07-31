import logging
import queue
import threading
from flask import Flask, jsonify, request, render_template, send_from_directory, Response
import os
import random
import string
import re
import google.generativeai as genai
from datetime import datetime
import json
import time

# Flask app setup
app = Flask(__name__)

# Configure Gemini API
genai.configure(api_key="AIzaSyBZCIJ0OKe3TOA1MDQy56PxHGR3Af4DkPA")
model = genai.GenerativeModel('gemini-pro')

# Logging configuration
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
avoid ="do not add any chineese word in the reponse , go with pure english "

# Your existing code below
def write_to_log(new_content, file_path='logs.txt'):
    # Get the current date and time
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Create the log content with date and time
    log_entry = f"{current_time} - {new_content}"
    
    try:
        with open(file_path, 'a') as file:
            file.write(log_entry + '\n')  # Adding a newline character for readability
        app.logger.info(f"Content successfully written to {file_path}")
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")



# Example usage
file_path = 'logs.txt'
# new_content = 'This is the new log entry.'


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

# Function to handle the creation and regeneration of files
def create_files(code_sections, folder_name, page_name):
    folder_path = os.path.join('generated_folders', folder_name)
    os.makedirs(folder_path, exist_ok=True)
    
    # Format the page file name
    file_name = 'index.html' if page_name.lower() == 'home' else f"{page_name.lower().replace(' ', '-')}.html"
    
    # Save HTML file
    with open(os.path.join(folder_path, file_name), 'w', encoding='utf-8') as html_file:
        html_content = code_sections["html"]
        
        # Add Tailwind CSS CDN if not present
        tailwind_cdn = '<script src="https://cdn.tailwindcss.com"></script>'
        if '<head>' in html_content and tailwind_cdn not in html_content:
            html_content = html_content.replace(
                '<head>',
                f'<head>\n    {tailwind_cdn}'
            )
        elif '</title>' in html_content and tailwind_cdn not in html_content:
            html_content = html_content.replace(
                '</title>',
                f'</title>\n    {tailwind_cdn}'
            )
        elif not tailwind_cdn in html_content:
            # If no head tag exists, add it
            html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {tailwind_cdn}
    <title>{page_name}</title>
'''     + html_content
        
        head_tag_index = html_content.find('</head>')
        if head_tag_index != -1:
            # Link specific page styles and global styles
            html_content = html_content[:head_tag_index] + f'<link rel="stylesheet" href="{page_name.lower().replace(" ", "-")}.css">\n<link rel="stylesheet" href="global-style.css">\n' + html_content[head_tag_index:]
        else:
            html_content = f'<link rel="stylesheet" href="{page_name.lower().replace(" ", "-")}.css">\n<link rel="stylesheet" href="global-style.css">\n' + html_content
        
        # Add the corresponding script file at the end of the body tag
        body_tag_index = html_content.find('</body>')
        if body_tag_index != -1:
            html_content = html_content[:body_tag_index] + f'<script src="{page_name.lower().replace(" ", "-")}.js"></script>\n' + html_content[body_tag_index:]
        else:
            html_content += f'<script src="{page_name.lower().replace(" ", "-")}.js"></script>'
        
        html_file.write(html_content)

    # Save CSS to a page-specific file
    css_filename = 'home.css' if page_name.lower() == 'home' else f"{page_name.lower().replace(' ', '-')}.css"
    with open(os.path.join(folder_path, css_filename), 'w', encoding='utf-8') as css_file:
        css_file.write(code_sections["css"])
    
    # Save JS to a page-specific file
    js_filename = 'home.js' if page_name.lower() == 'home' else f"{page_name.lower().replace(' ', '-')}.js"
    with open(os.path.join(folder_path, js_filename), 'w', encoding='utf-8') as js_file:
        js_file.write(code_sections["js"])

    print(f'Page {page_name} generated successfully.')
    new_content =f"Page {page_name} generated successfully."
    write_to_log(new_content )

# Function to regenerate the code
def regenerate_code(prompt):
    response = model.generate_content(prompt)
    response_content = response.text

    if "您的ip已由于触发防滥用检测而被封禁" in response_content:
        return regenerate_code(prompt) # Retry on abuse detection

    return response_content

# Function to generate a page
def generate_page(page, original_prompt, base_prompt, folder_name, result_queue):
    prompt = f"{original_prompt} - {page} page: {base_prompt}"
    # Force a log entry to test
    app.logger.info('Starting Flask app')
    
    while True:
        response_content = regenerate_code(prompt)
        code_sections = extract_code_sections(response_content)

        if not is_complete_html(code_sections["html"]) or not contains_div_tags(code_sections["html"]):
            print(f"Incomplete HTML or missing <div> tags detected for {page}. Regenerating...")
            new_content =f"Incomplete HTML or missing <div> tags detected for {page}. Regenerating..."
            write_to_log(new_content )
            continue

        break

    create_files(code_sections, folder_name, page)
    result_queue.put(page)

def generate_navbar_css(navbar_html):
    """Generate custom CSS for the navbar using AI"""
    prompt = f"""
    Given this navbar HTML:
    {navbar_html}
    
    Generate modern, professional CSS that will:
    1. Create a sleek, professional navigation bar
    2. Include smooth hover transitions
    3. Ensure proper spacing and alignment
    4. Make the navbar sticky/fixed at the top
    5. Handle both light and dark modes
    6. Include responsive design for mobile
    7. Add subtle shadows and depth
    8. Ensure high contrast and readability
    
    Return ONLY the CSS code wrapped in ```css``` tags.
    """
    
    try:
        response = model.generate_content(prompt)
        css_content = response.text
        
        # Extract CSS from code blocks
        css_match = re.search(r'```css(.*?)```', css_content, re.DOTALL)
        if css_match:
            return css_match.group(1).strip()
        return ""
    except Exception as e:
        app.logger.error(f"Failed to generate navbar CSS: {str(e)}")
        return ""

def generate_custom_navbar(pages):
    """Generate the standardized navbar HTML"""
    navbar_html = '''
    <nav class="main-nav">
        <div class="nav-container">
            <div class="nav-content">
                <!-- Logo -->
                <div class="nav-logo">
                    <a href="index.html">
                        <img src="/path/to/logo.svg" alt="Logo">
                    </a>
                </div>

                <!-- Desktop Navigation -->
                <div class="nav-links">
                    <ul class="nav-list">
                        {nav_links}
                    </ul>
                </div>
            </div>
        </div>
    </nav>
    '''
    
    nav_links = []
    for page in pages:
        file_name = 'index.html' if page.lower() == 'home' else f"{page.lower().replace(' ', '-')}.html"
        link_text = page.replace('-', ' ').title()
        nav_links.append(f'<li class="nav-item"><a href="{file_name}">{link_text}</a></li>')
    
    return navbar_html.format(nav_links='\n'.join(nav_links))

def update_html_with_navbar(folder_name, pages):
    """Update HTML files with navbar and create/link navbar CSS"""
    folder_path = os.path.join('generated_folders', folder_name)
    
    # Generate navbar HTML and CSS
    navbar_html = generate_custom_navbar(pages)
    navbar_css = generate_navbar_css(navbar_html)
    
    # Save navbar CSS to file
    css_path = os.path.join(folder_path, 'navbar.css')
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(navbar_css)
    
    # Update each HTML file
    for page in pages:
        file_name = 'index.html' if page.lower() == 'home' else f"{page.lower().replace(' ', '-')}.html"
        file_path = os.path.join(folder_path, file_name)
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Add Tailwind CSS CDN if not present
        tailwind_cdn = '<script src="https://cdn.tailwindcss.com"></script>'
        if tailwind_cdn not in content:
            if '<head>' in content:
                content = content.replace('<head>', f'<head>\n    {tailwind_cdn}')
            elif '</title>' in content:
                content = content.replace('</title>', f'</title>\n    {tailwind_cdn}')
        
        # Remove any existing navigation elements
        content = re.sub(r'<nav\b[^>]*>.*?</nav>', '', content, flags=re.DOTALL)
        
        # Add navbar CSS link in head if not present
        css_link = '<link rel="stylesheet" href="navbar.css">'
        if '</head>' in content and css_link not in content:
            content = content.replace('</head>', f'    {css_link}\n</head>')
        
        # Insert navbar after body tag
        body_tag_index = content.find('<body')
        if body_tag_index != -1:
            closing_bracket_index = content.find('>', body_tag_index)
            if closing_bracket_index != -1:
                updated_content = (
                    content[:closing_bracket_index + 1] + 
                    '\n' + navbar_html + 
                    content[closing_bracket_index + 1:]
                )
                
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(updated_content)
        
        write_to_log(f"Updated {file_name} with custom navbar and ensured Tailwind CSS")

def update_navbar_links(folder_name, pages):
    print("navbar updation starts...")
    new_content ="navbar updation starts..."
    write_to_log( new_content)
    folder_path = os.path.join('generated_folders', folder_name)

    for page_name in pages:
        # Format the page file name
        file_name = 'index.html' if page_name.lower() == 'home' else f"{page_name.lower().replace(' ', '-')}.html"
        file_path = os.path.join(folder_path, file_name)

        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Update href links in the navbar
        for p in pages:
            # Format the href links just like the file names
            new_href = 'index.html' if p.lower() == 'home' else f"{p.lower().replace(' ', '-')}.html"
            
            # Remove any leading or trailing slashes from the new href
            new_href = new_href.strip('/')

            # Update the href attribute in the navbar
            content = re.sub(
                rf'href=["\'](?:/{re.escape(p.lower())}\.html|/{re.escape(p.lower().replace(" ", "-"))}\.html)["\']',
                f'href="{new_href}"',
                content
            )

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
            print(f"Updated navbar links in {p}")
            new_content =f"Updated navbar links in {p}"
            write_to_log(new_content)


        new_content =f"Updated navbar links in {file_name}"
        write_to_log(new_content)
        print(f"Updated navbar links in {file_name}")
        

# Example usage:
# update_navbar_links('my_folder', ['Home', 'About Us', 'Contact'])

# Force a log entry to test
app.logger.info('Starting Flask app')
@app.route('/')
def index():
    app.logger.info('Index route accessed')
    return render_template('index.html')

# Generate pages route
@app.route('/generate', methods=['POST'])
def generate():
    try:
        global generated_pages, total_pages
        generated_pages = []  # Reset for new generation
        
        original_prompt = request.json.get('prompt')
        if not original_prompt:
            return jsonify({"error": "No prompt provided"}), 400

        folder_name = generate_random_folder_name()
        result_queue = queue.Queue()

        # Updated pages prompt with strict English-only rules
        pages_prompt = f"""STRICT RULES FOR PAGE GENERATION:
1. RESPOND ONLY IN ENGLISH
2. NO CHINESE CHARACTERS ALLOWED
3. NO EXPLANATIONS OR APOLOGIES
4. RETURN ONLY PAGE NAMES
5. USE ONLY ASCII CHARACTERS

Based on this website requirement: {original_prompt}

FORMAT RULES:
1. Return ONLY comma-separated page names
2. "Home" MUST be the first page
3. Each page name must be Capitalized
4. Maximum 8 pages total
5. Use standard website page names
6. NO special characters except commas
7. NO numbers in page names

VALID EXAMPLES:
"Home, About, Services, Contact"
"Home, Products, Gallery, Blog"
"Home, Portfolio, Team, Contact"

INVALID EXAMPLES:
"主页, About" (NO Chinese characters)
"home, about" (must be Capitalized)
"I suggest..." (NO explanations)
"Contact-Us" (NO special characters)

COMMON PAGE NAMES TO USE:
- Home (required, must be first)
- About
- Services
- Products
- Portfolio
- Gallery
- Blog
- Contact
- Team
- Pricing
- FAQ

Return ONLY the comma-separated page names:"""

        # Add validation after getting the response
        def validate_page_names(pages_raw):
            # Check for Chinese characters
            if any('\u4e00' <= char <= '\u9fff' for char in pages_raw):
                raise ValueError("Response contains Chinese characters")
            
            # Clean and validate page names
            pages = [
                page.strip().strip('"\'').capitalize() 
                for page in pages_raw.split(',')
                if page.strip() and all(ord(char) < 128 for char in page.strip())
            ]
            
            # Ensure Home is first
            if "Home" not in pages:
                pages.insert(0, "Home")
            elif pages[0] != "Home":
                pages.remove("Home")
                pages.insert(0, "Home")
            
            return pages

        # Get pages with validation
        pages_response = model.generate_content(pages_prompt + "\n\nIMPORTANT: RESPOND ONLY IN ENGLISH WITH COMMA-SEPARATED PAGE NAMES.")
        
        try:
            pages = validate_page_names(pages_response.text.strip())
        except ValueError as e:
            # If validation fails, use default pages
            app.logger.warning(f"Page validation failed: {str(e)}. Using default pages.")
            pages = ["Home", "About", "Services", "Contact"]
        
        # Set total pages (including navbar update)
        total_pages = len(pages) + 1
        
        app.logger.info(f"Generated pages: {pages}")
        
        # Format base_prompt with available pages
        formatted_base_prompt = base_prompt.format(
            page_name="{page_name}",  # This will be formatted later for each page
            pages=", ".join(pages)
        )
        
        # Generate pages
        threads = []
        for page in pages:
            thread = threading.Thread(
                target=generate_page,
                args=(page, original_prompt, formatted_base_prompt, folder_name, result_queue)
            )
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Collect results
        while not result_queue.empty():
            result = result_queue.get()
            generated_pages.append(result)
            
        # Update navbar (counts as final step)
        update_html_with_navbar(folder_name, generated_pages)
        update_navbar_links(folder_name, generated_pages)
        
        return jsonify({"folder": folder_name, "pages": generated_pages})
        
    except Exception as e:
        app.logger.error(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Route to serve generated files
@app.route('/view/<folder>/<path:filename>')
def view(folder, filename):
    return send_from_directory(os.path.join('generated_folders', folder), filename)

# Add progress tracking
@app.route('/progress')
def progress():
    def generate():
        global generated_pages, total_pages
        
        while True:
            try:
                # Calculate progress including navbar update
                completed = len(generated_pages)
                current_progress = int((completed / total_pages) * 100) if total_pages > 0 else 0
                
                data = {"progress": current_progress}
                yield f"data: {json.dumps(data)}\n\n"
                
                if current_progress >= 100:
                    break
                    
                time.sleep(0.5)
                
            except Exception as e:
                app.logger.error(f"Progress error: {str(e)}")
                break
    
    return Response(generate(), mimetype='text/event-stream')

# After other global variables, before routes
pages = []
result_queue = queue.Queue()
generated_pages = []
total_pages = 0

# Define base_prompt before the routes
base_prompt = '''Generate a cutting-edge, visually stunning web page for a {page_name} that follows modern design trends and best practices. The page should create an immediate "wow" factor and maintain high usability.

Available Pages for Navigation: {pages}

Logo and Branding:
- Use a relevant logo image from:
  * Unsplash: https://source.unsplash.com/random/[width]x[height]?logo
  * Picsum: https://picsum.photos/[width]/[height]?random=1
  * Lorem Picsum: https://picsum.photos/seed/logo/[width]/[height]
- Logo dimensions should be appropriate for header placement
- Include logo in navigation/header area
- Ensure logo is responsive
- Add subtle hover effects on logo

Visual Design Requirements:
- Implement a modern, cohesive color scheme that evokes the right emotions
- Use sophisticated gradient combinations and subtle patterns
- Include micro-interactions and smooth animations
- Utilize glass-morphism and neumorphic design elements
- Add parallax scrolling effects
- Implement skeleton loading states
- Create engaging section transitions
- Use modern card designs with hover effects

[... rest of your existing prompt content ...]'''

if __name__ == "__main__":
    app.run(debug=False)