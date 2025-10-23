/**
 * Real-time image generation interface
 * Leverages AWS Bedrock models for cutting client-designer revision cycles by 30%
 */

class ImageGenerationManager {
    constructor() {
        this.currentSession = null;
        this.generationHistory = [];
        this.isGenerating = false;
        this.awsConfig = {
            region: 'us-west-2',
            bedrockModel: 'stability.stable-image-ultra-v1:1'
        };
        
        this.initializeInterface();
        this.setupEventListeners();
    }

    /**
     * Initialize the image generation interface
     */
    initializeInterface() {
        this.createGenerationInterface();
        this.createProgressIndicators();
        this.createImageGallery();
        this.createFeedbackModal();
    }

    /**
     * Create the main generation interface
     */
    createGenerationInterface() {
        const container = document.getElementById('generation-container') || this.createContainer();
        
        container.innerHTML = `
            <div class="generation-interface">
                <div class="connection-status-bar">
                    <div id="connection-status" class="connection-status disconnected">
                        Real-time: Connecting...
                    </div>
                    <div class="aws-badge">
                        <span class="aws-icon">☁️</span>
                        Powered by AWS Bedrock
                    </div>
                </div>
                
                <div class="generation-form">
                    <h3>AI-Powered Design Generation</h3>
                    <div class="form-group">
                        <label for="requirements-input">Design Requirements:</label>
                        <textarea 
                            id="requirements-input" 
                            placeholder="Describe your design concept in detail..."
                            rows="4"
                            maxlength="1000"
                        ></textarea>
                        <div class="character-count">
                            <span id="char-count">0</span>/1000 characters
                        </div>
                    </div>
                    
                    <div class="generation-options">
                        <div class="option-group">
                            <label for="style-select">Style Preference:</label>
                            <select id="style-select">
                                <option value="professional">Professional</option>
                                <option value="modern">Modern</option>
                                <option value="minimalist">Minimalist</option>
                                <option value="creative">Creative</option>
                                <option value="luxury">Luxury</option>
                            </select>
                        </div>
                        
                        <div class="option-group">
                            <label for="color-scheme">Color Scheme:</label>
                            <select id="color-scheme">
                                <option value="vibrant">Vibrant</option>
                                <option value="muted">Muted</option>
                                <option value="monochrome">Monochrome</option>
                                <option value="warm">Warm Tones</option>
                                <option value="cool">Cool Tones</option>
                            </select>
                        </div>
                        
                        <div class="option-group">
                            <label>
                                <input type="checkbox" id="realtime-mode" checked>
                                Real-time Generation Mode
                            </label>
                        </div>
                    </div>
                    
                    <button 
                        id="generate-button" 
                        class="generate-button"
                        disabled
                    >
                        <span class="button-icon">🎨</span>
                        Generate Design Concepts
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Create progress indicators for real-time feedback
     */
    createProgressIndicators() {
        const progressHTML = `
            <div id="generation-progress" class="progress-container" style="display: none;">
                <div class="progress-header">
                    <h4>Generating with AWS Bedrock...</h4>
                    <div class="progress-message">Initializing...</div>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div class="progress-details">
                    <div class="aws-status">
                        <span class="status-dot"></span>
                        Connected to AWS Lambda
                    </div>
                    <div class="bedrock-status">
                        <span class="status-dot"></span>
                        Processing with Stability AI
                    </div>
                </div>
            </div>
            
            <div id="feedback-progress" class="feedback-progress-container" style="display: none;">
                <div class="feedback-header">
                    <h4>Processing Your Feedback...</h4>
                    <div class="feedback-message">Analyzing changes...</div>
                </div>
                <div class="progress-bar">
                    <div class="feedback-progress-fill"></div>
                </div>
            </div>
        `;
        
        const container = document.getElementById('generation-container');
        container.insertAdjacentHTML('beforeend', progressHTML);
    }

    /**
     * Create image gallery for generated concepts
     */
    createImageGallery() {
        const galleryHTML = `
            <div id="image-gallery" class="image-gallery">
                <div class="gallery-header">
                    <h3>Generated Design Concepts</h3>
                    <div class="revision-info">
                        <span class="revision-count">Revisions: <span id="revision-count">0</span></span>
                        <span class="cost-info">💰 No scaling costs with AWS Lambda</span>
                    </div>
                </div>
                <div id="generated-images" class="generated-images-grid">
                    <!-- Generated images will appear here -->
                </div>
            </div>
        `;
        
        const container = document.getElementById('generation-container');
        container.insertAdjacentHTML('beforeend', galleryHTML);
    }

    /**
     * Create feedback modal for image revisions
     */
    createFeedbackModal() {
        const modalHTML = `
            <div id="feedback-modal" class="modal" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Provide Feedback for Revision</h3>
                        <button class="modal-close" onclick="this.closest('.modal').style.display='none'">×</button>
                    </div>
                    <div class="modal-body">
                        <div class="feedback-preview">
                            <img id="feedback-image-preview" alt="Image for feedback" />
                        </div>
                        <div class="feedback-form">
                            <label for="feedback-input">What would you like to change?</label>
                            <textarea 
                                id="feedback-input" 
                                placeholder="Describe the changes you'd like to see..."
                                rows="4"
                            ></textarea>
                            <div class="feedback-suggestions">
                                <h4>Quick Suggestions:</h4>
                                <div class="suggestion-buttons">
                                    <button class="suggestion-btn" data-feedback="Make it more colorful">More Colorful</button>
                                    <button class="suggestion-btn" data-feedback="Simplify the design">Simplify</button>
                                    <button class="suggestion-btn" data-feedback="Add more details">More Details</button>
                                    <button class="suggestion-btn" data-feedback="Change the style to modern">Modern Style</button>
                                    <button class="suggestion-btn" data-feedback="Make it more professional">Professional</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button id="submit-feedback" class="submit-feedback-btn">
                            Submit Feedback & Generate Revision
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Setup suggestion button handlers
        document.querySelectorAll('.suggestion-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const feedback = btn.getAttribute('data-feedback');
                document.getElementById('feedback-input').value = feedback;
            });
        });
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Character count for requirements input
        const requirementsInput = document.getElementById('requirements-input');
        if (requirementsInput) {
            requirementsInput.addEventListener('input', (e) => {
                const count = e.target.value.length;
                document.getElementById('char-count').textContent = count;
                
                // Enable/disable generate button
                const generateButton = document.getElementById('generate-button');
                generateButton.disabled = count < 10 || this.isGenerating;
            });
        }

        // Generate button
        const generateButton = document.getElementById('generate-button');
        if (generateButton) {
            generateButton.addEventListener('click', () => {
                this.startGeneration();
            });
        }

        // WebSocket event listeners
        if (window.echoWebSocket) {
            window.echoWebSocket.on('connected', () => {
                this.onWebSocketConnected();
            });

            window.echoWebSocket.on('generation_complete', (data) => {
                this.onGenerationComplete(data);
            });

            window.echoWebSocket.on('feedback_complete', (data) => {
                this.onFeedbackComplete(data);
            });
        }

        // Real-time mode toggle
        const realtimeMode = document.getElementById('realtime-mode');
        if (realtimeMode) {
            realtimeMode.addEventListener('change', (e) => {
                this.toggleRealtimeMode(e.target.checked);
            });
        }
    }

    /**
     * Create container if it doesn't exist
     */
    createContainer() {
        const container = document.createElement('div');
        container.id = 'generation-container';
        container.className = 'generation-container';
        
        // Insert after main content or at end of body
        const mainContent = document.querySelector('main') || document.body;
        mainContent.appendChild(container);
        
        return container;
    }

    /**
     * Start image generation process
     */
    async startGeneration() {
        const requirements = document.getElementById('requirements-input').value.trim();
        const style = document.getElementById('style-select').value;
        const colorScheme = document.getElementById('color-scheme').value;
        const realtimeMode = document.getElementById('realtime-mode').checked;

        if (!requirements) {
            this.showNotification('Please provide design requirements', 'warning');
            return;
        }

        this.isGenerating = true;
        this.updateGenerateButton(true);

        // Enhanced requirements with style preferences
        const enhancedRequirements = `${requirements}. Style: ${style}. Color scheme: ${colorScheme}.`;

        try {
            if (realtimeMode && window.echoWebSocket && window.echoWebSocket.isConnected) {
                // Use real-time WebSocket generation
                this.currentSession = `session_${Date.now()}`;
                window.echoWebSocket.joinSession(this.currentSession, this.getCurrentUserId());
                window.echoWebSocket.startRealtimeGeneration(enhancedRequirements, this.currentSession);
            } else {
                // Fallback to traditional API
                await this.generateViaAPI(enhancedRequirements);
            }

        } catch (error) {
            console.error('Generation failed:', error);
            this.showNotification('Generation failed. Please try again.', 'error');
            this.isGenerating = false;
            this.updateGenerateButton(false);
        }
    }

    /**
     * Generate via traditional API (fallback)
     */
    async generateViaAPI(requirements) {
        try {
            const response = await fetch('/api/briefing/generate-images', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ requirements }),
            });

            const data = await response.json();
            
            if (data.image_urls && data.image_urls.length > 0) {
                this.onGenerationComplete({ images: data.image_urls });
            } else {
                throw new Error('No images generated');
            }

        } catch (error) {
            throw new Error(`API generation failed: ${error.message}`);
        }
    }

    /**
     * Handle WebSocket connection
     */
    onWebSocketConnected() {
        console.log('WebSocket connected for real-time generation');
        const generateButton = document.getElementById('generate-button');
        if (generateButton && !this.isGenerating) {
            generateButton.disabled = false;
        }
    }

    /**
     * Handle generation completion
     */
    onGenerationComplete(data) {
        console.log('Generation completed:', data);
        
        this.isGenerating = false;
        this.updateGenerateButton(false);
        
        if (data.images && data.images.length > 0) {
            this.addImagesToGallery(data.images);
            this.updateRevisionCount();
            this.showNotification('Design concepts generated successfully!', 'success');
        }
    }

    /**
     * Handle feedback completion
     */
    onFeedbackComplete(data) {
        console.log('Feedback processed:', data);
        
        if (data.new_image_url) {
            this.addImagesToGallery([data.new_image_url]);
            this.updateRevisionCount();
            this.showNotification('Revision generated based on your feedback!', 'success');
        }
    }

    /**
     * Add images to gallery
     */
    addImagesToGallery(imageUrls) {
        const gallery = document.getElementById('generated-images');
        if (!gallery) return;

        imageUrls.forEach((imageUrl, index) => {
            const imageWrapper = this.createImageElement(imageUrl, index);
            gallery.appendChild(imageWrapper);
        });

        // Show gallery if hidden
        const galleryContainer = document.getElementById('image-gallery');
        if (galleryContainer) {
            galleryContainer.style.display = 'block';
        }
    }

    /**
     * Create image element with feedback functionality
     */
    createImageElement(imageUrl, index) {
        const wrapper = document.createElement('div');
        wrapper.className = 'image-wrapper fade-in';
        wrapper.style.animationDelay = `${index * 0.2}s`;

        wrapper.innerHTML = `
            <div class="image-container">
                <img src="${imageUrl}" alt="Generated design concept" class="generated-image" />
                <div class="image-overlay">
                    <div class="image-actions">
                        <button class="action-btn feedback-btn" data-image="${imageUrl}">
                            <span>💬</span> Revise
                        </button>
                        <button class="action-btn download-btn" data-image="${imageUrl}">
                            <span>⬇️</span> Download
                        </button>
                        <button class="action-btn share-btn" data-image="${imageUrl}">
                            <span>🔗</span> Share
                        </button>
                    </div>
                </div>
            </div>
            <div class="image-info">
                <div class="generation-time">${new Date().toLocaleTimeString()}</div>
                <div class="aws-badge-small">AWS Bedrock</div>
            </div>
        `;

        // Add event listeners
        const feedbackBtn = wrapper.querySelector('.feedback-btn');
        const downloadBtn = wrapper.querySelector('.download-btn');
        const shareBtn = wrapper.querySelector('.share-btn');

        if (feedbackBtn) {
            feedbackBtn.addEventListener('click', () => {
                this.showFeedbackModal(imageUrl);
            });
        }

        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => {
                this.downloadImage(imageUrl);
            });
        }

        if (shareBtn) {
            shareBtn.addEventListener('click', () => {
                this.shareImage(imageUrl);
            });
        }

        return wrapper;
    }

    /**
     * Show feedback modal
     */
    showFeedbackModal(imageUrl) {
        const modal = document.getElementById('feedback-modal');
        const preview = document.getElementById('feedback-image-preview');
        
        if (modal && preview) {
            preview.src = imageUrl;
            modal.style.display = 'block';
            
            // Store current image URL for submission
            modal.setAttribute('data-image-url', imageUrl);
        }
    }

    /**
     * Update generate button state
     */
    updateGenerateButton(isGenerating) {
        const button = document.getElementById('generate-button');
        if (!button) return;

        if (isGenerating) {
            button.disabled = true;
            button.innerHTML = `
                <div class="loading-spinner"></div>
                Generating...
            `;
        } else {
            button.disabled = false;
            button.innerHTML = `
                <span class="button-icon">🎨</span>
                Generate Design Concepts
            `;
        }
    }

    /**
     * Update revision count
     */
    updateRevisionCount() {
        const countElement = document.getElementById('revision-count');
        if (countElement) {
            const currentCount = parseInt(countElement.textContent) || 0;
            countElement.textContent = currentCount + 1;
        }
    }

    /**
     * Toggle real-time mode
     */
    toggleRealtimeMode(enabled) {
        const statusMessage = enabled 
            ? 'Real-time mode enabled - instant feedback!' 
            : 'Real-time mode disabled - using standard API';
        
        this.showNotification(statusMessage, 'info');
    }

    /**
     * Download image
     */
    async downloadImage(imageUrl) {
        try {
            const response = await fetch(imageUrl);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `echo-design-${Date.now()}.png`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            window.URL.revokeObjectURL(url);
            this.showNotification('Image downloaded successfully!', 'success');
            
        } catch (error) {
            console.error('Download failed:', error);
            this.showNotification('Download failed. Please try again.', 'error');
        }
    }

    /**
     * Share image
     */
    async shareImage(imageUrl) {
        if (navigator.share) {
            try {
                await navigator.share({
                    title: 'Echo Design Concept',
                    text: 'Check out this AI-generated design concept!',
                    url: imageUrl,
                });
            } catch (error) {
                console.log('Share cancelled or failed:', error);
            }
        } else {
            // Fallback: copy URL to clipboard
            try {
                await navigator.clipboard.writeText(imageUrl);
                this.showNotification('Image URL copied to clipboard!', 'success');
            } catch (error) {
                console.error('Copy failed:', error);
                this.showNotification('Unable to share. Please copy the URL manually.', 'error');
            }
        }
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        // Use the WebSocket client's notification system if available
        if (window.echoWebSocket) {
            window.echoWebSocket.showNotification('Image Generation', message, type);
        } else {
            // Fallback notification
            console.log(`${type.toUpperCase()}: ${message}`);
            alert(message);
        }
    }

    /**
     * Get current user ID (placeholder)
     */
    getCurrentUserId() {
        // In a real app, this would get the authenticated user ID
        return sessionStorage.getItem('userId') || `user_${Date.now()}`;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Wait a bit for WebSocket to initialize
    setTimeout(() => {
        window.imageGenerationManager = new ImageGenerationManager();
        console.log('Image Generation Manager initialized');
    }, 1000);
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ImageGenerationManager;
}