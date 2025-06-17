class ChatInterface {
    constructor() {
        this.api = window.api;
        this.sessionId = null;
        this.messages = [];
        this.isTyping = false;
        this.voiceRecording = false;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkURLParams();
        this.focusInput();
    }

    bindEvents() {
        // Input events
        const messageInput = document.getElementById('messageInput');
        messageInput.addEventListener('keydown', (e) => this.handleKeyPress(e));
        messageInput.addEventListener('input', (e) => this.autoResize(e.target));

        // Button events
        document.getElementById('sendBtn').addEventListener('click', () => this.sendMessage());
        document.getElementById('voiceBtn').addEventListener('click', () => this.toggleVoiceInput());
    }

    checkURLParams() {
        // Check if there's a pre-filled query from URL params
        const urlParams = new URLSearchParams(window.location.search);
        const query = urlParams.get('q');
        
        if (query) {
            document.getElementById('messageInput').value = query;
            this.sendMessage();
        }
    }

    focusInput() {
        document.getElementById('messageInput').focus();
    }

    handleKeyPress(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.sendMessage();
        }
    }

    autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    async sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();
        
        if (!message || this.isTyping) return;

        // Clear input and hide suggestions
        input.value = '';
        input.style.height = 'auto';
        this.hideSuggestions();

        // Add user message to chat
        this.addMessage('user', message);
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            // Send message to API
            const response = await this.api.sendMessage(message, this.sessionId);
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add AI response
            this.addMessage('assistant', response.response, {
                facultyMatches: response.faculty_matches,
                programMatches: response.program_matches,
                sources: response.sources
            });
            
            // Update session ID
            this.sessionId = response.session_id;
            
        } catch (error) {
            this.hideTypingIndicator();
            this.addMessage('assistant', 'I apologize, but I encountered an error processing your request. Please try again.');
            console.error('Chat error:', error);
        }
        
        this.focusInput();
    }

    sendQuickMessage(message) {
        document.getElementById('messageInput').value = message;
        this.sendMessage();
    }

    addMessage(role, content, data = {}) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageElement = this.createMessageElement(role, content, data);
        
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        this.messages.push({ role, content, data, timestamp: new Date() });
    }

    createMessageElement(role, content, data = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatar = role === 'user' ? '👤' : '🤖';
        const messageContent = this.formatMessageContent(content, data);
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-text">${messageContent}</div>
                ${data.facultyMatches ? this.createFacultyMatchesWidget(data.facultyMatches) : ''}
                ${data.programMatches ? this.createProgramMatchesWidget(data.programMatches) : ''}
                ${this.createQuickActions(role, content)}
            </div>
        `;
        
        return messageDiv;
    }

    formatMessageContent(content) {
        // Convert markdown-like formatting to HTML
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }

    createFacultyMatchesWidget(facultyMatches) {
        if (!facultyMatches || facultyMatches.length === 0) return '';
        
        const widget = document.createElement('div');
        widget.className = 'data-widget faculty-widget';
        
        widget.innerHTML = `
            <div class="widget-header">
                <span class="widget-icon">👨‍🎓</span>
                <span class="widget-title">Faculty Matches Found</span>
            </div>
            <div class="widget-content">
                ${facultyMatches.slice(0, 3).map(faculty => `
                    <div class="faculty-match-item">
                        <div class="faculty-info">
                            <strong>${faculty.name}</strong><br>
                            <small>${faculty.university} • ${faculty.research_areas.join(', ')}</small>
                        </div>
                        <div class="match-score">${Math.round(faculty.match_score * 100)}%</div>
                    </div>
                `).join('')}
                ${facultyMatches.length > 3 ? `<div class="view-more">+${facultyMatches.length - 3} more matches</div>` : ''}
            </div>
        `;
        
        return widget.outerHTML;
    }

    createProgramMatchesWidget(programMatches) {
        if (!programMatches || programMatches.length === 0) return '';
        
        const widget = document.createElement('div');
        widget.className = 'data-widget program-widget';
        
        widget.innerHTML = `
            <div class="widget-header">
                <span class="widget-icon">🏫</span>
                <span class="widget-title">Program Matches Found</span>
            </div>
            <div class="widget-content">
                ${programMatches.slice(0, 3).map(program => `
                    <div class="program-match-item">
                        <div class="program-info">
                            <strong>${program.name}</strong><br>
                            <small>${program.university} • ${program.degree_type}</small>
                        </div>
                        <div class="match-score">${Math.round(program.match_score * 100)}%</div>
                    </div>
                `).join('')}
                ${programMatches.length > 3 ? `<div class="view-more">+${programMatches.length - 3} more matches</div>` : ''}
            </div>
        `;
        
        return widget.outerHTML;
    }

    createQuickActions(role, content) {
        if (role !== 'assistant') return '';
        
        // Generate contextual quick actions based on the response
        const actions = [];
        
        if (content.toLowerCase().includes('faculty') || content.toLowerCase().includes('professor')) {
            actions.push('Show more faculty details');
            actions.push('Find similar professors');
        }
        
        if (content.toLowerCase().includes('program') || content.toLowerCase().includes('degree')) {
            actions.push('Show program requirements');
            actions.push('Compare with other programs');
        }
        
        if (content.toLowerCase().includes('deadline') || content.toLowerCase().includes('application')) {
            actions.push('Show all deadlines');
            actions.push('Set reminder');
        }
        
        // Always include these general actions
        actions.push('Tell me more');
        actions.push('What should I do next?');
        
        if (actions.length === 0) return '';
        
        return `
            <div class="quick-actions">
                ${actions.slice(0, 4).map(action => `
                    <button class="quick-action" onclick="sendQuickMessage('${action}')">
                        ${action}
                    </button>
                `).join('')}
            </div>
        `;
    }

    showTypingIndicator() {
        this.isTyping = true;
        const messagesContainer = document.getElementById('chatMessages');
        
        const typingTemplate = document.getElementById('typingTemplate');
        const typingElement = typingTemplate.content.cloneNode(true);
        typingElement.querySelector('.message').id = 'typingIndicator';
        
        messagesContainer.appendChild(typingElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    hideTypingIndicator() {
        this.isTyping = false;
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    hideSuggestions() {
        const suggestionsContainer = document.getElementById('suggestionsContainer');
        if (suggestionsContainer && this.messages.length === 0) {
            suggestionsContainer.style.display = 'none';
        }
    }

    toggleVoiceInput() {
        if (!this.voiceRecording) {
            this.startVoiceRecording();
        } else {
            this.stopVoiceRecording();
        }
    }

    startVoiceRecording() {
        // Voice recording implementation would go here
        // This is a simplified version for demo
        this.voiceRecording = true;
        const voiceBtn = document.getElementById('voiceBtn');
        voiceBtn.innerHTML = '⏹️';
        voiceBtn.classList.add('recording');
        
        // Simulate voice recording
        setTimeout(() => {
            this.stopVoiceRecording();
            document.getElementById('messageInput').value = 'What are the application deadlines for Stanford CS PhD program?';
        }, 3000);
    }

    stopVoiceRecording() {
        this.voiceRecording = false;
        const voiceBtn = document.getElementById('voiceBtn');
        voiceBtn.innerHTML = '🎤';
        voiceBtn.classList.remove('recording');
    }
}

// Global functions for template usage
function sendQuickMessage(message) {
    if (window.chatInterface) {
        window.chatInterface.sendQuickMessage(message);
    }
}

function toggleVoiceInput() {
    if (window.chatInterface) {
        window.chatInterface.toggleVoiceInput();
    }
}

function handleKeyPress(event) {
    if (window.chatInterface) {
        window.chatInterface.handleKeyPress(event);
    }
}

function autoResize(textarea) {
    if (window.chatInterface) {
        window.chatInterface.autoResize(textarea);
    }
}

function sendMessage() {
    if (window.chatInterface) {
        window.chatInterface.sendMessage();
    }
}

// Initialize chat interface when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.chatInterface = new ChatInterface();
});