/**
 * WebSocket client for real-time image generation
 * Enables cutting client-designer revision cycles by 30%
 */

class EchoWebSocketClient {
    constructor() {
        this.socket = null;
        this.sessionId = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.eventHandlers = new Map();
        
        this.initializeConnection();
    }

    /**
     * Initialize WebSocket connection for real-time communication
     */
    initializeConnection() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}`;
            
            this.socket = io(wsUrl, {
                transports: ['websocket', 'polling'],
                timeout: 20000,
                forceNew: true
            });

            this.setupEventHandlers();
            this.setupReconnectionLogic();
            
        } catch (error) {
            console.error('Failed to initialize WebSocket connection:', error);
            this.showConnectionError('Unable to establish real-time connection');
        }
    }

    /**
     * Setup WebSocket event handlers for real-time image generation
     */
    setupEventHandlers() {
        this.socket.on('connect', () => {
            console.log('Connected to real-time image generation service');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus('connected');
            this.emit('connected');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from real-time service');
            this.isConnected = false;
            this.updateConnectionStatus('disconnected');
            this.emit('disconnected');
        });

        this.socket.on('status', (data) => {
            console.log('Status update:', data.message);
            this.emit('status', data);
        });

        // Real-time image generation events
        this.socket.on('generation_started', (data) => {
            console.log('Image generation started:', data);
            this.showGenerationProgress('Starting image generation...', 0);
            this.emit('generation_started', data);
        });

        this.socket.on('generation_progress', (data) => {
            console.log('Generation progress:', data);
            this.showGenerationProgress(data.status, data.progress);
            this.emit('generation_progress', data);
        });

        this.socket.on('generation_complete', (data) => {
            console.log('Image generation complete:', data);
            this.showGenerationProgress('Generation complete!', 100);
            this.displayGeneratedImages(data.images);
            this.emit('generation_complete', data);
        });

        this.socket.on('generation_error', (data) => {
            console.error('Generation error:', data);
            this.showGenerationError(data.message || 'Image generation failed');
            this.emit('generation_error', data);
        });

        // Feedback processing events
        this.socket.on('feedback_processing', (data) => {
            console.log('Processing feedback:', data);
            this.showFeedbackProgress(data.message, data.progress);
            this.emit('feedback_processing', data);
        });

        this.socket.on('feedback_complete', (data) => {
            console.log('Feedback processed:', data);
            this.showFeedbackComplete(data);
            if (data.new_image_url) {
                this.displayGeneratedImages([data.new_image_url]);
            }
            this.emit('feedback_complete', data);
        });

        this.socket.on('feedback_error', (data) => {
            console.error('Feedback error:', data);
            this.showFeedbackError(data.message || 'Feedback processing failed');
            this.emit('feedback_error', data);
        });

        this.socket.on('error', (data) => {
            console.error('WebSocket error:', data);
            this.showConnectionError(data.message || 'Connection error occurred');
        });
    }

    /**
     * Setup automatic reconnection logic
     */
    setupReconnectionLogic() {
        this.socket.on('disconnect', () => {
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
                
                setTimeout(() => {
                    if (!this.isConnected) {
                        this.socket.connect();
                    }
                }, 2000 * this.reconnectAttempts); // Exponential backoff
            } else {
                this.showConnectionError('Connection lost. Please refresh the page.');
            }
        });
    }

    /**
     * Join a session for real-time updates
     */
    joinSession(sessionId, userId) {
        if (!this.isConnected) {
            console.warn('Cannot join session: WebSocket not connected');
            return;
        }

        this.sessionId = sessionId;
        this.socket.emit('join_session', {
            session_id: sessionId,
            user_id: userId
        });
    }

    /**
     * Start real-time image generation
     */
    startRealtimeGeneration(requirements, sessionId = null) {
        if (!this.isConnected) {
            this.showConnectionError('Not connected to real-time service');
            return;
        }

        const generationRequest = {
            requirements: requirements,
            session_id: sessionId || this.sessionId || `session_${Date.now()}`,
            timestamp: new Date().toISOString()
        };

        console.log('Starting real-time generation:', generationRequest);
        this.socket.emit('start_realtime_generation', generationRequest);
    }

    /**
     * Send real-time feedback on generated images
     */
    sendRealtimeFeedback(imageUrl, feedback, sessionId = null) {
        if (!this.isConnected) {
            this.showConnectionError('Not connected to real-time service');
            return;
        }

        const feedbackRequest = {
            image_url: imageUrl,
            feedback: feedback,
            session_id: sessionId || this.sessionId,
            timestamp: new Date().toISOString()
        };

        console.log('Sending real-time feedback:', feedbackRequest);
        this.socket.emit('realtime_feedback', feedbackRequest);
    }

    /**
     * Add event listener
     */
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    /**
     * Remove event listener
     */
    off(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    /**
     * Emit custom event
     */
    emit(event, data) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${event}:`, error);
                }
            });
        }
    }

    /**
     * Update connection status in UI
     */
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.className = `connection-status ${status}`;
            statusElement.textContent = status === 'connected' 
                ? 'Real-time: Connected' 
                : 'Real-time: Disconnected';
        }
    }

    /**
     * Show generation progress
     */
    showGenerationProgress(message, progress) {
        const progressContainer = document.getElementById('generation-progress');
        if (progressContainer) {
            progressContainer.style.display = 'block';
            
            const messageElement = progressContainer.querySelector('.progress-message');
            const progressBar = progressContainer.querySelector('.progress-bar');
            const progressFill = progressContainer.querySelector('.progress-fill');
            
            if (messageElement) messageElement.textContent = message;
            if (progressFill) progressFill.style.width = `${progress}%`;
            
            if (progress >= 100) {
                setTimeout(() => {
                    progressContainer.style.display = 'none';
                }, 2000);
            }
        }
    }

    /**
     * Show feedback progress
     */
    showFeedbackProgress(message, progress) {
        const feedbackProgress = document.getElementById('feedback-progress');
        if (feedbackProgress) {
            feedbackProgress.style.display = 'block';
            
            const messageElement = feedbackProgress.querySelector('.feedback-message');
            const progressFill = feedbackProgress.querySelector('.feedback-progress-fill');
            
            if (messageElement) messageElement.textContent = message;
            if (progressFill) progressFill.style.width = `${progress}%`;
            
            if (progress >= 100) {
                setTimeout(() => {
                    feedbackProgress.style.display = 'none';
                }, 2000);
            }
        }
    }

    /**
     * Display generated images in real-time
     */
    displayGeneratedImages(imageUrls) {
        const imageContainer = document.getElementById('generated-images');
        if (!imageContainer) return;

        imageUrls.forEach((imageUrl, index) => {
            const imageWrapper = document.createElement('div');
            imageWrapper.className = 'generated-image-wrapper fade-in';
            imageWrapper.style.animationDelay = `${index * 0.2}s`;

            const img = document.createElement('img');
            img.src = imageUrl;
            img.className = 'generated-image';
            img.alt = 'Generated concept image';
            
            img.onload = () => {
                imageWrapper.classList.add('loaded');
            };

            img.onerror = () => {
                imageWrapper.innerHTML = '<div class="image-error">Failed to load image</div>';
            };

            // Add feedback button
            const feedbackButton = document.createElement('button');
            feedbackButton.className = 'feedback-button';
            feedbackButton.textContent = 'Provide Feedback';
            feedbackButton.onclick = () => this.showFeedbackModal(imageUrl);

            imageWrapper.appendChild(img);
            imageWrapper.appendChild(feedbackButton);
            imageContainer.appendChild(imageWrapper);
        });
    }

    /**
     * Show feedback modal for image revision
     */
    showFeedbackModal(imageUrl) {
        const modal = document.getElementById('feedback-modal');
        const imagePreview = document.getElementById('feedback-image-preview');
        const feedbackInput = document.getElementById('feedback-input');
        const submitButton = document.getElementById('submit-feedback');

        if (modal && imagePreview && feedbackInput && submitButton) {
            imagePreview.src = imageUrl;
            feedbackInput.value = '';
            modal.style.display = 'block';

            submitButton.onclick = () => {
                const feedback = feedbackInput.value.trim();
                if (feedback) {
                    this.sendRealtimeFeedback(imageUrl, feedback);
                    modal.style.display = 'none';
                }
            };
        }
    }

    /**
     * Show feedback completion
     */
    showFeedbackComplete(data) {
        const notification = document.createElement('div');
        notification.className = 'feedback-notification success';
        notification.innerHTML = `
            <div class="notification-content">
                <h4>Feedback Processed!</h4>
                <p>${data.response}</p>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    /**
     * Show generation error
     */
    showGenerationError(message) {
        this.showNotification('Generation Error', message, 'error');
    }

    /**
     * Show feedback error
     */
    showFeedbackError(message) {
        this.showNotification('Feedback Error', message, 'error');
    }

    /**
     * Show connection error
     */
    showConnectionError(message) {
        this.showNotification('Connection Error', message, 'error');
    }

    /**
     * Show notification
     */
    showNotification(title, message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <h4>${title}</h4>
                <p>${message}</p>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 8000);
    }

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.isConnected = false;
        }
    }

    /**
     * Get connection status
     */
    getConnectionStatus() {
        return {
            isConnected: this.isConnected,
            sessionId: this.sessionId,
            reconnectAttempts: this.reconnectAttempts
        };
    }
}

// Initialize WebSocket client when page loads
let echoWebSocket = null;

document.addEventListener('DOMContentLoaded', () => {
    try {
        echoWebSocket = new EchoWebSocketClient();
        console.log('Echo WebSocket client initialized');
        
        // Make it globally available
        window.echoWebSocket = echoWebSocket;
        
    } catch (error) {
        console.error('Failed to initialize Echo WebSocket client:', error);
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EchoWebSocketClient;
}