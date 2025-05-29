// Universal Agent Connector JavaScript
class UniversalConnectorUI {
    constructor() {
        this.sessionId = null;
        this.messageCount = 0;
        this.totalResponseTime = 0;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadAgents();
        this.loadTemplates();
        this.loadStats();
        this.createSession();

        // Auto-refresh agents every 30 seconds
        setInterval(() => this.loadAgents(), 30000);
        setInterval(() => this.loadStats(), 10000);
    }

    setupEventListeners() {
        // Chat functionality
        document.getElementById('sendBtn').addEventListener('click', () => this.sendMessage());
        document.getElementById('chatInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });

        // Agent registration
        document.getElementById('registerForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.registerAgent();
        });

        // Connection type change
        document.getElementById('connectionType').addEventListener('change', (e) => {
            this.updateDynamicFields(e.target.value);
        });
    }

    async createSession() {
        try {
            const response = await fetch('/api/chat/session', { method: 'POST' });
            const data = await response.json();
            this.sessionId = data.session_id;
        } catch (error) {
            console.error('Error creating session:', error);
        }
    }

    async sendMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();

        if (!message) return;

        const sendBtn = document.getElementById('sendBtn');
        sendBtn.disabled = true;
        sendBtn.innerHTML = '<div class="loading"></div>';

        // Add user message to chat
        this.addMessage(message, 'user');
        input.value = '';

        try {
            const response = await fetch('/api/mcp/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    command: message,
                    session_id: this.sessionId
                })
            });

            const data = await response.json();

            // Add assistant response
            this.addAssistantMessage(data);

            // Update stats
            this.messageCount++;
            if (data.processing_time_ms) {
                this.totalResponseTime += data.processing_time_ms;
            }
            this.updateMessageStats();

        } catch (error) {
            this.addMessage('Sorry, there was an error processing your request.', 'assistant', 'error');
            console.error('Error sending message:', error);
        } finally {
            sendBtn.disabled = false;
            sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
        }
    }

    addMessage(content, type, status = 'success') {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;

        const time = new Date().toLocaleTimeString();
        const agentInfo = type === 'assistant' && typeof content === 'object' ?
            ` • ${content.agent_used || content.type || 'System'}` : '';

        const messageContent = typeof content === 'object' ?
            this.formatAssistantResponse(content) : content;

        messageDiv.innerHTML = `
            <div>${messageContent}</div>
            <div class="message-meta">${type === 'user' ? 'You' : 'Assistant'}${agentInfo} • ${time}</div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    addAssistantMessage(data) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message';

        const time = new Date().toLocaleTimeString();
        const agentUsed = data.agent_used || data.type || 'System';
        const processingTime = data.processing_time_ms ? ` • ${data.processing_time_ms}ms` : '';

        messageDiv.innerHTML = `
            <div>${this.formatAssistantResponse(data)}</div>
            <div class="message-meta">Assistant • ${agentUsed}${processingTime} • ${time}</div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    formatAssistantResponse(data) {
        if (data.type === 'weather') {
            const current = data.current || {};
            return `
                <div><strong>🌤️ Weather in ${data.location}</strong></div>
                <div>🌡️ Temperature: ${current.temperature || 'N/A'}</div>
                <div>☁️ Condition: ${current.condition || 'N/A'}</div>
                <div>💧 Humidity: ${current.humidity || 'N/A'}</div>
                ${current.wind_speed ? `<div>💨 Wind: ${current.wind_speed}</div>` : ''}
            `;
        } else if (data.type === 'search') {
            return `
                <div><strong>🔍 Search Results</strong></div>
                <div>Found ${data.results_count || 0} results for "${data.query || 'your search'}"</div>
                ${data.summary ? `<div>${data.summary}</div>` : ''}
            `;
        } else if (data.type === 'external_agent') {
            const result = data.result || {};
            return `
                <div><strong>🔌 External Agent Response</strong></div>
                <div>Agent: ${data.agent_used}</div>
                <div>Result: ${JSON.stringify(result, null, 2)}</div>
                ${data.routing_info ? `<div><small>Confidence: ${(data.routing_info.routing_confidence * 100).toFixed(1)}%</small></div>` : ''}
            `;
        } else if (data.type === 'document_analysis') {
            return `
                <div><strong>📄 Document Analysis</strong></div>
                <div>${data.analysis || 'Document processed successfully'}</div>
                ${data.word_count ? `<div>📊 ${data.word_count}</div>` : ''}
            `;
        } else if (data.type === 'error') {
            return `
                <div style="color: #dc3545;"><strong>❌ Error</strong></div>
                <div>${data.message || 'An error occurred'}</div>
            `;
        } else {
            return data.summary || data.message || JSON.stringify(data, null, 2);
        }
    }

    async loadAgents() {
        try {
            const response = await fetch('/api/agents/connected');
            const data = await response.json();

            this.renderAgents(data.connected_agents || {});

            // Update connected agents count
            document.getElementById('connectedAgents').textContent = data.total_count || 0;

        } catch (error) {
            console.error('Error loading agents:', error);
            document.getElementById('agentsList').innerHTML = `
                <div style="text-align: center; color: #dc3545; padding: 20px;">
                    <i class="fas fa-exclamation-triangle"></i>
                    <div style="margin-top: 10px;">Error loading agents</div>
                </div>
            `;
        }
    }

    renderAgents(agents) {
        const agentsList = document.getElementById('agentsList');

        if (Object.keys(agents).length === 0) {
            agentsList.innerHTML = `
                <div style="text-align: center; color: #666; padding: 20px;">
                    <i class="fas fa-plug" style="font-size: 2rem; margin-bottom: 10px; opacity: 0.3;"></i>
                    <div>No agents connected</div>
                    <div style="font-size: 0.9rem; margin-top: 5px;">Register an agent below to get started</div>
                </div>
            `;
            return;
        }

        agentsList.innerHTML = Object.entries(agents).map(([agentId, info]) => `
            <div class="agent-item">
                <div class="agent-info">
                    <h4>${agentId}</h4>
                    <p><i class="fas fa-cog"></i> ${info.connection_type}</p>
                    <p><i class="fas fa-tags"></i> ${(info.capabilities?.keywords || []).join(', ') || 'No keywords'}</p>
                </div>
                <div class="agent-status">
                    <span class="status-badge ${info.status === 'connected' ? 'status-connected' : 'status-disconnected'}">
                        ${info.status}
                    </span>
                    <div class="agent-actions">
                        <button class="btn-small btn-disable" onclick="ui.disableAgent('${agentId}')">
                            <i class="fas fa-pause"></i>
                        </button>
                        <button class="btn-small btn-remove" onclick="ui.removeAgent('${agentId}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async loadTemplates() {
        try {
            const response = await fetch('/api/agents/templates');
            const data = await response.json();

            this.renderTemplates(data.templates || {});

        } catch (error) {
            console.error('Error loading templates:', error);
        }
    }

    renderTemplates(templates) {
        const templatesGrid = document.getElementById('templatesGrid');

        templatesGrid.innerHTML = Object.entries(templates).map(([type, template]) => `
            <div class="template-card" onclick="ui.useTemplate('${type}')">
                <h4><i class="fas fa-${this.getTemplateIcon(type)}"></i> ${this.getTemplateTitle(type)}</h4>
                <p>${template.description || `Template for ${type} agents`}</p>
            </div>
        `).join('');
    }

    getTemplateIcon(type) {
        const icons = {
            'http_api': 'globe',
            'python_module': 'code',
            'function_call': 'function',
            'websocket': 'bolt',
            'grpc': 'server'
        };
        return icons[type] || 'cog';
    }

    getTemplateTitle(type) {
        const titles = {
            'http_api': 'HTTP API Agent',
            'python_module': 'Python Module',
            'function_call': 'Function Call',
            'websocket': 'WebSocket Agent',
            'grpc': 'gRPC Agent'
        };
        return titles[type] || type;
    }

    useTemplate(type) {
        const templates = {
            'http_api': {
                connectionType: 'http_api',
                agentId: 'my_api_agent',
                agentName: 'My API Agent',
                description: 'Agent accessible via HTTP API',
                keywords: 'api, external, service',
                endpoint: 'http://localhost:8001'
            },
            'python_module': {
                connectionType: 'python_module',
                agentId: 'my_python_agent',
                agentName: 'My Python Agent',
                description: 'Agent implemented as Python module',
                keywords: 'python, local, module',
                modulePath: 'my_agents.my_agent',
                className: 'MyAgent'
            },
            'function_call': {
                connectionType: 'function_call',
                agentId: 'my_function_agent',
                agentName: 'My Function Agent',
                description: 'Agent implemented as a function',
                keywords: 'function, simple, quick',
                modulePath: 'my_agents.functions',
                functionName: 'process_request'
            }
        };

        const template = templates[type];
        if (template) {
            // Fill form with template data
            Object.entries(template).forEach(([key, value]) => {
                const element = document.getElementById(key);
                if (element) {
                    element.value = value;
                }
            });

            // Update dynamic fields
            this.updateDynamicFields(template.connectionType);

            this.showNotification('Template loaded! Modify the fields as needed.', 'info');
        }
    }

    updateDynamicFields(connectionType) {
        const dynamicFields = document.getElementById('dynamicFields');

        let fieldsHTML = '';

        switch (connectionType) {
            case 'http_api':
                fieldsHTML = `
                    <div class="form-group">
                        <label for="endpoint">API Endpoint</label>
                        <input type="url" id="endpoint" name="endpoint" placeholder="http://localhost:8001" required>
                    </div>
                    <div class="form-group">
                        <label for="headers">Headers (JSON)</label>
                        <textarea id="headers" name="headers" rows="2" placeholder='{"Content-Type": "application/json"}'></textarea>
                    </div>
                `;
                break;
            case 'python_module':
                fieldsHTML = `
                    <div class="form-group">
                        <label for="modulePath">Module Path</label>
                        <input type="text" id="modulePath" name="modulePath" placeholder="my_agents.my_agent" required>
                    </div>
                    <div class="form-group">
                        <label for="className">Class Name</label>
                        <input type="text" id="className" name="className" placeholder="MyAgent" required>
                    </div>
                `;
                break;
            case 'function_call':
                fieldsHTML = `
                    <div class="form-group">
                        <label for="modulePath">Module Path</label>
                        <input type="text" id="modulePath" name="modulePath" placeholder="my_agents.functions" required>
                    </div>
                    <div class="form-group">
                        <label for="functionName">Function Name</label>
                        <input type="text" id="functionName" name="functionName" placeholder="process_request" required>
                    </div>
                `;
                break;
            case 'websocket':
                fieldsHTML = `
                    <div class="form-group">
                        <label for="websocketUrl">WebSocket URL</label>
                        <input type="url" id="websocketUrl" name="websocketUrl" placeholder="ws://localhost:8002/ws" required>
                    </div>
                `;
                break;
            case 'grpc':
                fieldsHTML = `
                    <div class="form-group">
                        <label for="grpcEndpoint">gRPC Endpoint</label>
                        <input type="text" id="grpcEndpoint" name="grpcEndpoint" placeholder="localhost:50051" required>
                    </div>
                    <div class="form-group">
                        <label for="service">Service Name</label>
                        <input type="text" id="service" name="service" placeholder="AgentService">
                    </div>
                `;
                break;
        }

        dynamicFields.innerHTML = fieldsHTML;
    }

    async registerAgent() {
        const form = document.getElementById('registerForm');
        const formData = new FormData(form);

        // Build agent configuration
        const config = {
            id: formData.get('agentId'),
            name: formData.get('agentName'),
            description: formData.get('description') || '',
            connection_type: formData.get('connectionType'),
            keywords: formData.get('keywords') ? formData.get('keywords').split(',').map(k => k.trim()) : [],
            enabled: true
        };

        // Add connection-specific fields
        switch (config.connection_type) {
            case 'http_api':
                config.endpoint = formData.get('endpoint');
                const headers = formData.get('headers');
                if (headers) {
                    try {
                        config.headers = JSON.parse(headers);
                    } catch (e) {
                        config.headers = { "Content-Type": "application/json" };
                    }
                }
                break;
            case 'python_module':
                config.module_path = formData.get('modulePath');
                config.class_name = formData.get('className');
                break;
            case 'function_call':
                config.module_path = formData.get('modulePath');
                config.function_name = formData.get('functionName');
                break;
            case 'websocket':
                config.websocket_url = formData.get('websocketUrl');
                break;
            case 'grpc':
                config.grpc_endpoint = formData.get('grpcEndpoint');
                config.service = formData.get('service');
                break;
        }

        try {
            const response = await fetch('/api/agents/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification(`Agent "${config.name}" registered successfully!`, 'success');
                form.reset();
                document.getElementById('dynamicFields').innerHTML = '';
                this.loadAgents();
                this.loadStats();
            } else {
                this.showNotification(`Error: ${result.detail || 'Failed to register agent'}`, 'error');
            }

        } catch (error) {
            console.error('Error registering agent:', error);
            this.showNotification('Error registering agent. Please try again.', 'error');
        }
    }

    async disableAgent(agentId) {
        try {
            const response = await fetch(`/api/agents/${agentId}/disable`, { method: 'POST' });
            const result = await response.json();

            if (response.ok) {
                this.showNotification(`Agent "${agentId}" disabled`, 'info');
                this.loadAgents();
            } else {
                this.showNotification(`Error disabling agent: ${result.detail}`, 'error');
            }

        } catch (error) {
            console.error('Error disabling agent:', error);
            this.showNotification('Error disabling agent', 'error');
        }
    }

    async removeAgent(agentId) {
        if (!confirm(`Are you sure you want to remove agent "${agentId}"?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/agents/${agentId}`, { method: 'DELETE' });
            const result = await response.json();

            if (response.ok) {
                this.showNotification(`Agent "${agentId}" removed`, 'success');
                this.loadAgents();
                this.loadStats();
            } else {
                this.showNotification(`Error removing agent: ${result.detail}`, 'error');
            }

        } catch (error) {
            console.error('Error removing agent:', error);
            this.showNotification('Error removing agent', 'error');
        }
    }

    async loadStats() {
        try {
            // Load agent registry stats
            const registryResponse = await fetch('/api/agents/registry');
            const registryData = await registryResponse.json();

            document.getElementById('totalAgents').textContent = registryData.total_count || 0;

            // Update message stats
            this.updateMessageStats();

        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    updateMessageStats() {
        document.getElementById('totalMessages').textContent = this.messageCount;

        const avgTime = this.messageCount > 0 ?
            Math.round(this.totalResponseTime / this.messageCount) : 0;
        document.getElementById('avgResponseTime').textContent = `${avgTime}ms`;
    }

    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        notification.textContent = message;
        notification.className = `notification ${type}`;
        notification.classList.add('show');

        setTimeout(() => {
            notification.classList.remove('show');
        }, 4000);
    }
}

// Initialize the UI when the page loads
let ui;
document.addEventListener('DOMContentLoaded', () => {
    ui = new UniversalConnectorUI();
});
