/**
 * AWS Integration Module for Echo Platform
 * Demonstrates distributed cloud architecture on AWS Lambda with DynamoDB storage
 */

class AWSIntegrationManager {
    constructor() {
        this.config = {
            region: 'us-west-2',
            apiVersion: '2023-01-01',
            services: {
                bedrock: 'bedrock-runtime',
                lambda: 'lambda',
                dynamodb: 'dynamodb',
                s3: 's3'
            }
        };
        
        this.endpoints = {
            lambda: {
                imageGenerator: 'echo-image-generator-dev',
                websocketHandler: 'echo-websocket-handler-dev'
            },
            websocket: this.getWebSocketEndpoint(),
            rest: this.getRestEndpoint()
        };
        
        this.connectionStatus = {
            lambda: false,
            dynamodb: false,
            bedrock: false,
            websocket: false
        };
        
        this.initializeAWSIntegration();
    }

    /**
     * Initialize AWS integration and test connections
     */
    async initializeAWSIntegration() {
        console.log('🚀 Initializing AWS distributed cloud architecture...');
        
        try {
            await this.testAWSConnections();
            this.setupAWSMonitoring();
            this.initializeMetrics();
            
            console.log('✅ AWS integration initialized successfully');
            this.updateAWSStatusDisplay();
            
        } catch (error) {
            console.error('❌ AWS integration initialization failed:', error);
            this.handleAWSError(error);
        }
    }

    /**
     * Test connections to AWS services
     */
    async testAWSConnections() {
        const tests = [
            this.testLambdaConnection(),
            this.testDynamoDBConnection(),
            this.testBedrockConnection(),
            this.testWebSocketConnection()
        ];

        try {
            await Promise.allSettled(tests);
            console.log('AWS connection tests completed');
        } catch (error) {
            console.warn('Some AWS connections failed:', error);
        }
    }

    /**
     * Test AWS Lambda connection for serverless scaling
     */
    async testLambdaConnection() {
        try {
            const response = await fetch('/api/aws/lambda/health', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                this.connectionStatus.lambda = true;
                console.log('✅ AWS Lambda connection successful');
                this.logMetric('lambda_connection', 'success');
            } else {
                throw new Error(`Lambda health check failed: ${response.status}`);
            }

        } catch (error) {
            console.warn('⚠️ Lambda connection test failed:', error.message);
            this.connectionStatus.lambda = false;
            this.logMetric('lambda_connection', 'failed');
        }
    }

    /**
     * Test DynamoDB connection for distributed storage
     */
    async testDynamoDBConnection() {
        try {
            const response = await fetch('/api/aws/dynamodb/health', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                this.connectionStatus.dynamodb = true;
                console.log('✅ DynamoDB connection successful');
                this.logMetric('dynamodb_connection', 'success');
            } else {
                throw new Error(`DynamoDB health check failed: ${response.status}`);
            }

        } catch (error) {
            console.warn('⚠️ DynamoDB connection test failed:', error.message);
            this.connectionStatus.dynamodb = false;
            this.logMetric('dynamodb_connection', 'failed');
        }
    }

    /**
     * Test AWS Bedrock connection for AI models
     */
    async testBedrockConnection() {
        try {
            const response = await fetch('/api/aws/bedrock/health', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                this.connectionStatus.bedrock = true;
                console.log('✅ AWS Bedrock connection successful');
                this.logMetric('bedrock_connection', 'success');
            } else {
                throw new Error(`Bedrock health check failed: ${response.status}`);
            }

        } catch (error) {
            console.warn('⚠️ Bedrock connection test failed:', error.message);
            this.connectionStatus.bedrock = false;
            this.logMetric('bedrock_connection', 'failed');
        }
    }

    /**
     * Test WebSocket connection for real-time communication
     */
    async testWebSocketConnection() {
        try {
            if (window.echoWebSocket && window.echoWebSocket.isConnected) {
                this.connectionStatus.websocket = true;
                console.log('✅ WebSocket connection successful');
                this.logMetric('websocket_connection', 'success');
            } else {
                throw new Error('WebSocket not connected');
            }

        } catch (error) {
            console.warn('⚠️ WebSocket connection test failed:', error.message);
            this.connectionStatus.websocket = false;
            this.logMetric('websocket_connection', 'failed');
        }
    }

    /**
     * Invoke AWS Lambda function for image generation
     */
    async invokeLambdaImageGeneration(payload) {
        try {
            console.log('🔄 Invoking AWS Lambda for image generation...');
            
            const response = await fetch('/api/aws/lambda/invoke', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    functionName: this.endpoints.lambda.imageGenerator,
                    payload: payload
                })
            });

            if (!response.ok) {
                throw new Error(`Lambda invocation failed: ${response.status}`);
            }

            const result = await response.json();
            
            console.log('✅ Lambda function executed successfully');
            this.logMetric('lambda_invocation', 'success');
            
            return result;

        } catch (error) {
            console.error('❌ Lambda invocation failed:', error);
            this.logMetric('lambda_invocation', 'failed');
            throw error;
        }
    }

    /**
     * Store data in DynamoDB for unlimited revisions
     */
    async storeToDynamoDB(tableName, data) {
        try {
            console.log(`🔄 Storing data to DynamoDB table: ${tableName}`);
            
            const response = await fetch('/api/aws/dynamodb/put', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    tableName: tableName,
                    item: {
                        ...data,
                        timestamp: new Date().toISOString(),
                        ttl: Math.floor(Date.now() / 1000) + (24 * 60 * 60) // 24 hour TTL
                    }
                })
            });

            if (!response.ok) {
                throw new Error(`DynamoDB storage failed: ${response.status}`);
            }

            const result = await response.json();
            
            console.log('✅ Data stored to DynamoDB successfully');
            this.logMetric('dynamodb_write', 'success');
            
            return result;

        } catch (error) {
            console.error('❌ DynamoDB storage failed:', error);
            this.logMetric('dynamodb_write', 'failed');
            throw error;
        }
    }

    /**
     * Query DynamoDB for user sessions and history
     */
    async queryDynamoDB(tableName, queryParams) {
        try {
            console.log(`🔄 Querying DynamoDB table: ${tableName}`);
            
            const response = await fetch('/api/aws/dynamodb/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    tableName: tableName,
                    ...queryParams
                })
            });

            if (!response.ok) {
                throw new Error(`DynamoDB query failed: ${response.status}`);
            }

            const result = await response.json();
            
            console.log('✅ DynamoDB query successful');
            this.logMetric('dynamodb_read', 'success');
            
            return result;

        } catch (error) {
            console.error('❌ DynamoDB query failed:', error);
            this.logMetric('dynamodb_read', 'failed');
            throw error;
        }
    }

    /**
     * Generate image using AWS Bedrock models
     */
    async generateWithBedrock(prompt, options = {}) {
        try {
            console.log('🔄 Generating image with AWS Bedrock...');
            
            const payload = {
                model: 'stability.stable-image-ultra-v1:1',
                prompt: prompt,
                options: {
                    output_format: 'png',
                    aspect_ratio: '1:1',
                    seed: options.seed || 0,
                    ...options
                }
            };

            const response = await fetch('/api/aws/bedrock/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`Bedrock generation failed: ${response.status}`);
            }

            const result = await response.json();
            
            console.log('✅ Bedrock image generation successful');
            this.logMetric('bedrock_generation', 'success');
            
            return result;

        } catch (error) {
            console.error('❌ Bedrock generation failed:', error);
            this.logMetric('bedrock_generation', 'failed');
            throw error;
        }
    }

    /**
     * Setup AWS monitoring and metrics
     */
    setupAWSMonitoring() {
        // Monitor connection health
        setInterval(() => {
            this.checkAWSHealth();
        }, 30000); // Check every 30 seconds

        // Monitor performance metrics
        setInterval(() => {
            this.collectPerformanceMetrics();
        }, 60000); // Collect every minute

        console.log('📊 AWS monitoring initialized');
    }

    /**
     * Check AWS service health
     */
    async checkAWSHealth() {
        const healthChecks = await Promise.allSettled([
            this.testLambdaConnection(),
            this.testDynamoDBConnection(),
            this.testBedrockConnection()
        ]);

        const healthStatus = {
            timestamp: new Date().toISOString(),
            lambda: this.connectionStatus.lambda,
            dynamodb: this.connectionStatus.dynamodb,
            bedrock: this.connectionStatus.bedrock,
            websocket: this.connectionStatus.websocket
        };

        // Store health status
        try {
            await this.storeToDynamoDB('echo_health_status', healthStatus);
        } catch (error) {
            console.warn('Failed to store health status:', error);
        }

        this.updateAWSStatusDisplay();
    }

    /**
     * Collect performance metrics
     */
    collectPerformanceMetrics() {
        const metrics = {
            timestamp: new Date().toISOString(),
            sessionId: this.getCurrentSessionId(),
            generationCount: this.getGenerationCount(),
            avgResponseTime: this.getAverageResponseTime(),
            errorRate: this.getErrorRate(),
            scalingEvents: this.getScalingEvents()
        };

        console.log('📈 Performance metrics:', metrics);
        
        // Send metrics to monitoring system
        this.sendMetricsToCloudWatch(metrics);
    }

    /**
     * Initialize metrics tracking
     */
    initializeMetrics() {
        this.metrics = {
            requests: 0,
            errors: 0,
            responseTimes: [],
            generationCount: 0,
            scalingEvents: 0
        };

        // Track page performance
        if ('performance' in window) {
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.name.includes('/api/')) {
                        this.metrics.responseTimes.push(entry.duration);
                        this.metrics.requests++;
                    }
                }
            });
            observer.observe({ entryTypes: ['measure', 'navigation'] });
        }
    }

    /**
     * Log metrics for analysis
     */
    logMetric(metricName, value, tags = {}) {
        const metric = {
            name: metricName,
            value: value,
            timestamp: Date.now(),
            tags: {
                service: 'echo-platform',
                environment: 'production',
                ...tags
            }
        };

        // Store locally for batching
        if (!this.metricsBuffer) {
            this.metricsBuffer = [];
        }
        this.metricsBuffer.push(metric);

        // Flush metrics periodically
        if (this.metricsBuffer.length >= 10) {
            this.flushMetrics();
        }
    }

    /**
     * Send metrics to CloudWatch (simulated)
     */
    sendMetricsToCloudWatch(metrics) {
        // In a real implementation, this would send to CloudWatch
        console.log('📊 Sending metrics to CloudWatch:', metrics);
        
        // Store metrics in DynamoDB for analysis
        this.storeToDynamoDB('echo_metrics', metrics).catch(error => {
            console.warn('Failed to store metrics:', error);
        });
    }

    /**
     * Flush metrics buffer
     */
    flushMetrics() {
        if (this.metricsBuffer && this.metricsBuffer.length > 0) {
            this.sendMetricsToCloudWatch(this.metricsBuffer);
            this.metricsBuffer = [];
        }
    }

    /**
     * Update AWS status display in UI
     */
    updateAWSStatusDisplay() {
        const statusContainer = document.getElementById('aws-status') || this.createAWSStatusDisplay();
        
        const services = [
            { name: 'Lambda', status: this.connectionStatus.lambda, icon: '⚡' },
            { name: 'DynamoDB', status: this.connectionStatus.dynamodb, icon: '🗃️' },
            { name: 'Bedrock', status: this.connectionStatus.bedrock, icon: '🧠' },
            { name: 'WebSocket', status: this.connectionStatus.websocket, icon: '🔗' }
        ];

        statusContainer.innerHTML = `
            <div class="aws-status-header">
                <h4>🏗️ AWS Distributed Architecture Status</h4>
                <div class="cost-savings">💰 Supporting unlimited revisions without scaling costs</div>
            </div>
            <div class="aws-services-grid">
                ${services.map(service => `
                    <div class="aws-service ${service.status ? 'connected' : 'disconnected'}">
                        <div class="service-icon">${service.icon}</div>
                        <div class="service-name">${service.name}</div>
                        <div class="service-status">${service.status ? 'Connected' : 'Disconnected'}</div>
                    </div>
                `).join('')}
            </div>
            <div class="aws-metrics">
                <div class="metric">
                    <span class="metric-label">Generations:</span>
                    <span class="metric-value">${this.getGenerationCount()}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Avg Response:</span>
                    <span class="metric-value">${this.getAverageResponseTime()}ms</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Uptime:</span>
                    <span class="metric-value">${this.getUptime()}</span>
                </div>
            </div>
        `;
    }

    /**
     * Create AWS status display
     */
    createAWSStatusDisplay() {
        const container = document.createElement('div');
        container.id = 'aws-status';
        container.className = 'aws-status-container';
        
        // Insert into page
        const targetContainer = document.getElementById('generation-container') || document.body;
        targetContainer.appendChild(container);
        
        return container;
    }

    /**
     * Handle AWS errors gracefully
     */
    handleAWSError(error) {
        console.error('AWS Error:', error);
        
        const errorNotification = {
            title: 'AWS Service Issue',
            message: 'Some AWS services are experiencing issues. Functionality may be limited.',
            type: 'warning',
            actions: [
                {
                    text: 'Retry',
                    action: () => this.initializeAWSIntegration()
                },
                {
                    text: 'Use Fallback',
                    action: () => this.enableFallbackMode()
                }
            ]
        };

        if (window.echoWebSocket) {
            window.echoWebSocket.showNotification(
                errorNotification.title,
                errorNotification.message,
                errorNotification.type
            );
        }
    }

    /**
     * Enable fallback mode when AWS services are unavailable
     */
    enableFallbackMode() {
        console.log('🔄 Enabling fallback mode for AWS services');
        
        // Switch to local storage instead of DynamoDB
        this.useFallbackStorage = true;
        
        // Use simulated responses for testing
        this.useSimulatedResponses = true;
        
        console.log('✅ Fallback mode enabled');
    }

    /**
     * Get WebSocket endpoint based on environment
     */
    getWebSocketEndpoint() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        return `${protocol}//${window.location.host}`;
    }

    /**
     * Get REST API endpoint
     */
    getRestEndpoint() {
        const protocol = window.location.protocol;
        return `${protocol}//${window.location.host}/api`;
    }

    /**
     * Helper methods for metrics
     */
    getCurrentSessionId() {
        return sessionStorage.getItem('sessionId') || `session_${Date.now()}`;
    }

    getGenerationCount() {
        return this.metrics ? this.metrics.generationCount : 0;
    }

    getAverageResponseTime() {
        if (!this.metrics || this.metrics.responseTimes.length === 0) return 0;
        const sum = this.metrics.responseTimes.reduce((a, b) => a + b, 0);
        return Math.round(sum / this.metrics.responseTimes.length);
    }

    getErrorRate() {
        if (!this.metrics || this.metrics.requests === 0) return 0;
        return Math.round((this.metrics.errors / this.metrics.requests) * 100);
    }

    getScalingEvents() {
        return this.metrics ? this.metrics.scalingEvents : 0;
    }

    getUptime() {
        const startTime = sessionStorage.getItem('appStartTime') || Date.now();
        const uptime = Date.now() - startTime;
        const minutes = Math.floor(uptime / 60000);
        return `${minutes}m`;
    }
}

// Initialize AWS integration when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Store app start time for uptime calculation
    sessionStorage.setItem('appStartTime', Date.now());
    
    // Initialize AWS integration after a short delay
    setTimeout(() => {
        window.awsIntegration = new AWSIntegrationManager();
        console.log('🚀 AWS Integration Manager initialized');
    }, 1500);
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AWSIntegrationManager;
}