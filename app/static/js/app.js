// Continue from previous implementation

// Upload form initialization
function initUploadForm() {
    const uploadForm = document.getElementById('uploadForm');
    const uploadButton = document.getElementById('uploadButton');
    const fileInput = document.getElementById('fileInput');
    const uploadProgress = document.querySelector('.upload-progress');
    
    if (!uploadForm || !uploadButton) {
        console.error('Upload form elements not found');
        return;
    }
    
    console.log('Upload form initialized');
    
    uploadButton.addEventListener('click', function() {
        console.log('Upload button clicked');
        
        if (!fileInput || !fileInput.files.length) {
            alert('Please select a file to upload');
            return;
        }
        
        const file = fileInput.files[0];
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            alert('Please select a PDF file');
            return;
        }
        
        console.log('File selected:', file.name);
        
        // Show progress indicator
        if (uploadProgress) {
            uploadProgress.classList.remove('d-none');
        }
        uploadButton.disabled = true;
        
        // Create FormData and submit
        const formData = new FormData(uploadForm);
        
        // Log form data for debugging (remove in production)
        console.log('Uploading file...', formData.get('file').name);
        
        fetch(uploadForm.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            console.log('Response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Upload response:', data);
            
            // Hide progress indicator
            if (uploadProgress) {
                uploadProgress.classList.add('d-none');
            }
            uploadButton.disabled = false;
            
            if (data.error) {
                alert(data.error);
                return;
            }
            
            // Close modal
            try {
                const uploadModal = bootstrap.Modal.getInstance(document.getElementById('uploadModal'));
                if (uploadModal) {
                    uploadModal.hide();
                }
            } catch (e) {
                console.error('Modal error:', e);
            }
            
            // Add new document to selector and select it
            const documentSelector = document.getElementById('documentSelector');
            const option = document.createElement('option');
            option.value = data.filename;
            option.textContent = data.filename;
            option.selected = true;
            
            // Check if option already exists
            let optionExists = false;
            for (let i = 0; i < documentSelector.options.length; i++) {
                if (documentSelector.options[i].value === data.filename) {
                    documentSelector.options[i].selected = true;
                    optionExists = true;
                    break;
                }
            }
            
            if (!optionExists) {
                documentSelector.appendChild(option);
            }
            
            // Update PDF viewer
            const pdfViewerContainer = document.getElementById('pdfViewerContainer');
            pdfViewerContainer.innerHTML = `
                <div id="pdfViewer" data-pdf-url="/pdf/${encodeURIComponent(data.filename)}"></div>
            `;
            
            // Initialize PDF viewer with new document
            initPDFViewer();
            
            // Show success message
            showNotification(data.message || 'Document uploaded successfully', 'success');
        })
        .catch(error => {
            console.error('Upload error:', error);
            if (uploadProgress) {
                uploadProgress.classList.add('d-none');
            }
            uploadButton.disabled = false;
            alert('Error uploading document. Please try again.');
        });
    });
}

// Show notifications
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Add close handler
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', function() {
        document.body.removeChild(notification);
    });
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            document.body.removeChild(notification);
        }
    }, 5000);
    
    // Animate in
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
}

// Handle document selection from document list modal
function initDocumentListModal() {
    const documentBtns = document.querySelectorAll('.document-select-btn');
    
    documentBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const filename = this.dataset.filename;
            if (!filename) return;
            
            // Select document in dropdown
            const documentSelector = document.getElementById('documentSelector');
            for (let i = 0; i < documentSelector.options.length; i++) {
                if (documentSelector.options[i].value === filename) {
                    documentSelector.options[i].selected = true;
                    break;
                }
            }
            
            // Update active document on server
            fetch('/set_active_document', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: new URLSearchParams({
                    'filename': filename
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update PDF viewer
                    const pdfViewerContainer = document.getElementById('pdfViewerContainer');
                    pdfViewerContainer.innerHTML = `
                        <div id="pdfViewer" data-pdf-url="/pdf/${encodeURIComponent(filename)}"></div>
                    `;
                    
                    // Initialize PDF viewer with new document
                    initPDFViewer();
                    
                    // Close modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('documentListModal'));
                    if (modal) modal.hide();
                }
            })
            .catch(error => {
                console.error('Error setting active document:', error);
            });
        });
    });
}

// Utility function to escape HTML in user input
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Add typing animation for chat
function addTypingAnimation() {
    // Add CSS for typing animation
    const style = document.createElement('style');
    style.textContent = `
        .typing-indicator {
            display: flex;
            align-items: center;
        }
        
        .typing-dots {
            display: flex;
            align-items: center;
            height: 20px;
        }
        
        .typing-dots span {
            display: block;
            width: 8px;
            height: 8px;
            background-color: #a0a0a0;
            border-radius: 50%;
            margin: 0 2px;
            animation: dot-flashing 1s infinite alternate;
        }
        
        .typing-dots span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-dots span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes dot-flashing {
            0% { opacity: 0.3; transform: scale(0.8); }
            100% { opacity: 1; transform: scale(1); }
        }
    `;
    document.head.appendChild(style);
}

// Highlight text in PDF when referenced in chat
function highlightPdfText(text) {
    // This would be a more advanced feature using PDF.js text layer
    // For simplicity, we'll implement a basic version that finds
    // and scrolls to page references in the chat
    
    // Check if text contains page references like "page 5" or "p.5"
    const pageRegex = /page\s+(\d+)|p\.(\d+)/i;
    const match = text.match(pageRegex);
    
    if (match) {
        const pageNum = parseInt(match[1] || match[2]);
        if (pageNum) {
            // Find the page in the PDF viewer and scroll to it
            const pageContainer = document.querySelector(`[data-page-number="${pageNum}"]`);
            if (pageContainer) {
                pageContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
                
                // Briefly highlight the page
                pageContainer.classList.add('highlight-page');
                setTimeout(() => {
                    pageContainer.classList.remove('highlight-page');
                }, 2000);
            }
        }
    }
}

// Initialize document selector with additional events
function initDocumentSelector() {
    const documentSelector = document.getElementById('documentSelector');
    if (!documentSelector) return;
    
    documentSelector.addEventListener('change', function() {
        const selectedDocument = this.value;
        if (!selectedDocument) return;
        
        // Update active document on server
        fetch('/set_active_document', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: new URLSearchParams({
                'filename': selectedDocument
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update PDF viewer
                const pdfViewerContainer = document.getElementById('pdfViewerContainer');
                pdfViewerContainer.innerHTML = `
                    <div id="pdfViewer" data-pdf-url="/pdf/${encodeURIComponent(selectedDocument)}"></div>
                `;
                
                // Initialize PDF viewer with new document
                initPDFViewer();
                
                // Update interface to show we're working with a new document
                const chatHeader = document.querySelector('.chat-header h4');
                if (chatHeader) {
                    chatHeader.innerHTML = `
                        <i class="fas fa-comments me-2"></i>
                        Chat with ${selectedDocument}
                    `;
                }
                
                // Add a system message about switching documents
                const chatMessages = document.getElementById('chatMessages');
                if (chatMessages) {
                    // Remove welcome message if present
                    const welcomeMsg = chatMessages.querySelector('.chat-welcome');
                    if (welcomeMsg) {
                        chatMessages.removeChild(welcomeMsg);
                    }
                    
                    // Add system message
                    const systemMessage = document.createElement('div');
                    systemMessage.className = 'chat-message system-message';
                    systemMessage.innerHTML = `
                        <div class="message-content">
                            <i class="fas fa-info-circle me-2"></i>
                            Now chatting about document: <strong>${selectedDocument}</strong>
                        </div>
                    `;
                    chatMessages.appendChild(systemMessage);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            }
        })
        .catch(error => {
            console.error('Error setting active document:', error);
        });
    });
}

// Add theme switcher
function addThemeSwitcher() {
    // Create theme switcher button
    const themeBtn = document.createElement('button');
    themeBtn.className = 'theme-switch btn btn-sm btn-outline-light ms-2';
    themeBtn.innerHTML = '<i class="fas fa-moon"></i>';
    
    // Add to navbar
    const navbar = document.querySelector('.navbar-brand');
    if (navbar && navbar.parentNode) {
        navbar.parentNode.insertBefore(themeBtn, navbar.nextSibling);
    }
    
    // Check for saved theme preference
    const currentTheme = localStorage.getItem('theme') || 'light';
    if (currentTheme === 'dark') {
        document.body.classList.add('dark-theme');
        themeBtn.innerHTML = '<i class="fas fa-sun"></i>';
    }
    
    // Add click handler
    themeBtn.addEventListener('click', function() {
        document.body.classList.toggle('dark-theme');
        
        if (document.body.classList.contains('dark-theme')) {
            localStorage.setItem('theme', 'dark');
            themeBtn.innerHTML = '<i class="fas fa-sun"></i>';
        } else {
            localStorage.setItem('theme', 'light');
            themeBtn.innerHTML = '<i class="fas fa-moon"></i>';
        }
    });
}

// Add responsive features for mobile devices
function enhanceMobileExperience() {
    const toggleViewBtn = document.createElement('button');
    toggleViewBtn.className = 'd-lg-none btn btn-sm btn-outline-primary toggle-view-btn';
    toggleViewBtn.innerHTML = '<i class="fas fa-comments"></i>';
    toggleViewBtn.setAttribute('title', 'Toggle between document and chat view');
    
    // Add to document
    document.body.appendChild(toggleViewBtn);
    
    // Add click handler
    toggleViewBtn.addEventListener('click', function() {
        const documentPanel = document.getElementById('documentPanel');
        const chatPanel = document.getElementById('chatPanel');
        
        if (documentPanel.style.display === 'none') {
            // Show document, hide chat
            documentPanel.style.display = 'flex';
            chatPanel.style.display = 'none';
            toggleViewBtn.innerHTML = '<i class="fas fa-comments"></i>';
        } else {
            // Show chat, hide document
            documentPanel.style.display = 'none';
            chatPanel.style.display = 'flex';
            toggleViewBtn.innerHTML = '<i class="fas fa-file-pdf"></i>';
        }
    });
}

// Run all initializations when document is ready
document.addEventListener('DOMContentLoaded', function() {
    initPDFViewer();
    initChatInterface();
    initDocumentSelector();
    initUploadForm();
    initDocumentListModal();
    addTypingAnimation();
    addThemeSwitcher();
    enhanceMobileExperience();
    initMouseWheelZoom();
    
    // Add dark theme CSS
    const darkThemeCSS = `
        body.dark-theme {
            background-color: #1a1a1a;
            color: #f0f0f0;
        }
        
        body.dark-theme .document-panel,
        body.dark-theme .chat-header,
        body.dark-theme .chat-input,
        body.dark-theme .document-header,
        body.dark-theme .modal-content {
            background-color: #2d2d2d;
            color: #f0f0f0;
            border-color: #444;
        }
        
        body.dark-theme .form-control,
        body.dark-theme .form-select {
            background-color: #333;
            color: #f0f0f0;
            border-color: #555;
        }
        
        body.dark-theme .assistant-message {
            background-color: #2d2d2d;
            color: #f0f0f0;
        }
        
        body.dark-theme .assistant-message .message-content {
            color: #f0f0f0;
        }
        
        body.dark-theme .chat-welcome {
            background-color: #2d2d2d;
            color: #f0f0f0;
        }
        
        body.dark-theme .pdf-viewer-container {
            background-color: #333;
        }
        
        body.dark-theme .empty-viewer-message {
            color: #aaa;
        }
        
        body.dark-theme .toggle-view-btn {
            background-color: #444;
            color: #fff;
            border-color: #555;
        }
    `;
    
    const style = document.createElement('style');
    style.textContent = darkThemeCSS;
    document.head.appendChild(style);
});

// Global variables for PDF viewer
let currentPdfDoc = null;
let currentPage = 1;
let currentZoomLevel = 1.5; // Default zoom level

function initPDFViewer() {
    const pdfViewer = document.getElementById('pdfViewer');
    if (!pdfViewer) return;
    
    const pdfUrl = pdfViewer.dataset.pdfUrl;
    if (!pdfUrl) return;
    
    // Initialize zoom controls
    initZoomControls();
    
    // PDF.js worker path
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.4.120/build/pdf.worker.min.js';
    
    // Load and render PDF
    const loadingTask = pdfjsLib.getDocument(pdfUrl);
    loadingTask.promise.then(function(pdf) {
        currentPdfDoc = pdf;
        
        // Update page info
        const pageInfo = document.getElementById('pageInfo');
        if (pageInfo) {
            pageInfo.textContent = `Page 1 of ${pdf.numPages}`;
        }
        
        // Clear viewer
        pdfViewer.innerHTML = '';
        
        // Create container for pages
        const pagesContainer = document.createElement('div');
        pagesContainer.className = 'pdf-pages-container';
        pdfViewer.appendChild(pagesContainer);
        
        // Render all pages
        const pagePromises = [];
        for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
            pagePromises.push(renderPage(pdf, pageNum, pagesContainer));
        }
        
        return Promise.all(pagePromises);
    }).catch(function(error) {
        console.error('Error loading PDF:', error);
        pdfViewer.innerHTML = `
            <div class="empty-viewer-message">
                <i class="fas fa-exclamation-circle fa-3x mb-3 text-danger"></i>
                <p>Error loading PDF document</p>
                <small class="text-muted">${error.message}</small>
            </div>
        `;
    });
    
    // Initialize page navigation controls
    initPageControls();
}

function renderPage(pdf, pageNum, container) {
    return pdf.getPage(pageNum).then(function(page) {
        const scale = currentZoomLevel;
        const viewport = page.getViewport({ scale });
        
        // Create page container
        const pageContainer = document.createElement('div');
        pageContainer.className = 'pdf-page-container';
        pageContainer.style.position = 'relative';
        pageContainer.dataset.pageNumber = pageNum;
        container.appendChild(pageContainer);
        
        // Create canvas
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        pageContainer.appendChild(canvas);
        
        // Render PDF page
        const renderContext = {
            canvasContext: context,
            viewport: viewport
        };
        
        return page.render(renderContext).promise;
    });
}

function initZoomControls() {
    const zoomIn = document.getElementById('zoomIn');
    const zoomOut = document.getElementById('zoomOut');
    const zoomFit = document.getElementById('zoomFit');
    const zoomLevelEl = document.getElementById('zoomLevel');
    
    if (!zoomIn || !zoomOut || !zoomFit || !zoomLevelEl) return;
    
    // Update zoom level display
    zoomLevelEl.textContent = `${Math.round(currentZoomLevel * 100)}%`;
    
    // Zoom in
    zoomIn.addEventListener('click', function() {
        if (currentZoomLevel >= 3) return; // Max zoom level
        currentZoomLevel += 0.25;
        updateZoom();
    });
    
    // Zoom out
    zoomOut.addEventListener('click', function() {
        if (currentZoomLevel <= 0.5) return; // Min zoom level
        currentZoomLevel -= 0.25;
        updateZoom();
    });
    
    // Fit to width
    zoomFit.addEventListener('click', function() {
        const pdfViewer = document.getElementById('pdfViewer');
        if (!pdfViewer || !currentPdfDoc) return;
        
        // Get the viewer width
        const viewerWidth = pdfViewer.clientWidth - 40; // Subtract padding
        
        // Get the first page to calculate fit to width
        currentPdfDoc.getPage(1).then(function(page) {
            const viewport = page.getViewport({ scale: 1.0 });
            // Calculate scale to fit width
            currentZoomLevel = viewerWidth / viewport.width;
            updateZoom();
        });
    });
}

function updateZoom() {
    // Update zoom level display
    const zoomLevelEl = document.getElementById('zoomLevel');
    if (zoomLevelEl) {
        zoomLevelEl.textContent = `${Math.round(currentZoomLevel * 100)}%`;
    }
    
    // Re-render the PDF with new zoom level
    const pdfViewer = document.getElementById('pdfViewer');
    if (!pdfViewer || !currentPdfDoc) return;
    
    // Clear viewer
    const pagesContainer = pdfViewer.querySelector('.pdf-pages-container');
    if (pagesContainer) {
        pagesContainer.innerHTML = '';
        
        // Re-render all pages
        for (let pageNum = 1; pageNum <= currentPdfDoc.numPages; pageNum++) {
            renderPage(currentPdfDoc, pageNum, pagesContainer);
        }
        
        // Scroll to current page
        const currentPageEl = pagesContainer.querySelector(`[data-page-number="${currentPage}"]`);
        if (currentPageEl) {
            currentPageEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
}

function initPageControls() {
    const prevPage = document.getElementById('prevPage');
    const nextPage = document.getElementById('nextPage');
    const pageInfo = document.getElementById('pageInfo');
    
    if (!prevPage || !nextPage || !pageInfo) return;
    
    // Previous page
    prevPage.addEventListener('click', function() {
        if (!currentPdfDoc || currentPage <= 1) return;
        currentPage--;
        updatePageView();
    });
    
    // Next page
    nextPage.addEventListener('click', function() {
        if (!currentPdfDoc || currentPage >= currentPdfDoc.numPages) return;
        currentPage++;
        updatePageView();
    });
}

function updatePageView() {
    // Update page info display
    const pageInfo = document.getElementById('pageInfo');
    if (pageInfo && currentPdfDoc) {
        pageInfo.textContent = `Page ${currentPage} of ${currentPdfDoc.numPages}`;
    }
    
    // Scroll to current page
    const pdfViewer = document.getElementById('pdfViewer');
    if (!pdfViewer) return;
    
    const currentPageEl = pdfViewer.querySelector(`[data-page-number="${currentPage}"]`);
    if (currentPageEl) {
        currentPageEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// Add keyboard navigation
function initKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Only process if we're not in an input field
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        
        // Page navigation
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
            if (currentPdfDoc && currentPage < currentPdfDoc.numPages) {
                currentPage++;
                updatePageView();
            }
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
            if (currentPdfDoc && currentPage > 1) {
                currentPage--;
                updatePageView();
            }
        }
        
        // Zoom controls
        if (e.ctrlKey && e.key === '=') {
            e.preventDefault();
            document.getElementById('zoomIn')?.click();
        } else if (e.ctrlKey && e.key === '-') {
            e.preventDefault();
            document.getElementById('zoomOut')?.click();
        } else if (e.ctrlKey && e.key === '0') {
            e.preventDefault();
            document.getElementById('zoomFit')?.click();
        }
    });
}

function initChatInterface() {
    const chatForm = document.getElementById('chatForm');
    const queryInput = document.getElementById('queryInput');
    const chatMessages = document.getElementById('chatMessages');
    const clearChatBtn = document.getElementById('clearChat');
    
    if (!chatForm || !queryInput || !chatMessages) {
        console.error('Chat interface elements not found');
        return;
    }
    
    console.log('Chat interface initialized');
    
    // Submit handler
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const query = queryInput.value.trim();
        if (!query) return;
        
        // Clear input
        queryInput.value = '';
        
        // Get active document
        const documentSelector = document.getElementById('documentSelector');
        const activeDocument = documentSelector ? documentSelector.value : '';
        
        // Add user message immediately
        const currentTime = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        // Remove welcome message if present
        const welcomeMsg = chatMessages.querySelector('.chat-welcome');
        if (welcomeMsg) {
            chatMessages.removeChild(welcomeMsg);
        }
        
        // Append user message
        const userMessageEl = document.createElement('div');
        userMessageEl.className = 'chat-message user-message';
        userMessageEl.innerHTML = `
            <div class="message-content">${escapeHtml(query)}</div>
            <div class="message-time">${currentTime}</div>
        `;
        chatMessages.appendChild(userMessageEl);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Show typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'chat-message assistant-message typing-indicator';
        typingIndicator.innerHTML = `
            <div class="message-content">
                <div class="typing-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        chatMessages.appendChild(typingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        console.log('Sending question to server:', query);
        
        // Send request to server
        fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: new URLSearchParams({
                'query': query,
                'active_document': activeDocument
            })
        })
        .then(response => {
            console.log('Response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Chat response received:', data);
            
            // Remove typing indicator
            if (typingIndicator && typingIndicator.parentNode) {
                chatMessages.removeChild(typingIndicator);
            }
            
            if (data.error) {
                // Show error message
                const errorMessageEl = document.createElement('div');
                errorMessageEl.className = 'chat-message assistant-message error-message';
                errorMessageEl.innerHTML = `
                    <div class="message-content">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        ${data.error}
                    </div>
                    <div class="message-time">${currentTime}</div>
                `;
                chatMessages.appendChild(errorMessageEl);
            } else {
                // Add assistant response
                const assistantMessageEl = document.createElement('div');
                assistantMessageEl.className = 'chat-message assistant-message';
                assistantMessageEl.innerHTML = `
                    <div class="message-content">${data.answer}</div>
                    <div class="message-time">${currentTime}</div>
                `;
                chatMessages.appendChild(assistantMessageEl);
            }
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        })
        .catch(error => {
            console.error('Error processing question:', error);
            
            // Remove typing indicator
            if (typingIndicator && typingIndicator.parentNode) {
                chatMessages.removeChild(typingIndicator);
            }
            
            // Show error message
            const errorMessageEl = document.createElement('div');
            errorMessageEl.className = 'chat-message assistant-message error-message';
            errorMessageEl.innerHTML = `
                <div class="message-content">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Network error. Please try again.
                </div>
                <div class="message-time">${currentTime}</div>
            `;
            chatMessages.appendChild(errorMessageEl);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        });
    });
    
    // Clear chat handler
    if (clearChatBtn) {
        clearChatBtn.addEventListener('click', function() {
            // Confirm clear
            if (!confirm('Are you sure you want to clear the chat history?')) return;
            
            fetch('/clear_chat', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Clear chat UI
                    chatMessages.innerHTML = `
                        <div class="chat-welcome">
                            <div class="welcome-icon">
                                <i class="fas fa-robot fa-3x"></i>
                            </div>
                            <h3>Hello! I'm your document assistant</h3>
                            <p>Ask me anything about the document you've uploaded, and I'll try to help answer your questions.</p>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error clearing chat:', error);
                alert('Error clearing chat history. Please try again.');
            });
        });
    }
}

function initMouseWheelZoom() {
    const pdfViewer = document.getElementById('pdfViewer');
    if (!pdfViewer) return;
    
    pdfViewer.addEventListener('wheel', function(e) {
        // Only zoom if Ctrl key is pressed
        if (e.ctrlKey) {
            e.preventDefault(); // Prevent page scrolling
            
            if (e.deltaY < 0) {
                // Zoom in
                if (currentZoomLevel < 3) {
                    currentZoomLevel += 0.1;
                    updateZoom();
                }
            } else {
                // Zoom out
                if (currentZoomLevel > 0.5) {
                    currentZoomLevel -= 0.1;
                    updateZoom();
                }
            }
        }
    });
} 