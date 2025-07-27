# Website Builder 2.0 - Workflow & Model Usage

## Overview
Website Builder 2.0 is an automated web application that generates complete, modern, multi-page websites based on user prompts. It leverages advanced AI models to generate page names, HTML, CSS, and JavaScript for each page, and assembles them into a cohesive, navigable website.

---

## Workflow Steps

### 1. User Prompt Submission
- **User Action:** The user submits a website requirement or description via the frontend.
- **Backend:** The `/generate` endpoint in `full_folder_test.py` receives the prompt.

### 2. Page Name Generation (AI Model)
- **Model Used:** `claude-3.5-sonnet` (via g4f client)
- **Prompt:** Strict instructions to generate only English, capitalized, comma-separated page names (e.g., "Home, About, Services, Contact").
- **Validation:** Ensures no Chinese characters, only ASCII, and "Home" is always first.
- **Result:** A list of standard website page names.

### 3. Folder Creation
- **Backend:** Generates a random folder name and creates a directory under `generated_folders/` to store the website files.

### 4. Page Generation (AI Model)
- **Model Used:** `claude-3.5-sonnet`
- **Prompt:** For each page, a detailed prompt is constructed (using `base_prompt`) describing design, branding, and technical requirements.
- **Parallelization:** Each page is generated in a separate thread for efficiency.
- **Result:** The model returns HTML, CSS, and JS code blocks for each page.

### 5. File Creation
- **Backend:** Extracts code sections and writes them to appropriately named files (e.g., `about.html`, `about.css`, `about.js`).
- **Enhancements:**
  - Adds Tailwind CSS CDN if missing.
  - Links CSS and JS files in HTML.
  - Ensures each page has a consistent structure.

### 6. Navbar Generation & Insertion (AI Model)
- **Model Used:** `claude-3.5-sonnet`
- **Prompt:** Generates a modern, responsive navbar HTML and CSS based on the list of pages.
- **Backend:**
  - Inserts the navbar into each HTML file after the `<body>` tag.
  - Writes `navbar.css` and links it in each HTML file.
  - Updates navbar links to point to the correct local files.

### 7. Logging & Progress Tracking
- **Backend:**
  - Logs key events and errors to `logs.txt` and `app.log`.
  - Provides a `/progress` endpoint for real-time progress updates.

### 8. Website Delivery
- **Backend:**
  - Returns the folder name and list of generated pages to the frontend.
  - Serves generated files via `/view/<folder>/<filename>` endpoint.

---

## Model Usage Summary
- **claude-3.5-sonnet** is used for:
  - Generating the list of page names.
  - Generating the HTML, CSS, and JS for each page.
  - Generating custom CSS for the navbar.
- **g4f client** is the interface for calling the model.

---

## File Structure Example
```
website-builder-2.0/
  generated_folders/
    <random_folder>/
      index.html
      about.html
      services.html
      contact.html
      home.css
      about.css
      ...
      navbar.css
      home.js
      ...
```

---

## Notes
- All AI-generated content is strictly in English and follows modern web design best practices.
- The system is designed for extensibility and can be adapted to use other models or prompts as needed. 