class APIClient {
    constructor() {
        this.baseURL = '/api/v1';
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Chat API
    async sendMessage(message, sessionId = null, context = {}) {
        return this.request('/chat/query', {
            method: 'POST',
            body: JSON.stringify({
                message,
                session_id: sessionId,
                context
            })
        });
    }

    async getChatSessions() {
        return this.request('/chat/sessions');
    }

    // Faculty API
    async getFaculty(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/faculty?${params}`);
    }

    async searchFaculty(searchCriteria) {
        return this.request('/faculty/search', {
            method: 'POST',
            body: JSON.stringify(searchCriteria)
        });
    }

    async getFacultyByResearchArea(researchArea, hiringOnly = false) {
        const params = new URLSearchParams({
            hiring_only: hiringOnly
        });
        return this.request(`/faculty/research/${encodeURIComponent(researchArea)}?${params}`);
    }

    // Programs API
    async getPrograms(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/programs?${params}`);
    }

    async searchPrograms(searchCriteria) {
        return this.request('/programs/search', {
            method: 'POST',
            body: JSON.stringify(searchCriteria)
        });
    }

    async getProgramRecommendations() {
        return this.request('/programs/match/recommendations');
    }

    // Universities API
    async getUniversities(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/universities?${params}`);
    }

    // Utility methods
    async healthCheck() {
        return this.request('/health');
    }
}

// Create global API client instance
const api = new APIClient();

// Export for use in other files
window.api = api;
