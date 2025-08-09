const generateBtn = document.getElementById('generate-btn');
const saveBtn = document.getElementById('save-btn');
const promptInput = document.getElementById('prompt');
const htmlCodeOutput = document.getElementById('html-code');
const cssCodeOutput = document.getElementById('css-code');
const jsCodeOutput = document.getElementById('js-code');
const viewPageBtn = document.createElement('button');
viewPageBtn.textContent = 'View Page';
viewPageBtn.style.display = 'none';
viewPageBtn.className = 'btn-hover-effect';
document.body.appendChild(viewPageBtn);

let currentFolderName = '';

const progressContainer = document.querySelector('.progress-container');
const progressBar = document.querySelector('.progress');
const progressText = document.getElementById('progress-text');

// Add loading spinner to buttons
function addLoadingSpinner(button, text) {
    const originalText = button.innerHTML;
    button.innerHTML = `<span class="loading-spinner"></span> ${text}`;
    button.disabled = true;
    return () => {
        button.innerHTML = originalText;
        button.disabled = false;
    };
}

// Add success animation
function addSuccessAnimation(element) {
    element.classList.add('success-animation');
    setTimeout(() => {
        element.classList.remove('success-animation');
    }, 500);
}

// Add error animation
function addErrorAnimation(element) {
    element.classList.add('error-animation');
    setTimeout(() => {
        element.classList.remove('error-animation');
    }, 500);
}

// Enhanced button click effects
function addButtonEffects(button) {
    button.addEventListener('mousedown', function() {
        this.style.transform = 'scale(0.95)';
    });
    
    button.addEventListener('mouseup', function() {
        this.style.transform = 'scale(1)';
    });
    
    button.addEventListener('mouseleave', function() {
        this.style.transform = 'scale(1)';
    });
}

// Add effects to all buttons
addButtonEffects(generateBtn);
addButtonEffects(saveBtn);
addButtonEffects(viewPageBtn);

// Enhanced textarea interactions
promptInput.addEventListener('focus', function() {
    this.style.transform = 'scale(1.02)';
    this.style.boxShadow = '0 0 20px rgba(79, 172, 254, 0.3)';
});

promptInput.addEventListener('blur', function() {
    this.style.transform = 'scale(1)';
    this.style.boxShadow = 'none';
});

promptInput.addEventListener('input', function() {
    // Add character counter
    const charCount = this.value.length;
    if (charCount > 0) {
        this.style.borderColor = 'rgba(79, 172, 254, 0.5)';
    } else {
        this.style.borderColor = 'rgba(255, 255, 255, 0.1)';
    }
});

generateBtn.addEventListener('click', async () => {
  const prompt = promptInput.value.trim();
  if (!prompt) {
    addErrorAnimation(generateBtn);
    alert('Please enter a prompt.');
    return;
  }

  try {
    // Add loading state with spinner
    const stopLoading = addLoadingSpinner(generateBtn, 'Generating...');
    
    progressContainer.style.display = 'block';
    progressBar.style.width = '0%';
    progressText.textContent = '0%';

    const response = await fetch('http://127.0.0.1:5000/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ prompt })
    });

    const eventSource = new EventSource('http://127.0.0.1:5000/progress');
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const progress = data.progress;
      progressBar.style.width = `${progress}%`;
      progressText.textContent = `${progress}%`;
      
      if (progress === 100) {
        eventSource.close();
        setTimeout(() => {
          progressContainer.style.display = 'none';
        }, 1000);
      }
    };

    const data = await response.json();
    
    if (response.ok) {
      htmlCodeOutput.textContent = data.html;
      cssCodeOutput.textContent = data.css;
      jsCodeOutput.textContent = data.js;
      
      // Add success animation
      addSuccessAnimation(generateBtn);
      addSuccessAnimation(document.getElementById('code-container'));
      
      // Smooth scroll to results
      document.getElementById('code-container').scrollIntoView({ 
        behavior: 'smooth',
        block: 'center'
      });
    } else {
      addErrorAnimation(generateBtn);
      alert('An error occurred while generating the code.');
    }
  } catch (error) {
    console.error('Error:', error);
    addErrorAnimation(generateBtn);
    alert('An error occurred while generating the code.');
    progressContainer.style.display = 'none';
  } finally {
    // Stop loading spinner
    const stopLoading = addLoadingSpinner(generateBtn, 'Generate');
    stopLoading();
  }
});

saveBtn.addEventListener('click', () => {
  if (!htmlCodeOutput.textContent && !cssCodeOutput.textContent && !jsCodeOutput.textContent) {
    addErrorAnimation(saveBtn);
    alert('No code generated yet. Please generate code first.');
    return;
  }
  
  currentFolderName = generateRandomFolderName();
  saveCodeToLocalStorage(currentFolderName);
  viewPageBtn.style.display = 'block';
  
  // Add success animation
  addSuccessAnimation(saveBtn);
  
  // Show success message with animation
  const successMessage = document.createElement('div');
  successMessage.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    padding: 15px 20px;
    border-radius: 10px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
    z-index: 1000;
    transform: translateX(100%);
    transition: transform 0.3s ease;
  `;
  successMessage.textContent = `Files saved in folder: ${currentFolderName}`;
  document.body.appendChild(successMessage);
  
  // Animate in
  setTimeout(() => {
    successMessage.style.transform = 'translateX(0)';
  }, 100);
  
  // Remove after 3 seconds
  setTimeout(() => {
    successMessage.style.transform = 'translateX(100%)';
    setTimeout(() => {
      document.body.removeChild(successMessage);
    }, 300);
  }, 3000);
});

viewPageBtn.addEventListener('click', () => {
  if (currentFolderName) {
    const win = window.open('', '_blank');
    const storedData = JSON.parse(localStorage.getItem(currentFolderName));
    
    if (storedData) {
      win.document.write(`
        <html>
          <head>
            <style>${storedData.css}</style>
          </head>
          <body>
            ${storedData.html}
            <script>${storedData.js}</script>
          </body>
        </html>
      `);
      
      // Add success animation
      addSuccessAnimation(viewPageBtn);
    } else {
      addErrorAnimation(viewPageBtn);
      alert('No saved data found. Please save the code first.');
    }
  } else {
    addErrorAnimation(viewPageBtn);
    alert('No page generated yet. Please generate and save a page first.');
  }
});

function generateRandomFolderName(length = 8) {
  const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += characters.charAt(Math.floor(Math.random() * characters.length));
  }
  return 'generated_folders/' + result;
}

function saveCodeToLocalStorage(folderName) {
  const htmlContent = htmlCodeOutput.textContent;
  const cssContent = cssCodeOutput.textContent;
  const jsContent = jsCodeOutput.textContent;

  const folderContent = {
    html: htmlContent,
    css: cssContent,
    js: jsContent
  };

  localStorage.setItem(folderName, JSON.stringify(folderContent));
}

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
  // Ctrl+Enter to generate
  if (e.ctrlKey && e.key === 'Enter') {
    e.preventDefault();
    generateBtn.click();
  }
  
  // Ctrl+S to save
  if (e.ctrlKey && e.key === 's') {
    e.preventDefault();
    saveBtn.click();
  }
});

// Add auto-save functionality
let autoSaveTimeout;
promptInput.addEventListener('input', function() {
  clearTimeout(autoSaveTimeout);
  autoSaveTimeout = setTimeout(() => {
    if (htmlCodeOutput.textContent || cssCodeOutput.textContent || jsCodeOutput.textContent) {
      saveCodeToLocalStorage('auto-save');
    }
  }, 5000); // Auto-save after 5 seconds of inactivity
});

// Add code highlighting
function highlightCode() {
  const codeBlocks = document.querySelectorAll('pre');
  codeBlocks.forEach(block => {
    block.addEventListener('click', function() {
      const range = document.createRange();
      range.selectNodeContents(this);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      
      // Show copy feedback
      const originalText = this.textContent;
      this.textContent = 'Copied!';
      this.style.background = 'rgba(16, 185, 129, 0.3)';
      
      setTimeout(() => {
        this.textContent = originalText;
        this.style.background = 'rgba(0, 0, 0, 0.3)';
      }, 1000);
    });
  });
}

// Initialize code highlighting
document.addEventListener('DOMContentLoaded', function() {
  highlightCode();
});

// Add smooth scrolling for better UX
function smoothScrollTo(element) {
  element.scrollIntoView({
    behavior: 'smooth',
    block: 'center'
  });
}

// Add tooltip functionality
function addTooltips() {
  const buttons = document.querySelectorAll('button');
  buttons.forEach(button => {
    const tooltip = document.createElement('div');
    tooltip.style.cssText = `
      position: absolute;
      background: rgba(0, 0, 0, 0.8);
      color: white;
      padding: 5px 10px;
      border-radius: 5px;
      font-size: 12px;
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.3s;
      z-index: 1000;
    `;
    
    if (button.id === 'generate-btn') {
      tooltip.textContent = 'Generate code from prompt (Ctrl+Enter)';
    } else if (button.id === 'save-btn') {
      tooltip.textContent = 'Save code to folder (Ctrl+S)';
    }
    
    button.style.position = 'relative';
    button.appendChild(tooltip);
    
    button.addEventListener('mouseenter', () => {
      tooltip.style.opacity = '1';
    });
    
    button.addEventListener('mouseleave', () => {
      tooltip.style.opacity = '0';
    });
  });
}

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
  addTooltips();
});