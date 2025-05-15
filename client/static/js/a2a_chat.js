document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    
    // Auto-resize textarea
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.scrollHeight > 200) {
            this.style.overflowY = 'auto';
        } else {
            this.style.overflowY = 'hidden';
        }
    });
    
    // Generate a UUID that works across all browsers
    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    // Session ID for this conversation
    const sessionId = generateUUID();
    
    // Get agent avatar based on agent name
    function getAgentAvatar(agentName) {
        // You could replace these with actual agent icons if available
        switch(agentName) {
            case 'Orchestrator':
                return '<div class="avatar agent-avatar">O</div>';
            case 'Diagnosis':
                return '<div class="avatar agent-avatar">D</div>';
            case 'Matching':
                return '<div class="avatar agent-avatar">M</div>';
            case 'Appointment':
                return '<div class="avatar agent-avatar">A</div>';
            case 'Feedback':
                return '<div class="avatar agent-avatar">F</div>';
            default:
                return '<div class="avatar agent-avatar">AI</div>';
        }
    }
    
    // Get user avatar
    function getUserAvatar() {
        return '<div class="avatar user-avatar">U</div>';
    }
    
    // Function to extract agent name from response
    function extractAgentName(response) {
        // First try to find explicit agent labels - look for patterns like [AgentName] or "Agent: AgentName"
        const explicitAgentMatch = response.match(/^\[(.*?)\]|^Agent:\s*(.*?)(?:\s*-|\n|:)|^(Diagnosis|Matching|Appointment|Feedback|Orchestrator):/i);
        
        if (explicitAgentMatch) {
            // Return the first capturing group that has a value
            return explicitAgentMatch[1] || explicitAgentMatch[2] || explicitAgentMatch[3] || "Agent";
        }
        
        // Look for sub-agent mentions in the response
        const subAgentPatterns = [
            { 
                name: "Diagnosis", 
                patterns: [
                    /diagnosis agent/i, 
                    /diagnosi/i, 
                    /diagnostic/i,
                    /diagnose/i,
                    /let me (check|examine|diagnose|identify)/i,
                    /I'll (help|assist) (you with|in) (diagnosing|identifying)/i,
                    /problem (seems to|appears to|might|could) be/i,
                    /based on (your description|what you've described|your explanation)/i
                ]
            },
            { 
                name: "Matching", 
                patterns: [
                    /matching agent/i, 
                    /matching/i, 
                    /find professional/i, 
                    /trovare un professionista/i,
                    /I (can|could|will) (help you|assist you in) (find|finding|locate|locating|connect|matching)/i,
                    /let me (find|match|connect|help you find)/i,
                    /here (are|is) (some|a few|a list of|a|the) (professionals|experts|specialists|recommended|options)/i,
                    /I've found (some|a few|several|the following) professionals/i,
                    /you need a (professional|specialist|expert|plumber|electrician|contractor)/i
                ]
            },
            { 
                name: "Appointment", 
                patterns: [
                    /appointment agent/i, 
                    /appuntamento/i, 
                    /booking/i, 
                    /calendario/i, 
                    /schedule/i
                ]
            },
            { 
                name: "Feedback", 
                patterns: [
                    /feedback agent/i, 
                    /feedback/i, 
                    /review/i, 
                    /recensione/i
                ]
            }
        ];
        
        // Check each sub-agent pattern
        for (const agent of subAgentPatterns) {
            for (const pattern of agent.patterns) {
                if (pattern.test(response)) {
                    return agent.name;
                }
            }
        }
        
        // Enhanced fallback detection based on context clues
        if (/what (kind of|type of) (problem|issue)|describe (the|your) (problem|issue|symptoms)/i.test(response)) {
            return "Diagnosis";
        }
        
        if (/professional|specialist|expert|service provider|technician/i.test(response)) {
            return "Matching";
        }
        
        // Default to "Orchestrator" if no specific agent is identified
        return "Orchestrator";
    }
    
    // Function to extract main text content from response
    function extractMainContent(response) {
        // Remove any JSON or reasoning parts that might be present
        // This is a simplified version - adjust based on actual response format
        
        // Remove agent prefix if present
        let content = response.replace(/^\[(.*?)\]\s*/, '').trim();
        content = content.replace(/^Agent:\s*(.*?)(?:\s*-|\n|:)/i, '').trim();
        
        // Remove any JSON blocks
        content = content.replace(/```json.*?```/gs, '');
        
        // Remove any reasoning sections marked with specific patterns
        content = content.replace(/Reasoning:.*?Result:/gs, 'Result:');
        
        return content.trim();
    }
    
    // Function to add a message to the chat
    function addMessage(role, content, agentName = null) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', role);
        
        let avatar = '';
        if (role === 'agent') {
            avatar = getAgentAvatar(agentName);
        } else {
            avatar = getUserAvatar();
        }
        
        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');
        
        messageContent.innerHTML = avatar;
        
        const chatDetails = document.createElement('div');
        chatDetails.classList.add('message-bubble');
        
        if (role === 'agent' && agentName) {
            const agentLabel = document.createElement('div');
            agentLabel.classList.add('agent-label');
            agentLabel.textContent = agentName;
            agentLabel.setAttribute('data-agent', agentName);
            chatDetails.appendChild(agentLabel);
        }
        
        const textContent = document.createElement('div');
        textContent.textContent = content;
        chatDetails.appendChild(textContent);
        
        messageContent.appendChild(chatDetails);
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to add typing indicator
    function addTypingIndicator() {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'agent', 'typing-indicator');
        
        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');
        
        messageContent.innerHTML = getAgentAvatar('Orchestrator');
        
        const bubble = document.createElement('div');
        bubble.classList.add('message-bubble', 'typing');
        
        // Add the typing dots
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.classList.add('typing-dot');
            bubble.appendChild(dot);
        }
        
        messageContent.appendChild(bubble);
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return messageDiv;
    }
    
    // Function to remove typing indicator
    function removeTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Function to send message to server
    async function sendMessage(message) {
        try {
            const response = await fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            return data.response;
        } catch (error) {
            console.error('Error sending message:', error);
            return 'Sorry, there was an error processing your request.';
        }
    }
    
    // Handle form submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const message = userInput.value.trim();
        if (!message) return;
        
        // Add user message
        addMessage('user', message);
        
        // Clear input and reset height
        userInput.value = '';
        userInput.style.height = 'auto';
        
        // Focus on input
        userInput.focus();
        
        // Show typing indicator
        const typingIndicator = addTypingIndicator();
        
        // Send message to server
        const response = await sendMessage(message);
        
        // Remove typing indicator
        removeTypingIndicator();
        
        // Extract agent name and main content
        const agentName = extractAgentName(response);
        const mainContent = extractMainContent(response);
        
        // Add agent response
        addMessage('agent', mainContent, agentName);
    });
    
    // Handle textarea enter key
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });
    
    // Focus input on page load
    userInput.focus();
    
    // Add welcome message when page loads
    const welcomeMessage = "Hello! I'm your home repair assistant. What problem are you experiencing with your home today?";
    
    // Display the welcome message with a slight delay to make it seem more natural
    setTimeout(() => {
        addMessage('agent', welcomeMessage, 'Orchestrator');
    }, 500);
}); 