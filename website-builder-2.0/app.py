import logging
from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
import os
import random
import string
import re
from g4f.client import Client
import threading
import queue
import shutil
import zipfile
from datetime import datetime, timedelta
import asyncio
import platform
import time

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
            html_content = '<html lang="en">\n' + html_content
        
        if not re.search(r'<head[^>]*>', html_content, re.IGNORECASE):
            html_content = html_content.replace('<html', '<html>\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>' + page_name + '</title>\n</head>', 1)
        
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

    print(f'Page {page_name} generated successfully.')

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
            page_prompt += "\nFocus on creating an engaging landing page with clear navigation to other sections."
        elif page.lower() == 'about':
            page_prompt += "\nFocus on telling the story and building trust with visitors."
        elif page.lower() == 'services' or page.lower() == 'products':
            page_prompt += "\nFocus on showcasing the services/products with clear benefits and features."
        elif page.lower() == 'contact':
            page_prompt += "\nFocus on making it easy for visitors to get in touch."
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response_content = regenerate_code(page_prompt)
                code_sections = extract_code_sections(response_content)

                if not is_complete_html(code_sections["html"]) or not contains_div_tags(code_sections["html"]):
                    print(f"Incomplete HTML or missing <div> tags detected for {page}. Retry {retry_count + 1}/{max_retries}")
                    retry_count += 1
                    continue

                # Validate page-specific content
                if page.lower() == 'home' and not re.search(r'hero|banner|main-content', code_sections["html"], re.IGNORECASE):
                    print(f"Home page missing hero section. Retry {retry_count + 1}/{max_retries}")
                    retry_count += 1
                    continue
                elif page.lower() == 'about' and not re.search(r'about|mission|team|history', code_sections["html"], re.IGNORECASE):
                    print(f"About page missing relevant content. Retry {retry_count + 1}/{max_retries}")
                    retry_count += 1
                    continue
                elif page.lower() == 'contact' and not re.search(r'contact|form|email|phone', code_sections["html"], re.IGNORECASE):
                    print(f"Contact page missing contact information. Retry {retry_count + 1}/{max_retries}")
                    retry_count += 1
                    continue
                elif page.lower() in ['services', 'products'] and not re.search(r'service|product|feature|pricing', code_sections["html"], re.IGNORECASE):
                    print(f"{page} page missing service/product information. Retry {retry_count + 1}/{max_retries}")
                    retry_count += 1
                    continue

                # If we get here, the page generation was successful
                create_files(code_sections, folder_name, page)
                result_queue.put(page)
                return

            except Exception as e:
                print(f"Error generating {page} page: {str(e)}. Retry {retry_count + 1}/{max_retries}")
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"Failed to generate {page} page after {max_retries} attempts")
                    result_queue.put(None)  # Signal failure
                    return

    except Exception as e:
        print(f"Critical error in generate_page for {page}: {str(e)}")
        result_queue.put(None)  # Signal failure
        return

# New function to generate custom navbar
def generate_custom_navbar(pages):
    client = Client()
    
    navbar_prompt = f"""Create a simple, responsive navbar using Tailwind CSS for these pages: {', '.join(pages)}.
    Requirements:
    1. Use simple <nav> with <ul> and <li> elements
    2. Each link should point to the exact .html file (e.g., home.html, about.html)
    3. Include a mobile hamburger menu for small screens
    4. Use basic Tailwind classes for styling
    5. Keep the design clean and minimal
    6. Ensure all links work correctly with proper href attributes
    {avoid}"""

    while True:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": navbar_prompt}]
        )

        response_content = response.choices[0].message.content

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

    return ""  # Return an empty string if no navbar is generated after multiple attempts

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
    client = Client()
    
    name_prompt = f"""Based on this website description: "{prompt}", generate a professional, memorable website name.
    Requirements:
    1. The name should be 2-3 words maximum
    2. It should be relevant to the website's purpose
    3. It should be easy to remember and type
    4. It should be professional and brandable
    5. Avoid generic names
    6. Do not include any special characters
    7. Keep it in English only
    
    Format your response exactly like this:
    Website Name: [name]"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": name_prompt}]
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Extract the website name
        if "Website Name:" in response_text:
            name = response_text.split("Website Name:", 1)[1].strip()
            return name
        else:
            # Fallback to a generated name if the format is wrong
            words = prompt.split()
            if len(words) >= 2:
                return f"{words[0].capitalize()}{words[1].capitalize()}"
            return f"{prompt.split()[0].capitalize()}Site"
            
    except Exception as e:
        print(f"Error generating website name: {str(e)}")
        # Fallback to a simple name if there's an error
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
        global code_generation_failures
        original_prompt = request.json.get('prompt')
        
        if not original_prompt:
            return jsonify({"error": "No prompt provided"}), 400
        
        # Generate website name based on the prompt
        website_name = generate_website_name(original_prompt)
        
        client = Client()
        
        # Get the list of pages with a more structured prompt
        pages_prompt = f"""For a website about {original_prompt}, list exactly 3-5 essential pages.
        Format your response exactly like this:
        the minimum required pages are: Home, About, Services, Contact
        
        Only use these standard page names: Home, About, Services, Products, Contact, Blog, Portfolio
        Always start with Home page.
        Keep the response simple and exactly in the format shown above."""
        
        try:
            pages_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": pages_prompt}]
            )
            
            response_text = pages_response.choices[0].message.content.strip()
            
            # Extract pages with better error handling
            if "the minimum required pages are:" not in response_text.lower():
                # If the format is wrong, use default pages
                pages = ['Home', 'About', 'Contact']
            else:
                try:
                    # Split on the colon and get the second part
                    pages_text = response_text.split(':', 1)[1].strip()
                    # Split on commas and clean up each page name
                    pages = [page.strip() for page in pages_text.split(',') if page.strip()]
                    
                    # Validate page names
                    valid_pages = ['Home', 'About', 'Services', 'Products', 'Contact', 'Blog', 'Portfolio']
                    pages = [page for page in pages if any(valid.lower() == page.lower() for valid in valid_pages)]
                    
                    # If no valid pages found, use defaults
                    if not pages:
                        pages = ['Home', 'About', 'Contact']
                except Exception as e:
                    print(f"Error parsing pages: {str(e)}")
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
            
            # Log the final pages list for debugging
            print(f"Final pages list: {pages}")
            
        except Exception as e:
            print(f"Error getting pages from API: {str(e)}")
            # Use default pages if there's an error
            pages = ['Home', 'About', 'Contact']
        
        folder_name = generate_random_folder_name()
        
        # Define base prompt here to ensure it's available
        base_prompt = '''Generate a unique, production-ready web page for the {page_name} page of a website about {original_prompt}. The content and design should be specifically tailored for a {page_name} page, following these guidelines:

For Home page:
- Create an engaging hero section with a clear value proposition
- Include a brief overview of the main services/products
- Add featured content or highlights
- Include a call-to-action section

For About page:
- Include company/organization history and mission
- Add team member information or founder story
- Include values and achievements
- Add relevant images and testimonials

For Services/Products page:
- List and describe each service/product in detail
- Include pricing if applicable
- Add service/product features and benefits
- Include relevant images and icons

For Contact page:
- Add a contact form
- Include business hours and location
- Add contact information (email, phone)
- Include a map or address

For any other page:
- Focus on the specific purpose of that page
- Include relevant content and features
- Maintain consistent branding

Technical Requirements:
- Use semantic HTML5 tags
- Implement responsive design with Tailwind CSS
- Include proper meta tags and SEO optimization
- Add necessary JavaScript for interactivity
- Ensure accessibility standards
- Include appropriate images and icons
- Add smooth animations and transitions

The page should be visually appealing, functional, and optimized for both desktop and mobile devices.'''
        
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
            except Exception as e:
                print(f"Error updating navbar: {str(e)}")
                # Continue even if navbar update fails
        
        # Create the ZIP file
        zip_path, zip_filename = create_website_zip(folder_name, website_name)
        
        if zip_path and os.path.exists(zip_path):
            return jsonify({
                "folder": folder_name,
                "pages": generated_pages,
                "failed_pages": failed_pages if failed_pages else None,
                "website_name": website_name,
                "download_url": f"/download/{folder_name}",  # Add download URL to the response
                "zip_path": zip_path,
                "zip_filename": zip_filename
            })
        else:
            return jsonify({"error": "Failed to create ZIP file"}), 500

    except Exception as e:
        print(f"Error in generate route: {str(e)}")
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
    app.run(debug=False)