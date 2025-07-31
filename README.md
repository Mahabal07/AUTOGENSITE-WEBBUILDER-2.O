# AutoSiteGen: AI-Powered Website Builder

## Overview
AutoSiteGen is an intelligent web application that generates complete, modern websites using AI. It leverages Google's Gemini AI to create responsive, multi-page websites with custom HTML, CSS, and JavaScript based on user descriptions. The system automatically generates professional websites with navigation, styling, and interactive features.

## Features
- **AI-Powered Generation**: Uses Google Gemini AI to create websites from text descriptions
- **Multi-Page Websites**: Automatically generates 3-5 essential pages (Home, About, Services, Contact, etc.)
- **Modern Design**: Creates responsive websites with Tailwind CSS and custom styling
- **Custom Navigation**: Generates intelligent navigation bars linking all pages
- **Download Ready**: Provides complete websites as downloadable ZIP files
- **Real-time Generation**: Multi-threaded generation for faster website creation
- **Automatic Cleanup**: Self-maintaining system that removes old files
- **Professional UI**: Beautiful, modern interface with gradient designs

## Setup

### Option 1: Local Installation
Clone the repository:
```bash
git clone https://github.com/yourusername/autositegen.git
cd autositegen
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### Option 2: Using Docker
Clone the repository:
```bash
git clone https://github.com/yourusername/autositegen.git
cd autositegen
```

Build the Docker image:
```bash
docker build -t autositegen .
```

Run the Docker container:
```bash
docker run -p 5000:5000 autositegen
```

Open your web browser and navigate to `http://localhost:5000`

**Note**: The Docker version includes all dependencies and is ready to run without additional setup.

## Usage

### Running the Application
Start the Flask application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

### How to Generate a Website
1. **Enter Description**: Describe your website in the text area
   - Example: "A modern restaurant website with online ordering"
   - Example: "An e-commerce store for handmade jewelry"
   - Example: "A portfolio website for a graphic designer"

2. **Generate**: Click the "Generate Website" button

3. **Wait for Processing**: The AI will generate multiple pages simultaneously

4. **Download**: Once complete, download your website as a ZIP file

5. **Deploy**: Extract the ZIP and upload to any web hosting service

## How it Works

### AI-Powered Generation
The application uses Google's Gemini AI model to understand your website requirements and generate appropriate content. The system:

- **Analyzes your description** to determine website type and purpose
- **Generates page structure** based on common website patterns
- **Creates custom content** for each page type (Home, About, Services, Contact)
- **Applies modern design principles** with responsive layouts

### Multi-Page Architecture
Each generated website includes:

- **Home Page**: Landing page with hero section, features, and call-to-action
- **About Page**: Company information, team, and mission statement
- **Services/Products Page**: Service offerings with pricing and features
- **Contact Page**: Contact form, business information, and Google Maps integration
- **Additional Pages**: Blog, Portfolio, or other relevant pages

### Technical Implementation
- **Flask Backend**: Python web framework for API endpoints
- **Multi-threading**: Parallel page generation for faster results
- **File Management**: Automatic organization of generated files
- **ZIP Creation**: Complete website packaging for easy deployment

## Example Results

### Generated Website Structure
```
your-website/
├── index.html          # Home page
├── about.html          # About page
├── services.html       # Services page
├── contact.html        # Contact page
├── home.css           # Home page styles
├── about.css          # About page styles
├── services.css       # Services page styles
├── contact.css        # Contact page styles
├── home.js            # Home page JavaScript
├── about.js           # About page JavaScript
├── services.js        # Services page JavaScript
├── contact.js         # Contact page JavaScript
└── global-style.css   # Global styles
```

### Sample Generated Pages

#### Home Page Example
- Hero section with animated background
- Feature cards in grid layout
- Testimonials carousel
- Statistics section
- Prominent call-to-action buttons

#### About Page Example
- Timeline layout for company history
- Team grid with circular profile images
- Mission statement in card format
- Values displayed as icons
- Statistics in counter format

#### Contact Page Example
- Contact form on left side
- Business information on right side
- Embedded Google Maps iframe
- Social media icons
- Business hours in card format

## Application UI

### Modern Interface
The application features a beautiful, modern UI with:

- **Gradient Backgrounds**: Eye-catching visual design
- **Glass Morphism**: Modern glass-like card effects
- **Responsive Design**: Works on all device sizes
- **Smooth Animations**: Hover effects and transitions
- **Real-time Feedback**: Loading states and progress indicators

### Input Methods:
- **Text Description**: Describe your website in natural language
- **AI Analysis**: The system understands context and requirements
- **Smart Suggestions**: Automatic page selection based on website type

### Generation Process:
- **Multi-threaded**: Generates all pages simultaneously
- **Progress Tracking**: Real-time updates on generation status
- **Error Handling**: Graceful handling of generation failures
- **Quality Validation**: Ensures generated code meets standards

### Results:
- **Complete Website**: All files included in ZIP download
- **Production Ready**: Code is optimized and ready for deployment
- **Cross-browser Compatible**: Works on all modern browsers
- **Mobile Responsive**: Automatically adapts to different screen sizes

## Example Workflow

1. **Start the Application**
   ```bash
   python app.py
   ```

2. **Access the Interface**
   - Open browser to `http://localhost:5000`
   - See the modern gradient interface

3. **Describe Your Website**
   - Enter: "A modern coffee shop website with online ordering"
   - The AI analyzes your requirements

4. **Generate Website**
   - Click "Generate Website"
   - Watch real-time progress updates
   - See pages being generated simultaneously

5. **Download and Deploy**
   - Download the ZIP file
   - Extract to your web server
   - Your website is live!

## Technical Architecture

### Backend Components
- **Flask Application**: Main web server
- **Google Gemini AI**: Content generation engine
- **Multi-threading**: Parallel page generation
- **File Management**: Automatic organization and cleanup
- **ZIP Creation**: Website packaging system

### Frontend Components
- **HTML Templates**: Modern, responsive interface
- **Tailwind CSS**: Utility-first styling
- **JavaScript**: Interactive features and animations
- **AJAX**: Real-time communication with backend

### AI Integration
- **Prompt Engineering**: Optimized prompts for better results
- **Content Validation**: Ensures generated code quality
- **Error Recovery**: Automatic retry mechanisms
- **Fallback Systems**: Alternative AI models when needed

## Model Performance

The application uses Google's Gemini AI model with the following capabilities:

| Feature | Description |
|---------|-------------|
| **Content Generation** | Creates unique, relevant content for each page |
| **Code Quality** | Generates production-ready HTML, CSS, and JavaScript |
| **Design Consistency** | Maintains visual consistency across all pages |
| **Responsive Design** | Automatically creates mobile-friendly layouts |
| **SEO Optimization** | Includes proper meta tags and semantic HTML |

### Generation Metrics
- **Average Generation Time**: 30-60 seconds for complete website
- **Success Rate**: 95%+ successful generation rate
- **Code Quality**: Production-ready, validated code
- **File Size**: Optimized for fast loading

## Dataset and Training

This project uses Google's Gemini AI model, which has been trained on:
- **Web Development Patterns**: Modern website structures and layouts
- **Design Principles**: Current web design trends and best practices
- **Code Standards**: HTML5, CSS3, and JavaScript best practices
- **Content Generation**: Natural language processing for relevant content

## Contact

For questions or support, contact the development team.

## Contributing

Contributions are welcome! If you would like to improve this project, please follow these steps:

1. **Fork the repository** and create your branch from main
2. **Make your changes** with clear, descriptive commit messages
3. **Test your changes** to ensure they work as expected
4. **Submit a pull request** with a detailed description of your changes

### Guidelines
- Follow PEP8 style for Python code
- Add docstrings and comments for new functions or modules
- If adding new features, update the documentation and README accordingly
- For bug fixes, describe the issue and how your fix resolves it
- Test thoroughly before submitting changes

## Docker Development

To modify the Docker setup:

1. **Edit the Dockerfile** to update build steps or dependencies
2. **Rebuild the image** after changes:
   ```bash
   docker build -t autositegen .
   ```
3. **Run with volume mount** for development:
   ```bash
   docker run -p 5000:5000 -v $(pwd):/app autositegen
   ```

## Deployment

### Local Development
```bash
python app.py
```

### Production Deployment
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Environment Variables
- `FLASK_ENV`: Set to 'production' for production deployment
- `GEMINI_API_KEY`: Your Google Gemini API key (optional, uses default)

## Acknowledgments

- **Google Gemini AI**: For providing the AI generation capabilities
- **Tailwind CSS**: For the utility-first CSS framework
- **Flask**: For the Python web framework
- **Open Source Community**: For various supporting libraries and tools 
