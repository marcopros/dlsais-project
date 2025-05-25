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
    
    // Function to extract agent name from metadata
    function extractAgentName(metadata) {
        // Check if we have agent information in the metadata
        if (metadata && metadata.agent) {
            // Extract the agent name from the string (e.g., "Matching Agent")
            const agentName = metadata.agent;
            return agentName.replace(/\s+Agent$/i, '');
        }
        
        // Default to Orchestrator if no specific agent is identified
        return "Orchestrator";
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
            // Retrieve user from localStorage
            const userJson = localStorage.getItem("user");
            let userId = 'Default'; // Default if no user found
            let bodyData = { message }; // Base data

            if (userJson) {
                const user = JSON.parse(userJson);
                userId = user.id;
                bodyData.user_id = userId; // Add user_id only if user exists
            } else {
                console.warn("User not logged in, using default user.");
            }

            // Send request
            const response = await fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(bodyData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            // Read the response as JSON
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error sending message:', error);
            return { 
                text: '[ERROR] Sorry, there was an error processing your request.',
                metadata: {}
            };
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
        
        // Extract agent name from metadata
        const agentName = extractAgentName(response.metadata);
        
        // Add agent response
        addMessage('agent', response.text, agentName);
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