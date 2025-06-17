class Dashboard {
    constructor() {
        this.api = window.api;
        this.currentUser = null;
        this.facultyMatches = [];
        this.programMatches = [];
        this.applicationData = {};
        
        this.init();
    }

    async init() {
        try {
            this.showLoading();
            await this.loadDashboardData();
            this.renderDashboard();
        } catch (error) {
            console.error('Dashboard initialization failed:', error);
            this.showError('Failed to load dashboard data');
        } finally {
            this.hideLoading();
        }
    }

    async loadDashboardData() {
        // Load faculty matches
        this.facultyMatches = await this.loadFacultyMatches();
        
        // Load program recommendations  
        this.programMatches = await this.loadProgramRecommendations();
        
        // Load application data
        this.applicationData = await this.loadApplicationData();
        
        // Load research insights
        this.researchInsights = await this.loadResearchInsights();
    }

    async loadFacultyMatches() {
        try {
            // For demo purposes, return mock data
            // In real implementation, this would call the API
            return [
                {
                    id: 1,
                    name: "Dr. Andrew Ng",
                    university: "Stanford University",
                    department: "Computer Science",
                    research_areas: ["Machine Learning", "AI"],
                    hiring_status: "hiring",
                    match_score: 0.94,
                    email: "ang@cs.stanford.edu"
                },
                {
                    id: 2,
                    name: "Dr. Fei-Fei Li", 
                    university: "Stanford University",
                    department: "Computer Science",
                    research_areas: ["Computer Vision", "AI"],
                    hiring_status: "maybe",
                    match_score: 0.91,
                    email: "feifeili@cs.stanford.edu"
                },
                {
                    id: 3,
                    name: "Dr. Yoshua Bengio",
                    university: "University of Montreal", 
                    department: "Computer Science",
                    research_areas: ["Deep Learning", "AI"],
                    hiring_status: "hiring",
                    match_score: 0.89,
                    email: "yoshua.bengio@umontreal.ca"
                }
            ];
        } catch (error) {
            console.error('Error loading faculty matches:', error);
            return [];
        }
    }

    async loadProgramRecommendations() {
        try {
            // Mock data for demo
            return [
                {
                    id: 1,
                    name: "Computer Science PhD",
                    university: "Stanford University",
                    degree_type: "PhD",
                    match_score: 0.95,
                    acceptance_rate: 0.06,
                    ranking: 1
                },
                {
                    id: 2,
                    name: "EECS PhD",
                    university: "MIT",
                    degree_type: "PhD", 
                    match_score: 0.92,
                    acceptance_rate: 0.08,
                    ranking: 2
                }
            ];
        } catch (error) {
            console.error('Error loading program recommendations:', error);
            return [];
        }
    }

    async loadApplicationData() {
        try {
            // Mock application data
            return {
                total: 8,
                submitted: 3,
                in_progress: 2,
                to_start: 3,
                deadlines: [
                    { program: "MIT EECS", deadline: "2024-12-15", days_left: 45, urgent: true },
                    { program: "Stanford CS", deadline: "2024-12-20", days_left: 50, urgent: false },
                    { program: "CMU SCS", deadline: "2025-01-02", days_left: 63, urgent: false }
                ],
                documents: [
                    { name: "Statement of Purpose", status: "complete" },
                    { name: "CV/Resume", status: "complete" },
                    { name: "Transcripts", status: "complete" },
                    { name: "Letters of Recommendation", status: "partial", count: "2/3" },
                    { name: "GRE Scores", status: "missing" }
                ]
            };
        } catch (error) {
            console.error('Error loading application data:', error);
            return {};
        }
    }

    async loadResearchInsights() {
        try {
            return {
                user_interests: ["Machine Learning", "Computer Vision", "Robotics", "NLP"],
                trending_areas: ["Generative AI", "Multimodal Learning", "AI Safety", "Quantum ML"],
                ai_insight: "Consider highlighting your experience with multimodal learning in your personal statement - it's gaining traction at 8 of your target schools."
            };
        } catch (error) {
            console.error('Error loading research insights:', error);
            return {};
        }
    }

    renderDashboard() {
        this.renderFacultyMatches();
        this.renderDeadlines(); 
        this.renderResearchInsights();
        this.renderRankings();
        this.renderDocuments();
        this.updateStats();
    }

    renderFacultyMatches() {
        const container = document.getElementById('facultyList');
        if (!container) return;

        container.innerHTML = '';
        
        this.facultyMatches.slice(0, 5).forEach(faculty => {
            const facultyElement = this.createFacultyElement(faculty);
            container.appendChild(facultyElement);
        });
    }

    createFacultyElement(faculty) {
        const element = document.createElement('div');
        element.className = 'faculty-item';
        
        const initials = faculty.name.split(' ')
            .map(n => n[0])
            .join('')
            .substring(0, 2)
            .toUpperCase();
        
        const statusClass = faculty.hiring_status === 'hiring' ? 'hiring' : 
                           faculty.hiring_status === 'maybe' ? 'maybe' : 'closed';

        element.innerHTML = `
            <div class="faculty-avatar">${initials}</div>
            <div class="faculty-info">
                <h4>${faculty.name}</h4>
                <p>${faculty.university} • ${faculty.research_areas.join(', ')}</p>
            </div>
            <div class="match-score">${Math.round(faculty.match_score * 100)}%</div>
            <div class="hiring-status ${statusClass}"></div>
        `;

        element.addEventListener('click', () => {
            this.showFacultyDetails(faculty);
        });

        return element;
    }

    renderDeadlines() {
        const container = document.getElementById('deadlinesList');
        if (!container || !this.applicationData.deadlines) return;

        container.innerHTML = '';

        this.applicationData.deadlines.forEach(deadline => {
            const element = document.createElement('div');
            element.className = `deadline-item ${deadline.urgent ? 'urgent' : ''}`;
            
            element.innerHTML = `
                <div class="deadline-info">
                    <div class="deadline-program">${deadline.program}</div>
                    <div class="deadline-type">PhD Application</div>
                </div>
                <div class="deadline-date">
                    <div class="date">${this.formatDate(deadline.deadline)}</div>
                    <div class="days-left">${deadline.days_left} days</div>
                </div>
            `;

            container.appendChild(element);
        });
    }

    renderResearchInsights() {
        if (!this.researchInsights) return;

        // Render user interests
        const userInterests = document.getElementById('userInterests');
        if (userInterests && this.researchInsights.user_interests) {
            userInterests.innerHTML = '';
            this.researchInsights.user_interests.forEach(interest => {
                const tag = document.createElement('span');
                tag.className = 'research-tag';
                tag.textContent = interest;
                userInterests.appendChild(tag);
            });
        }

        // Render trending areas
        const trendingAreas = document.getElementById('trendingAreas'); 
        if (trendingAreas && this.researchInsights.trending_areas) {
            trendingAreas.innerHTML = '';
            this.researchInsights.trending_areas.forEach(area => {
                const tag = document.createElement('span');
                tag.className = 'research-tag trending-tag';
                tag.textContent = area;
                trendingAreas.appendChild(tag);
            });
        }

        // Render AI insight
        const aiInsight = document.getElementById('aiInsightText');
        if (aiInsight && this.researchInsights.ai_insight) {
            aiInsight.textContent = this.researchInsights.ai_insight;
        }
    }

    renderRankings() {
        const container = document.getElementById('rankingsList');
        if (!container) return;

        container.innerHTML = '';

        this.programMatches.forEach(program => {
            const element = document.createElement('div');
            element.className = 'ranking-item';
            
            element.innerHTML = `
                <div class="ranking-info">
                    <div class="university-name">${program.university}</div>
                    <div class="program-type">${program.name}</div>
                </div>
                <div class="ranking-stats">
                    <div class="ranking">#${program.ranking}</div>
                    <div class="match">${Math.round(program.match_score * 100)}% Match</div>
                </div>
            `;

            container.appendChild(element);
        });
    }

    renderDocuments() {
        const container = document.getElementById('documentsList');
        if (!container || !this.applicationData.documents) return;

        container.innerHTML = '';

        this.applicationData.documents.forEach(doc => {
            const element = document.createElement('div');
            element.className = 'document-item';
            
            const statusIcon = doc.status === 'complete' ? '✅' :
                              doc.status === 'partial' ? '⚠️' : '❌';
            
            const statusText = doc.status === 'partial' ? doc.count : 
                              doc.status === 'complete' ? 'Complete' : 'Missing';

            element.innerHTML = `
                <span class="document-name">${doc.name}</span>
                <span class="document-status">
                    ${statusIcon} ${statusText}
                </span>
            `;

            container.appendChild(element);
        });
    }

    updateStats() {
        // Update university count
        const universityCount = document.getElementById('universityCount');
        if (universityCount) {
            this.animateNumber(universityCount, 247);
        }

        // Update faculty count  
        const facultyCount = document.getElementById('facultyCount');
        if (facultyCount) {
            this.animateNumber(facultyCount, 1840);
        }

        // Update data freshness
        const dataFreshness = document.getElementById('dataFreshness');
        if (dataFreshness) {
            this.animateNumber(dataFreshness, 94, '%');
        }
    }

    animateNumber(element, target, suffix = '') {
        let current = 0;
        const increment = target / 50;
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            element.textContent = Math.floor(current) + suffix;
        }, 20);
    }

    showFacultyDetails(faculty) {
        // This would open a modal or navigate to faculty details page
        console.log('Show faculty details for:', faculty);
        alert(`Faculty Details:\n\nName: ${faculty.name}\nUniversity: ${faculty.university}\nResearch: ${faculty.research_areas.join(', ')}\nHiring Status: ${faculty.hiring_status}\nMatch Score: ${Math.round(faculty.match_score * 100)}%`);
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric' 
        });
    }

    showLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.add('show');
        }
    }

    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.remove('show');
        }
    }

    showError(message) {
        alert(`Error: ${message}`);
    }
}

// Global functions for quick actions
function quickQuery(query) {
    // Redirect to chat with pre-filled query
    window.location.href = `/chat?q=${encodeURIComponent(query)}`;
}

function handleQuickQuery(event) {
    if (event.key === 'Enter') {
        const input = document.getElementById('quickQueryInput');
        if (input.value.trim()) {
            quickQuery(input.value.trim());
        }
    }
}

async function refreshFacultyMatches() {
    try {
        dashboard.showLoading();
        dashboard.facultyMatches = await dashboard.loadFacultyMatches();
        dashboard.renderFacultyMatches();
    } catch (error) {
        dashboard.showError('Failed to refresh faculty matches');
    } finally {
        dashboard.hideLoading();
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});