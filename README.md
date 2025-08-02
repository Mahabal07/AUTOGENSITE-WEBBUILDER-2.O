# AutoSiteGen (AI-Powered Website Generator)

A Website Generator that automatically creates multi-page, production-ready, responsive web pages based on user prompts.

## 🚀 Core Features
- **Multi-page Generation**: Creates 3-5 essential pages (Home, About, Services, Contact, etc.)
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Custom Components**: Unique design for each page type
- **SEO Optimization**: Semantic HTML5 structure
- **Error Handling**: Robust retry mechanisms and fallback systems
- **Parallel Processing**: Threading for simultaneous page generation
- **ZIP Download**: Complete website packages for easy deployment

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask 3.0.3
- **AI Engine**: Google Gemini AI (gemini-1.5-flash)
- **Threading**: Parallel page generation
- **File Management**: ZIP creation, cleanup automation
- **Error Handling**: Comprehensive retry mechanisms

### Frontend
- **HTML5**: Semantic structure with ARIA accessibility
- **Tailwind CSS**: Utility-first CSS framework via CDN
- **JavaScript (ES6+)**: Modern interactivity and animations
- **Responsive Design**: Mobile-first approach

### Dependencies
- **Core**: Flask, google-generativeai, requests
- **File Handling**: zipfile, shutil, os
- **Threading**: threading, queue
- **Time Management**: datetime, time
- **Platform Support**: platform, asyncio

## 🔄 Complete Workflow

### 1. User Input Processing
```
User enters prompt → Frontend validation → POST to /generate endpoint
```

### 2. Website Planning
- **Website Name Generation**: AI creates contextual website name
- **Page Selection**: AI determines 3-5 essential pages based on prompt
- **Folder Creation**: Random 8-character folder name generation

### 3. Parallel Page Generation
```
For each page (Home, About, Services, Contact):
├── Create page-specific prompt
├── Generate content with AI (max 3 retries)
├── Extract HTML, CSS, JavaScript code blocks
├── Validate page-specific content requirements
├── Create individual files (.html, .css, .js)
└── Add to result queue
```

### 4. Navigation Integration
- **Custom Navbar Generation**: AI creates responsive navigation
- **Link Updates**: Automatic href attribute correction
- **Mobile Menu**: Hamburger menu for small screens

### 5. File Organization
```
generated_folders/
└── [random_folder]/
    ├── index.html (Home page)
    ├── about.html
    ├── services.html
    ├── contact.html
    ├── home.css, about.css, services.css, contact.css
    └── home.js, about.js, services.js, contact.js
```

### 6. ZIP Creation & Download
- **ZIP Generation**: Complete website package
- **File Naming**: Website name + timestamp
- **Download Route**: `/download/<folder>` endpoint

### 7. Cleanup Automation
- **Background Thread**: Runs every hour
- **Age Limit**: 24-hour folder retention
- **Storage Management**: Automatic old folder removal

## 📋 Properties & Configuration

### AI Configuration
```python
# Gemini AI Setup
genai.configure(api_key="AIzaSyDH8326_llp1bhBIw1biLA1GDU4rs6TO6o")
model = genai.GenerativeModel('gemini-1.5-flash')

# Generation Config
generation_config = {
    "max_output_tokens": 4000,
    "temperature": 0.7
}
```

### Page Generation Properties
- **Max Retries**: 3 attempts per page
- **Content Validation**: Page-specific keyword checking
- **File Structure**: Separate HTML, CSS, JS files per page
- **Responsive Design**: Mobile-first approach

### Page-Specific Requirements

#### Home Page
- Hero section with animated background
- Feature cards in grid layout
- Testimonials carousel
- Statistics section
- Prominent call-to-action
- Vibrant colors and modern animations

#### About Page
- Timeline layout for company history
- Team grid with circular profile images
- Mission statement in card format
- Values displayed as icons
- Statistics in counter format
- Professional blue/gray color scheme

#### Services Page
- Service cards in masonry layout
- Pricing tables with hover effects
- Feature comparison in table format
- Testimonials in slider
- FAQ accordion
- Gradient backgrounds and modern card designs

#### Contact Page
- Contact form on left
- Business info on right
- Embedded Google Maps iframe (MANDATORY)
- Social media icons
- Business hours in card format
- Minimal design with focus on functionality

### File Management Properties
```python
# Cleanup Configuration
CLEANUP_INTERVAL = 3600  # 1 hour
FOLDER_MAX_AGE = 24      # 24 hours

# Directory Structure
generated_folders/    # Main output directory
temp_zips/           # Temporary ZIP storage
templates/           # Flask templates
frontend/            # Static frontend files
```

### Frontend Properties
- **Progress Tracking**: Real-time generation progress
- **Error Handling**: User-friendly error messages
- **File Download**: ZIP package download
- **Preview System**: Live page preview functionality

### API Endpoints
```
GET  /                    # Main application page
POST /generate           # Website generation endpoint
GET  /view/<folder>/<file>  # View generated files
GET  /download/<folder>     # Download ZIP package
```

### Error Handling Properties
- **AI Fallback**: Hugging Face API as backup
- **Retry Logic**: 3 attempts per page generation
- **Content Validation**: Page-specific content verification
- **Graceful Degradation**: Continue with partial success

### Security Properties
- **Input Validation**: Prompt sanitization
- **File Path Security**: Safe file operations
- **Error Logging**: Comprehensive error tracking
- **Resource Management**: Automatic cleanup

## 🎯 Key Features

### Multi-Page Generation
- **Dynamic Page Selection**: AI determines relevant pages
- **Parallel Processing**: Simultaneous page generation
- **Consistent Branding**: Unified design across pages
- **Navigation Integration**: Automatic navbar generation

### Responsive Design
- **Mobile-First**: Tailwind CSS utility classes
- **Breakpoint Support**: sm, md, lg, xl responsive design
- **Touch-Friendly**: Mobile-optimized interactions
- **Cross-Browser**: Modern browser compatibility

### SEO & Accessibility
- **Semantic HTML**: Proper heading hierarchy
- **ARIA Labels**: Screen reader support
- **Meta Tags**: SEO-optimized meta information
- **Alt Text**: Image accessibility

### Performance Optimization
- **CDN Integration**: Tailwind CSS via CDN
- **Minified Code**: Production-ready output
- **Lazy Loading**: Optimized resource loading
- **Caching**: Browser cache optimization

## 🔧 Development & Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py

# Access application
http://localhost:5000
```

### Production Deployment
- **WSGI Server**: Gunicorn configuration
- **Environment Variables**: Secure API key management
- **Static File Serving**: Optimized file delivery
- **Error Monitoring**: Production error tracking

### File Structure
```
webbuilder-new--ver/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── frontend/             # Static frontend files
│   ├── index.html
│   ├── script.js
│   └── style.css
├── templates/            # Flask templates
├── generated_folders/    # Generated websites
├── temp_zips/           # Temporary ZIP files
└── details.md           # This documentation
```

## 📊 Performance Metrics

### Generation Speed
- **Single Page**: ~10-15 seconds
- **Multi-Page**: ~30-45 seconds (parallel processing)
- **ZIP Creation**: ~2-3 seconds
- **Total Process**: ~35-50 seconds for complete website

### Resource Usage
- **Memory**: ~50-100MB per generation
- **Storage**: ~1-5MB per website
- **CPU**: Multi-threaded processing
- **Network**: AI API calls optimization

### Scalability
- **Concurrent Users**: Thread-safe operations
- **File Management**: Automatic cleanup
- **Storage Optimization**: 24-hour retention policy
- **Error Recovery**: Robust retry mechanisms

## 🚀 Future Enhancements

### Planned Features
- **Custom Domain Support**: Direct domain integration
- **Template System**: Pre-built design templates
- **E-commerce Integration**: Shopping cart functionality
- **CMS Integration**: Content management system
- **Analytics Dashboard**: Website performance tracking
- **Multi-language Support**: Internationalization
- **Advanced SEO**: Schema markup and structured data
- **Performance Monitoring**: Real-time website metrics

### Technical Improvements
- **Caching System**: Redis integration for faster generation
- **CDN Integration**: Global content delivery
- **Database Support**: PostgreSQL for user management
- **API Rate Limiting**: Fair usage policies
- **Advanced AI Models**: GPT-4 and Claude integration
- **Real-time Collaboration**: Multi-user editing
- **Version Control**: Git integration for websites
- **Automated Testing**: Comprehensive test suite 
