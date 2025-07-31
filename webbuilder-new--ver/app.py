import logging
from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
import os
import random
import string
import re
import google.generativeai as genai
import requests
import threading
import queue
import shutil
import zipfile
from datetime import datetime, timedelta
import asyncio
import platform
import time

# Configure Gemini API
genai.configure(api_key="AIzaSyDH8326_llp1bhBIw1biLA1GDU4rs6TO6o")
model = genai.GenerativeModel('gemini-1.5-flash')

# Alternative free AI model (Hugging Face)
def use_huggingface_api(prompt):
    """Use Hugging Face's free API as alternative"""
    try:
        API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        headers = {"Authorization": "Bearer hf_xxx"}  # Free API, no key needed
        
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
        return response.json()[0]["generated_text"]
    except:
        return None

# Fallback function for when quota is exceeded
def generate_with_fallback(prompt):
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 4000,
                "temperature": 0.7
            }
        )
        return response.text
    except Exception as e:
        print(f"❌ API Error: {str(e)}")
        raise e

# Fix for Windows event loop warning
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Add cleanup configuration
CLEANUP_INTERVAL = 3600  # Run cleanup every hour
FOLDER_MAX_AGE = 24  # Maximum age of folders in hours

def cleanup_old_folders():
    """Remove folders older than FOLDER_MAX_AGE hours"""
    try:
        generated_folders_path = 'generated_folders'
        temp_zips_path = 'temp_zips'
        current_time = datetime.now()
        
        # Clean up generated_folders
        if os.path.exists(generated_folders_path):
            for folder_name in os.listdir(generated_folders_path):
                folder_path = os.path.join(generated_folders_path, folder_name)
                if os.path.isdir(folder_path):
                    folder_age = current_time - datetime.fromtimestamp(os.path.getctime(folder_path))
                    if folder_age > timedelta(hours=FOLDER_MAX_AGE):
                        try:
                            shutil.rmtree(folder_path)
                            print(f"Cleaned up old folder: {folder_name}")
                        except Exception as e:
                            print(f"Error cleaning up folder {folder_name}: {str(e)}")
        
        # Clean up temp_zips
        if os.path.exists(temp_zips_path):
            for folder_name in os.listdir(temp_zips_path):
                folder_path = os.path.join(temp_zips_path, folder_name)
                if os.path.isdir(folder_path):
                    folder_age = current_time - datetime.fromtimestamp(os.path.getctime(folder_path))
                    if folder_age > timedelta(hours=FOLDER_MAX_AGE):
                        try:
                            shutil.rmtree(folder_path)
                            print(f"Cleaned up old temp zip folder: {folder_name}")
                        except Exception as e:
                            print(f"Error cleaning up temp zip folder {folder_name}: {str(e)}")
    
    except Exception as e:
        print(f"Error in cleanup process: {str(e)}")

def cleanup_thread():
    """Background thread to periodically run cleanup"""
    while True:
        cleanup_old_folders()
        time.sleep(CLEANUP_INTERVAL)

# Start cleanup thread when the app starts
cleanup_thread = threading.Thread(target=cleanup_thread, daemon=True)
cleanup_thread.start()

avoid ="do not add any chineese word in the reponse , go with pure english "
app = Flask(__name__)
# DEBUG, INFO, WARNING, ERROR, CRITICAL
log_level = logging.DEBUG
log_file = 'app.log'
log_file_mode = 'a'
log_format = '%(asctime)s - %(levelname)s - %(message)s'

logging.basicConfig(level=log_level, filename=log_file, filemode=log_file_mode, format=log_format)

# Force a log entry to test
app.logger.info('Starting Flask app')
# Counter to track code generation failures
code_generation_failures = {}

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
    
    # Always use index.html for the home page
    file_name = 'index.html' if page_name.lower() == 'home' else f"{page_name.lower().replace(' ', '-')}.html"
    
    # Save HTML file
    with open(os.path.join(folder_path, file_name), 'w', encoding='utf-8') as html_file:
        html_content = code_sections["html"]
        
        # Ensure the HTML has proper structure
        if not html_content.strip().startswith('<!DOCTYPE html>'):
            html_content = '<!DOCTYPE html>\n' + html_content
        
        if not re.search(r'<html[^>]*>', html_content, re.IGNORECASE):
            html_content = '<html lang="en">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>' + page_name + '</title>\n<script src="https://cdn.tailwindcss.com"></script>\n</head>'
        
        if not re.search(r'<body[^>]*>', html_content, re.IGNORECASE):
            html_content = html_content.replace('</head>', '</head>\n<body>', 1)
            html_content += '\n</body>'
        
        if not re.search(r'</html>', html_content, re.IGNORECASE):
            html_content += '\n</html>'
        
        # Ensure there's at least one div
        if not re.search(r'<div[^>]*>', html_content, re.IGNORECASE):
            body_content = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
            if body_content:
                new_body_content = f'<body>\n<div class="container">\n{body_content.group(1)}\n</div>\n</body>'
                html_content = html_content.replace(body_content.group(0), new_body_content)
        
        # Add CSS and JS links without navbar (navbar will be added later)
        head_tag_index = html_content.find('</head>')
        if head_tag_index != -1:
            # Link specific page styles and global styles
            css_filename = 'home.css' if page_name.lower() == 'home' else f"{page_name.lower().replace(' ', '-')}.css"
            html_content = html_content[:head_tag_index] + f'<link rel="stylesheet" href="{css_filename}">\n<link rel="stylesheet" href="global-style.css">\n' + html_content[head_tag_index:]
        else:
            css_filename = 'home.css' if page_name.lower() == 'home' else f"{page_name.lower().replace(' ', '-')}.css"
            html_content = f'<link rel="stylesheet" href="{css_filename}">\n<link rel="stylesheet" href="global-style.css">\n' + html_content
        
        # Add the corresponding script file at the end of the body tag
        body_tag_index = html_content.find('</body>')
        if body_tag_index != -1:
            js_filename = 'home.js' if page_name.lower() == 'home' else f"{page_name.lower().replace(' ', '-')}.js"
            html_content = html_content[:body_tag_index] + f'<script src="{js_filename}"></script>\n' + html_content[body_tag_index:]
        else:
            js_filename = 'home.js' if page_name.lower() == 'home' else f"{page_name.lower().replace(' ', '-')}.js"
            html_content += f'<script src="{js_filename}"></script>'
        
        html_file.write(html_content)

    # Save CSS to a page-specific file
    css_filename = 'home.css' if page_name.lower() == 'home' else f"{page_name.lower().replace(' ', '-')}.css"
    with open(os.path.join(folder_path, css_filename), 'w', encoding='utf-8') as css_file:
        css_file.write(code_sections["css"])
    
    # Save JS to a page-specific file
    js_filename = 'home.js' if page_name.lower() == 'home' else f"{page_name.lower().replace(' ', '-')}.js"
    with open(os.path.join(folder_path, js_filename), 'w', encoding='utf-8') as js_file:
        js_file.write(code_sections["js"])

# Function to regenerate the code
def regenerate_code(prompt):
    retry_count = 0
    max_retries = 3

    # Simplified and more explicit prompt
    format_instructions = """
You MUST respond with exactly three code blocks in this exact order:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Title</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
    <!-- Your HTML content here -->
</body>
</html>
```

```css
/* Your CSS styles here */
```

```javascript
// Your JavaScript code here
document.addEventListener('DOMContentLoaded', function() {
    // Initialize your JavaScript functionality
});
```

IMPORTANT: You must include all three code blocks: HTML, CSS, and JavaScript. Do not skip any of them."""

    while retry_count < max_retries:
        try:
            # Combine the original prompt with formatting instructions
            full_prompt = f"{prompt}\n\n{format_instructions}"
            
            response_content = generate_with_fallback(full_prompt)

            # Validate response format
            if not all(block in response_content.lower() for block in ['```html', '```css', '```javascript']):
                retry_count += 1
                continue

            return response_content

        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                raise Exception(f"Failed to generate code after {max_retries} attempts")

    raise Exception("Failed to generate valid code after maximum retries")

# Function to generate a page
def generate_page(page, original_prompt, base_prompt, folder_name, result_queue):
    try:
        # Create a page-specific prompt without the avoid variable
        page_prompt = base_prompt.replace('{avoid}', '')  # Remove the avoid placeholder
        page_prompt = page_prompt.format(
            page_name=page,
            original_prompt=original_prompt
        )
        
        # Add specific instructions based on page type
        if page.lower() == 'home':
            page_prompt += "\nCreate a dynamic landing page with: Hero section with animated background, feature cards in grid layout, testimonials carousel, statistics section, and prominent call-to-action. Use vibrant colors and modern animations."
        elif page.lower() == 'about':
            page_prompt += "\nCreate a professional About page with: Timeline layout for company history, team grid with circular profile images, mission statement in card format, values displayed as icons, and statistics in counter format. Use professional color scheme with blue/gray tones."
        elif page.lower() == 'services' or page.lower() == 'products':
            page_prompt += "\nCreate a modern Services page with: Service cards in masonry layout, pricing tables with hover effects, feature comparison in table format, testimonials in slider, and FAQ accordion. Use gradient backgrounds and modern card designs."
        elif page.lower() == 'contact':
            page_prompt += "\nCreate a clean Contact page with: Contact form on left, business info on right, embedded Google Maps iframe (MANDATORY), social media icons, and business hours in card format. Use minimal design with focus on functionality."
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response_content = regenerate_code(page_prompt)
                code_sections = extract_code_sections(response_content)

                if not is_complete_html(code_sections["html"]):
                    retry_count += 1
                    continue

                # Validate page-specific content
                if page.lower() == 'home' and not re.search(r'hero|banner|main-content|<section|<h1', code_sections["html"], re.IGNORECASE):
                    # Do NOT retry, just log a warning and continue
                    pass
                elif page.lower() == 'about' and not re.search(r'about|mission|team|timeline|values|testimonial', code_sections["html"], re.IGNORECASE):
                    retry_count += 1
                    continue
                elif page.lower() == 'contact' and not re.search(r'contact|form|email|phone|map|iframe.*google|google.*maps', code_sections["html"], re.IGNORECASE):
                    retry_count += 1
                    continue
                elif page.lower() in ['services', 'products'] and not re.search(r'service|product|pricing|feature|testimonial|faq', code_sections["html"], re.IGNORECASE):
                    retry_count += 1
                    continue

                # If we get here, the page generation was successful
                create_files(code_sections, folder_name, page)
                print(f"✅ {page} page generated successfully!")
                result_queue.put(page)
                return

            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    result_queue.put(None)  # Signal failure
                    return

    except Exception as e:
        result_queue.put(None)  # Signal failure
        return

# New function to generate custom navbar
def generate_custom_navbar(pages):
    retry_count = 0
    max_retries = 3

    while retry_count < max_retries:
        try:
            print(f"🔗 Generating custom navbar (attempt {retry_count + 1}/{max_retries})...")
            navbar_prompt = f"""Create a simple, responsive navbar using Tailwind CSS for these pages: {', '.join(pages)}.

Requirements:
1. Use simple <nav> with <ul> and <li> elements
2. Each link should point to the exact .html file (e.g., index.html for Home, about.html for About)
3. Include a mobile hamburger menu for small screens
4. Use basic Tailwind classes for styling
5. Keep the design clean and minimal
6. Ensure all links work correctly with proper href attributes

Format your response with just the navbar HTML code, no explanations.

Example format:
<nav class="bg-white shadow-lg">
    <div class="max-w-6xl mx-auto px-4">
        <div class="flex justify-between">
            <div class="flex space-x-7">
                <div>
                    <a href="index.html" class="flex items-center py-4">
                        <span class="font-semibold text-gray-500 text-lg">Logo</span>
                    </a>
                </div>
                <div class="hidden md:flex items-center space-x-1">
                    <a href="index.html" class="py-4 px-2 text-gray-500 hover:text-gray-900 transition duration-300">Home</a>
                    <a href="about.html" class="py-4 px-2 text-gray-500 hover:text-gray-900 transition duration-300">About</a>
                </div>
            </div>
        </div>
    </div>
</nav>"""

            response_content = generate_with_fallback(navbar_prompt)

            # Extract the navbar HTML
            nav_pattern = re.compile(r'<nav.*?>(.*?)</nav>', re.DOTALL)
            nav_match = nav_pattern.search(response_content)

            if nav_match:
                navbar_html = nav_match.group(0)
                
                # Ensure all links are correct
                for page in pages:
                    file_name = 'index.html' if page.lower() == 'home' else f"{page.lower()}.html"
                    navbar_html = navbar_html.replace(f'href="{page.lower()}.html"', f'href="{file_name}"')
                    navbar_html = navbar_html.replace(f'href="{page}.html"', f'href="{file_name}"')
                    navbar_html = navbar_html.replace(f'href="/{page.lower()}.html"', f'href="{file_name}"')
                    navbar_html = navbar_html.replace(f'href="/{page}.html"', f'href="{file_name}"')
                
                return navbar_html
            else:
                print("Navbar not found in the generated content. Retrying...")
                retry_count += 1
                continue

        except Exception as e:
            print(f"❌ Error generating navbar: {str(e)}. Retry {retry_count + 1}/{max_retries}")
            retry_count += 1
            if retry_count >= max_retries:
                raise Exception(f"Failed to generate navbar after {max_retries} attempts: {str(e)}")

    raise Exception("Failed to generate valid navbar after maximum retries")

# Function to update HTML files with the custom navbar
def update_html_with_navbar(folder_name, pages):
    folder_path = os.path.join('generated_folders', folder_name)
    navbar_html = generate_custom_navbar(pages)
    
    for page in pages:
        file_name = 'index.html' if page.lower() == 'home' else f"{page.lower().replace(' ', '-')}.html"
        file_path = os.path.join(folder_path, file_name)
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Insert navbar after the <body> tag
        body_tag_index = content.find('<body')
        if body_tag_index != -1:
            closing_bracket_index = content.find('>', body_tag_index)
            if closing_bracket_index != -1:
                updated_content = content[:closing_bracket_index + 1] + '\n' + navbar_html + content[closing_bracket_index + 1:]
                
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(updated_content)
        
        print(f"Updated {file_name} with custom navbar.")

def update_navbar_links(folder_name, pages):
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

        print(f"Updated navbar links in {file_name}")

# Example usage:
# update_navbar_links('my_folder', ['Home', 'About Us', 'Contact'])

# Function to generate website name based on prompt
def generate_website_name(prompt):
    retry_count = 0
    max_retries = 3

    while retry_count < max_retries:
        try:
            print(f"🏷️ Generating website name (attempt {retry_count + 1}/{max_retries})...")
            name_prompt = f"""Based on this website description: "{prompt}", generate a professional, memorable website name.

Requirements:
1. The name should be 2-3 words maximum
2. It should be relevant to the website's purpose
3. It should be easy to remember and type
4. It should be professional and brandable
5. Avoid generic names
6. Do not include any special characters
7. Keep it in English only

Respond with ONLY the website name, nothing else. Example: "TechFlow" or "DigitalCraft" """

            response_text = generate_with_fallback(name_prompt)
            print(f"✅ Website name generated: {response_text}")
            
            # Clean up the response
            if response_text:
                # Remove any quotes or extra formatting
                response_text = response_text.replace('"', '').replace("'", '').strip()
                # Take only the first line if multiple lines
                response_text = response_text.split('\n')[0].strip()
                return response_text
            else:
                # Fallback to a generated name if the response is empty
                words = prompt.split()
                if len(words) >= 2:
                    return f"{words[0].capitalize()}{words[1].capitalize()}"
                return f"{prompt.split()[0].capitalize()}Site"
                
        except Exception as e:
            print(f"❌ Error generating website name: {str(e)}. Retry {retry_count + 1}/{max_retries}")
            retry_count += 1
            if retry_count >= max_retries:
                # Fallback to a simple name
                words = prompt.split()
                if len(words) >= 2:
                    return f"{words[0].capitalize()}{words[1].capitalize()}"
                return f"{prompt.split()[0].capitalize()}Site"

    # Final fallback
    words = prompt.split()
    if len(words) >= 2:
        return f"{words[0].capitalize()}{words[1].capitalize()}"
    return f"{prompt.split()[0].capitalize()}Site"

# Function to create a ZIP file of the generated website
def create_website_zip(folder_name, website_name):
    try:
        # Create a temporary directory for the ZIP
        temp_dir = os.path.join('temp_zips', folder_name)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Create a copy of the website folder with the website name
        website_folder = os.path.join('generated_folders', folder_name)
        zip_folder = os.path.join(temp_dir, website_name.replace(' ', '_'))
        shutil.copytree(website_folder, zip_folder)
        
        # Create ZIP file
        zip_filename = f"{website_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(zip_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, zip_folder)
                    zipf.write(file_path, arcname)
        
        return zip_path, zip_filename
    except Exception as e:
        print(f"Error creating ZIP file: {str(e)}")
        return None, None

@app.route('/')
def index():
    return render_template('index.html')

# Generate pages route
@app.route('/generate', methods=['POST'])
def generate():
    try:
        print("\n" + "="*60)
        print("🎯 WEBSITE GENERATION STARTED")
        print("="*60)
        
        global code_generation_failures
        original_prompt = request.json.get('prompt')
        
        if not original_prompt:
            return jsonify({"error": "No prompt provided"}), 400
        
        print(f"📝 Prompt: {original_prompt}")
        
        # Generate website name based on the prompt
        website_name = generate_website_name(original_prompt)
        print(f"🏷️ Website name: {website_name}")
        
        # Get the list of pages with a more structured prompt
        pages_prompt = f"""For a website about {original_prompt}, list exactly 3-5 essential pages.

Requirements:
- Only use these standard page names: Home, About, Services, Products, Contact, Blog, Portfolio
- Always start with Home page
- Choose 3-5 most relevant pages for this website
- Respond with ONLY the page names separated by commas, nothing else

Example response: Home, About, Services, Contact"""
        
        try:
            pages_response = generate_with_fallback(pages_prompt)
            
            response_text = pages_response.strip()
            
            # Extract pages with better error handling
            try:
                # Clean up the response and split by commas
                pages_text = response_text.replace('\n', '').replace(' ', '')
                pages = [page.strip() for page in pages_text.split(',') if page.strip()]
                
                # Validate page names
                valid_pages = ['Home', 'About', 'Services', 'Products', 'Contact', 'Blog', 'Portfolio']
                pages = [page for page in pages if any(valid.lower() == page.lower() for valid in valid_pages)]
                
                # If no valid pages found, use defaults
                if not pages:
                    pages = ['Home', 'About', 'Contact']
            except Exception as e:
                pages = ['Home', 'About', 'Contact']
            
            # Ensure we have between 3-5 pages
            if len(pages) > 5:
                pages = pages[:5]
            elif len(pages) < 3:
                # Add default pages if we have less than 3
                default_pages = ['Home', 'About', 'Contact']
                # Remove any duplicates
                pages = list(dict.fromkeys(pages + default_pages[:3-len(pages)]))
            
            # Ensure 'Home' is always the first page
            if 'Home' in pages:
                pages.remove('Home')
            pages = ['Home'] + pages
            
            print(f"📋 Pages: {', '.join(pages)}")
            
        except Exception as e:
            # Use default pages if there's an error
            pages = ['Home', 'About', 'Contact']
        
        folder_name = generate_random_folder_name()
        
        # Define base prompt here to ensure it's available
        base_prompt = '''
Create a unique, modern web page for the {page_name} page of a website about {original_prompt}.

Design Guidelines:
- Each page should have a distinct visual identity
- Use different layouts, color schemes, and typography for each page type
- Include modern design elements: gradients, shadows, animations
- Make each page feel unique while maintaining brand consistency
- Use high-quality images and icons
- Ensure excellent responsive design

Page-Specific Requirements:
- Home: Dynamic, engaging, conversion-focused
- About: Professional, trustworthy, story-driven
- Services: Modern, feature-rich, conversion-oriented
- Contact: Clean, functional, user-friendly

Technical Requirements:
- Use semantic HTML5 structure
- Include Tailwind CSS via CDN
- Add custom CSS for unique styling
- Include JavaScript for interactivity
- Ensure all code is production-ready

You MUST provide exactly three code blocks: HTML, CSS, and JavaScript.'''
        
        print(f"🔄 Generating {len(pages)} pages...")
        result_queue = queue.Queue()
        threads = []
        
        # Start thread for each page
        for page in pages:
            thread = threading.Thread(target=generate_page, args=(page, original_prompt, base_prompt, folder_name, result_queue))
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        # Collect results
        generated_pages = []
        failed_pages = []
        while not result_queue.empty():
            result = result_queue.get()
            if result is not None:
                generated_pages.append(result)
            else:
                failed_pages.append(result)

        if not generated_pages:
            return jsonify({"error": "Failed to generate any pages"}), 500

        # Update HTML files with custom navbar only if we have successful pages
        if generated_pages:
            try:
                update_html_with_navbar(folder_name, generated_pages)
                update_navbar_links(folder_name, generated_pages)
                print("🔗 Navbar updated successfully!")
            except Exception as e:
                # Continue even if navbar update fails
                pass
        
        # Create the ZIP file
        zip_path, zip_filename = create_website_zip(folder_name, website_name)
        
        if zip_path and os.path.exists(zip_path):
            print(f"📦 ZIP created: {zip_filename}")
            print(f"📁 Folder: {folder_name}")
            print("="*60)
            print("🎉 WEBSITE GENERATION COMPLETED!")
            print("="*60)
            
            return jsonify({
                "folder": folder_name,
                "pages": generated_pages,
                "failed_pages": failed_pages if failed_pages else None,
                "website_name": website_name,
                "download_url": f"/download/{folder_name}",
                "zip_path": zip_path,
                "zip_filename": zip_filename
            })
        else:
            return jsonify({"error": "Failed to create ZIP file"}), 500

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": "An error occurred while generating the website. Please try again."}), 500

# Route to serve generated files
@app.route('/view/<folder>/<path:filename>')
def view(folder, filename):
    # Handle both index.html and home.html for the home page
    if filename == 'index.html':
        home_path = os.path.join('generated_folders', folder, 'home.html')
        if os.path.exists(home_path):
            return send_from_directory(os.path.join('generated_folders', folder), 'home.html')
    return send_from_directory(os.path.join('generated_folders', folder), filename)

# New route to download the website as ZIP
@app.route('/download/<folder>')
def download_website(folder):
    try:
        # Get the website name from the folder's index.html
        index_path = os.path.join('generated_folders', folder, 'index.html')
        website_name = "Website"  # Default name
        
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Try to find the title tag
                title_match = re.search(r'<title>(.*?)</title>', content)
                if title_match:
                    website_name = title_match.group(1).strip()
        
        # Create the ZIP file
        zip_path, zip_filename = create_website_zip(folder, website_name)
        
        if zip_path and os.path.exists(zip_path):
            return send_file(
                zip_path,
                as_attachment=True,
                download_name=zip_filename,
                mimetype='application/zip'
            )
        else:
            return jsonify({"error": "Failed to create ZIP file"}), 500
            
    except Exception as e:
        print(f"Error in download route: {str(e)}")
        return jsonify({"error": "An error occurred while preparing the download"}), 500

if __name__ == "__main__":
    # Create necessary directories if they don't exist
    os.makedirs('generated_folders', exist_ok=True)
    os.makedirs('temp_zips', exist_ok=True)
    
    print("=" * 50)
    print("🚀 Flask App Starting...")
    print("📱 Open your browser and go to: http://127.0.0.1:5000")
    print("🔗 Or click this link: http://localhost:5000")
    print("=" * 50)
    
    app.run(debug=True)