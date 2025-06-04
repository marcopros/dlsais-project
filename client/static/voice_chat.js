// Voice-enabled chat functionality for Home Repair Assistant

document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    
    // Voice functionality elements
    const voiceInputBtn = document.getElementById('voice-input-btn');
    const speakerToggleBtn = document.getElementById('speaker-toggle-btn');
    const voiceStatus = document.getElementById('voice-status');
    const micIcon = document.getElementById('mic-icon');
    const micRecordingIcon = document.getElementById('mic-recording-icon');
    const speakerOnIcon = document.getElementById('speaker-on-icon');
    const speakerOffIcon = document.getElementById('speaker-off-icon');
    
    // Voice settings
    let isListening = false;
    let speechEnabled = false; // Start with speech disabled
    let recognition = null;
    let speechSynthesis = window.speechSynthesis;
    
    // Initialize speech recognition
    function initSpeechRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';
            
            recognition.onstart = () => {
                isListening = true;
                updateVoiceUI();
                voiceStatus.classList.remove('hidden');
            };
            
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                userInput.value = transcript;
                userInput.style.height = 'auto';
                userInput.style.height = userInput.scrollHeight + 'px';
            };
            
            recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                stopListening();
                if (event.error === 'no-speech') {
                    showTemporaryMessage('No speech detected. Please try again.');
                } else if (event.error === 'not-allowed') {
                    showTemporaryMessage('Microphone access denied. Please allow microphone access.');
                }
            };
            
            recognition.onend = () => {
                stopListening();
            };
        } else {
            console.warn('Speech recognition not supported in this browser');
            voiceInputBtn.style.display = 'none';
        }
    }
    
    // Text-to-speech function
    function speakText(text) {
        if (!speechEnabled || !speechSynthesis) return;
        
        // Cancel any ongoing speech
        speechSynthesis.cancel();
        
        // Clean text for speech (remove markdown-like formatting)
        const cleanText = text
            .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold markdown
            .replace(/\*(.*?)\*/g, '$1')     // Remove italic markdown
            .replace(/```[\s\S]*?```/g, '[code block]') // Replace code blocks
            .replace(/`(.*?)`/g, '$1')       // Remove inline code
            .replace(/#{1,6}\s*/g, '')       // Remove headers
            .replace(/\[(.*?)\]\(.*?\)/g, '$1') // Remove links
            .trim();
        
        if (cleanText.length > 0) {
            const utterance = new SpeechSynthesisUtterance(cleanText);
            utterance.rate = 0.85; // Slightly slower for better clarity
            utterance.pitch = 1.0;
            utterance.volume = 0.9;
            
            // Try to use a more natural voice with better priority order
            const voices = speechSynthesis.getVoices();
            
            // Priority order for natural voices
            const preferredVoiceNames = [
                'Google UK English Female',
                'Google US English',
                 'Microsoft Zira - English (United States)',
                'Microsoft David - English (United States)', 
                 'Alex',
                'Samantha',
                'Karen',
                'Daniel'
            ];
            
            let selectedVoice = null;
            
            // First try to find voices by specific names
            for (const voiceName of preferredVoiceNames) {
                selectedVoice = voices.find(voice => voice.name.includes(voiceName));
                if (selectedVoice) break;
            }
            
            // If no specific voice found, try to find natural voices
            if (!selectedVoice) {
                selectedVoice = voices.find(voice => 
                    voice.lang.startsWith('en') && (
                        voice.name.toLowerCase().includes('natural') ||
                        voice.name.toLowerCase().includes('neural') ||
                        voice.name.toLowerCase().includes('premium') ||
                        voice.name.toLowerCase().includes('female') ||
                        voice.name.toLowerCase().includes('google') ||
                        voice.name.toLowerCase().includes('microsoft')
                    )
                );
            }
            
            // Fallback to any English voice
            if (!selectedVoice) {
                selectedVoice = voices.find(voice => voice.lang.startsWith('en'));
            }
            
            if (selectedVoice) {
                utterance.voice = selectedVoice;
            }
            
            speechSynthesis.speak(utterance);
        }
    }
    
    // Update voice UI
    function updateVoiceUI() {
        if (isListening) {
            micIcon.classList.add('hidden');
            micRecordingIcon.classList.remove('hidden');
            voiceInputBtn.classList.add('bg-red-500', 'text-white');
            voiceInputBtn.classList.remove('bg-white/20');
        } else {
            micIcon.classList.remove('hidden');
            micRecordingIcon.classList.add('hidden');
            voiceInputBtn.classList.remove('bg-red-500', 'text-white');
            voiceInputBtn.classList.add('bg-white/20');
            voiceStatus.classList.add('hidden');
        }
        
        if (speechEnabled) {
            speakerOnIcon.classList.remove('hidden');
            speakerOffIcon.classList.add('hidden');
            speakerToggleBtn.classList.remove('text-gray-400');
        } else {
            speakerOnIcon.classList.add('hidden');
            speakerOffIcon.classList.remove('hidden');
            speakerToggleBtn.classList.add('text-gray-400');
        }
    }
    
    // Start listening
    function startListening() {
        if (recognition && !isListening) {
            recognition.start();
        }
    }
    
    // Stop listening
    function stopListening() {
        if (recognition && isListening) {
            recognition.stop();
        }
        isListening = false;
        updateVoiceUI();
    }
    
    // Show temporary message
    function showTemporaryMessage(message) {
        const tempDiv = document.createElement('div');
        tempDiv.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        tempDiv.textContent = message;
        document.body.appendChild(tempDiv);
        
        setTimeout(() => {
            if (tempDiv.parentNode) {
                tempDiv.parentNode.removeChild(tempDiv);
            }
        }, 3000);
    }
    
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
    
    // Voice input button click
    voiceInputBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (isListening) {
            stopListening();
        } else {
            startListening();
        }
    });
    
    // Speaker toggle button click
    speakerToggleBtn.addEventListener('click', (e) => {
        e.preventDefault();
        speechEnabled = !speechEnabled;
        updateVoiceUI();
        
        if (!speechEnabled) {
            speechSynthesis.cancel();
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
        switch(agentName) {
            case 'Orchestrator':
                return '<div class="avatar agent-avatar bg-blue-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">O</div>';
            case 'Diagnosis':
                return '<div class="avatar agent-avatar bg-green-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">D</div>';
            case 'Matching':
                return '<div class="avatar agent-avatar bg-purple-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">M</div>';
            case 'Appointment':
                return '<div class="avatar agent-avatar bg-orange-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">A</div>';
            case 'Feedback':
                return '<div class="avatar agent-avatar bg-pink-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">F</div>';
            default:
                return '<div class="avatar agent-avatar bg-gray-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">AI</div>';
        }
    }
    
    // Get user avatar
    function getUserAvatar() {
        return '<div class="avatar user-avatar bg-blue-500 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">U</div>';
    }
    
    // Function to extract agent name from metadata
    function extractAgentName(metadata) {
        if (metadata && metadata.agent) {
            const agentName = metadata.agent;
            return agentName.replace(/\s+Agent$/i, '');
        }
        return "Orchestrator";
    }

    // Function to render star rating based on trust score
    function renderStarRating(rating, size = 'text-base') {
        const roundedRating = Math.round(Math.max(0, Math.min(5, rating || 0)));
        const maxStars = 5;
        let starsHtml = '';
        
        for (let i = 1; i <= maxStars; i++) {
            if (i <= roundedRating) {
                starsHtml += `<span class="text-yellow-400 ${size}">★</span>`;
            } else {
                starsHtml += `<span class="text-gray-300 ${size}">★</span>`;
            }
        }
        
        return starsHtml;
    }
    
    // Function to render professional cards
    function renderProfessionalCards(professionals) {
        if (!professionals || !Array.isArray(professionals) || professionals.length === 0) {
            return null;
        }

        const cardsHtml = professionals.map(professional => {
            const {
                name = 'Unknown Professional',
                motivation = '',
                skills = [],
                rating = 0,
                trust_score = rating || 0,
                city = '',
                location = {},
                _id = '',
                trusted_by_you = false,
                trusted_by = []
            } = professional;

            // Handle location field variations
            const professionalCity = city || (location && location.city) || '';
            
            // Handle skills array or string
            let skillsText = '';
            if (Array.isArray(skills)) {
                skillsText = skills.slice(0, 3).join(', ');
            } else if (typeof skills === 'string') {
                skillsText = skills;
            }
            
            const trustNetworkCount = Array.isArray(trusted_by) ? trusted_by.length : 0;
            const displayRating = trust_score || rating || 0;

            return `
                <div class="bg-white/15 backdrop-blur-sm rounded-xl p-4 mb-3 border border-white/20 hover:bg-white/20 transition-all duration-200 cursor-pointer professional-card" data-professional-id="${_id}">
                    <div class="flex items-start justify-between mb-3">
                        <div class="flex-1">
                            <h4 class="text-white font-semibold text-lg mb-1">${name}</h4>
                            <div class="flex items-center gap-2 mb-1">
                                <div class="flex items-center gap-0">
                                    ${renderStarRating(displayRating, 'text-sm')}
                                </div>
                                <span class="text-white/70 text-sm">(${displayRating.toFixed(1)})</span>
                            </div>
                            ${professionalCity ? `<p class="text-white/60 text-sm mb-2">📍 ${professionalCity}</p>` : ''}
                        </div>
                        ${trusted_by_you ? '<div class="bg-green-500/20 text-green-300 px-2 py-1 rounded-full text-xs font-medium trust-badge">Trusted by you</div>' : ''}
                    </div>
                    
                    ${skillsText ? `<p class="text-white/80 text-sm mb-2"><span class="text-white/60">Skills:</span> ${skillsText}</p>` : ''}
                    
                    ${motivation ? `<p class="text-white/70 text-sm mb-3 italic">"${motivation}"</p>` : ''}
                    
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-3 text-xs text-white/60">
                            ${trustNetworkCount > 0 ? `<span>🤝 ${trustNetworkCount} mutual connections</span>` : ''}
                        </div>
                        <button class="bg-accent hover:bg-orange-400 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors contact-professional" data-professional-id="${_id}" data-professional-name="${name}">
                            Contact
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        return `
            <div class="professional-listings">
                <div class="text-white/90 font-medium mb-3">👷‍♂️ Recommended Professionals:</div>
                ${cardsHtml}
            </div>
        `;
    }

    // Function to check if content contains professional data
    function containsProfessionalData(metadata) {
        console.log('Checking metadata for professionals:', metadata);
        
        // Check direct professional data
        const hasProfessionals = metadata && metadata.professionals && Array.isArray(metadata.professionals) && metadata.professionals.length > 0;
        
        // Check professional data in metadata.data (backup file structure)
        const hasDataProfessionals = metadata && metadata.data && metadata.data.professionals && Array.isArray(metadata.data.professionals) && metadata.data.professionals.length > 0;
        
        if (hasProfessionals) {
            console.log('Professional data found in metadata.professionals:', metadata.professionals);
        }
        
        if (hasDataProfessionals) {
            console.log('Professional data found in metadata.data.professionals:', metadata.data.professionals);
        }
        
        return hasProfessionals || hasDataProfessionals;
    }

    // Function to get professional data from metadata
    function getProfessionalData(metadata) {
        if (metadata && metadata.professionals && Array.isArray(metadata.professionals)) {
            return metadata.professionals;
        }
        if (metadata && metadata.data && metadata.data.professionals && Array.isArray(metadata.data.professionals)) {
            return metadata.data.professionals;
        }
        return [];
    }

    function renderYouTubeCards(videoUrls) {
        if (!Array.isArray(videoUrls)) return null;

        const youtubeContainer = document.createElement('div');
        youtubeContainer.className = 'mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4';

        videoUrls.forEach(async (videoUrl) => {
            const trimmedUrl = videoUrl.trim();
            let videoId;

            try {
                const urlObj = new URL(trimmedUrl);
                videoId = urlObj.searchParams.get('v') || trimmedUrl.split('v=')[1]?.split(/[&/]/)[0];
            } catch (err) {
                console.warn('Invalid YouTube URL:', trimmedUrl);
                return;
            }

            try {
                const res = await fetch(`https://www.youtube.com/oembed?url=${encodeURIComponent(trimmedUrl)}&format=json`);
                if (!res.ok) throw new Error('Failed to fetch oEmbed data');
                const data = await res.json();

                const card = document.createElement('div');
                card.className = 'border border-gray-200 rounded-xl overflow-hidden bg-white shadow hover:shadow-lg transition-shadow duration-300';
                card.innerHTML = `
                    <div class="relative pb-[56.25%] h-0 overflow-hidden">
                        <img src="${data.thumbnail_url}" alt="Thumbnail for ${data.title}" class="absolute top-0 left-0 w-full h-full object-cover" />
                    </div>
                    <div class="p-3">
                        <h3 class="text-sm font-medium text-gray-800 truncate">${data.title}</h3>
                        <p class="text-xs text-gray-500 mt-1">Watch this helpful guide on YouTube 🎥</p>
                        <a href="${trimmedUrl}" target="_blank" class="mt-2 inline-block text-xs text-blue-500 hover:underline">Open on YouTube</a>
                    </div>
                `;

                youtubeContainer.appendChild(card);
            } catch (err) {
                console.error('Error fetching YouTube video info:', err);
            }
        });

        return youtubeContainer;
    }

    
    // Function to add a message to the chat
    function addMessage(role, content, agentName = null, metadata = null) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('flex', 'mb-4', role === 'user' ? 'justify-end' : 'justify-start');
        
        const messageContent = document.createElement('div');
        messageContent.classList.add('flex', 'max-w-md', 'lg:max-w-2xl', 'px-4', 'py-2', 'rounded-lg', 'items-start', 'gap-2');        
        if (role === 'user') {
            messageContent.classList.add('bg-white', 'text-gray-800', 'order-1');
            messageContent.innerHTML = `
                <div class="text-sm">${content}</div>
                ${getUserAvatar()}
            `;
        } else {
            messageContent.classList.add('bg-white/20', 'text-white', 'backdrop-blur-sm');
            
            let agentLabel = '';
            if (agentName) {
                agentLabel = `<div class="text-xs text-white/80 font-semibold mb-1">${agentName} Agent</div>`;
            }

            // Check if we have professional data to display
            let professionalCardsHtml = '';
            if (containsProfessionalData(metadata)) {
                const professionals = getProfessionalData(metadata);
                professionalCardsHtml = renderProfessionalCards(professionals);
                // Adjust max width for professional cards
                messageContent.classList.remove('max-w-xs', 'lg:max-w-md');
                messageContent.classList.add('max-w-md', 'lg:max-w-2xl');
            }
            
            messageContent.innerHTML = `
                ${getAgentAvatar(agentName)}
                <div class="flex-1">
                    ${agentLabel}
                    <div class="text-sm mb-3">${content}</div>
                    ${professionalCardsHtml || ''}
                </div>
            `;

            // Check for DIY YouTube videos
            const diyList = metadata?.diy_list || metadata?.data?.diy_list;
            if (Array.isArray(diyList)) {
                const youtubeCards = renderYouTubeCards(diyList);
                if (youtubeCards) {
                    const container = messageContent.querySelector('.flex-1');
                    container.appendChild(youtubeCards);
                }
            }


            
            // Speak the agent response if speech is enabled
            if (speechEnabled && content) {
                setTimeout(() => speakText(content), 500);
            }
        }
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Add event listeners for professional cards if they exist
        // if (containsProfessionalData(metadata)) {
        //     addProfessionalCardEventListeners(messageDiv);
        // }
    }
    
    // Function to add event listeners to professional cards
    function addProfessionalCardEventListeners(messageDiv) {
        const contactButtons = messageDiv.querySelectorAll('.contact-professional');
        const professionalCards = messageDiv.querySelectorAll('.professional-card');

        contactButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const professionalId = button.getAttribute('data-professional-id');
                const professionalName = button.getAttribute('data-professional-name');
                handleContactProfessional(professionalId, professionalName);
            });
        });

        professionalCards.forEach(card => {
            card.addEventListener('click', (e) => {
                // Don't trigger if clicking the contact button
                if (e.target.classList.contains('contact-professional')) return;
                
                const professionalId = card.getAttribute('data-professional-id');
                if (professionalId) {
                    // Add a subtle visual feedback
                    card.classList.add('ring-2', 'ring-white/30');
                    setTimeout(() => {
                        card.classList.remove('ring-2', 'ring-white/30');
                    }, 200);
                }
            });
        });
    }

    // Function to handle contacting a professional
    function handleContactProfessional(professionalId, professionalName) {
        console.log(`Contacting professional: ${professionalName} (ID: ${professionalId})`);
        
        // Add the professional selection message to chat
        addMessage('user', `I'd like to contact ${professionalName}`);
        
        // Send the selection to the backend
        setTimeout(() => {
            sendMessage(`I want to work with ${professionalName} (ID: ${professionalId})`);
        }, 500);
    }
    async function sendMessage(message) {
        if (!message.trim()) return;
        
        // Add user message to chat
        addMessage('user', message);
        
        // Clear input
        userInput.value = '';
        userInput.style.height = 'auto';
        
        // Show typing indicator
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.classList.add('flex', 'justify-start', 'mb-4');
        typingDiv.innerHTML = `
            <div class="flex max-w-xs lg:max-w-md px-4 py-2 rounded-lg bg-white/20 text-white backdrop-blur-sm items-center gap-2">
                <div class="bg-gray-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">AI</div>
                <div class="flex gap-1">
                    <div class="w-2 h-2 bg-white/60 rounded-full animate-bounce"></div>
                    <div class="w-2 h-2 bg-white/60 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                    <div class="w-2 h-2 bg-white/60 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                </div>
            </div>
        `;
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        try {
            const response = await fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    user_id: localStorage.getItem('user_id') || '68337647a96af0b281857c35'
                })
            });
            
            const data = await response.json();
            
            // Remove typing indicator
            const typingIndicator = document.getElementById('typing-indicator');
            if (typingIndicator) {
                typingIndicator.remove();
            }
            
            if (data.response) {
                console.log('Full response data:', data);
                console.log('Response object:', data.response);
                
                let responseText = '';
                let agentName = null;
                let metadata = null;
                
                if (typeof data.response === 'object') {
                    responseText = data.response.text || JSON.stringify(data.response);
                    agentName = extractAgentName(data.response.metadata);
                    metadata = data.response.metadata;
                    console.log('Extracted metadata:', metadata);
                } else {
                    responseText = data.response;
                }
                
                addMessage('agent', responseText, agentName, metadata);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            
            // Remove typing indicator
            const typingIndicator = document.getElementById('typing-indicator');
            if (typingIndicator) {
                typingIndicator.remove();
            }
            
            addMessage('agent', 'Sorry, there was an error processing your request. Please try again.');
        }
    }
    
    // Form submission
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        if (message) {
            sendMessage(message);
        }
    });
    
    // Enter key handling
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const message = userInput.value.trim();
            if (message) {
                sendMessage(message);
            }
        }
    });
    
    // Initialize everything
    initSpeechRecognition();
    updateVoiceUI();
    
    // Sidebar functionality
    const sidebar = document.getElementById('sidebar');
    const openSidebarBtn = document.getElementById('open-sidebar');
    const closeSidebarBtn = document.getElementById('close-sidebar');
    const chatWrapper = document.getElementById('chat-wrapper');
    const appointmentsList = document.getElementById('appointments-list');
    
    // Initialize sidebar state based on screen size
    function initializeSidebar() {
        if (window.innerWidth >= 1024) {
            // On large screens, sidebar should be open by default
            sidebar.classList.remove('-translate-x-full');
            chatWrapper.classList.add('lg:pl-64');
        } else {
            // On smaller screens, sidebar should be closed by default
            sidebar.classList.add('-translate-x-full');
            chatWrapper.classList.remove('lg:pl-64');
        }
    }
    
    // Sidebar toggle functions
    function openSidebar() {
        sidebar.classList.remove('-translate-x-full');
        chatWrapper.classList.add('lg:pl-64');
    }
    
    function closeSidebar() {
        sidebar.classList.add('-translate-x-full');
        chatWrapper.classList.remove('lg:pl-64');
    }
    
    // Event listeners for sidebar
    if (openSidebarBtn) {
        openSidebarBtn.addEventListener('click', openSidebar);
    }
    
    if (closeSidebarBtn) {
        closeSidebarBtn.addEventListener('click', closeSidebar);
    }
    
    // Initialize sidebar state
    initializeSidebar();
    
    // Handle window resize
    window.addEventListener('resize', () => {
        if (window.innerWidth >= 1024) {
            // On large screens, ensure sidebar behavior is correct
            if (sidebar.classList.contains('-translate-x-full')) {
                // If sidebar is hidden, remove the padding
                chatWrapper.classList.remove('lg:pl-64');
            } else {
                // If sidebar is visible, add the padding
                chatWrapper.classList.add('lg:pl-64');
            }
        } else {
            // On smaller screens, always remove padding (sidebar overlays)
            chatWrapper.classList.remove('lg:pl-64');
        }
    });
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
        if (window.innerWidth < 1024 && 
            !sidebar.contains(e.target) && 
            !openSidebarBtn.contains(e.target) &&
            !sidebar.classList.contains('-translate-x-full')) {
            closeSidebar();
        }
    });
    
    // Load appointments
    async function loadAppointments() {
        try {
            const response = await fetch('/appointments');
            const appointments = await response.json();
            const parsedAppointments = JSON.parse(appointments);
            
            if (appointmentsList) {
                appointmentsList.innerHTML = '';
                
                if (parsedAppointments.length === 0) {
                    appointmentsList.innerHTML = '<div class="text-white/60 text-center">No appointments found</div>';
                    return;
                }
                
                parsedAppointments.forEach(appointment => {
                    const appointmentDiv = document.createElement('div');
                    appointmentDiv.className = 'bg-white/10 p-3 rounded-lg backdrop-blur-sm border border-white/20';
                    
                    const statusColor = appointment.status === 'confirmed' ? 'text-green-400' : 
                                       appointment.status === 'pending' ? 'text-yellow-400' : 
                                       appointment.status === 'job_completed' ? 'text-blue-400' :
                                       appointment.status === 'terminated' ? 'text-red-400' : 'text-gray-400';
                    
                    // Extract date and time from scheduledTime
                    let formattedDate = 'N/A';
                    let formattedTime = 'N/A';
                    
                    if (appointment.scheduledTime) {
                        try {
                            let dateTime;
                            
                            // Handle MongoDB date format: {"$date": "2025-05-13T08:00:00Z"}
                            if (appointment.scheduledTime.$date) {
                                dateTime = new Date(appointment.scheduledTime.$date);
                            } else if (typeof appointment.scheduledTime === 'string') {
                                dateTime = new Date(appointment.scheduledTime);
                            } else {
                                dateTime = new Date(appointment.scheduledTime);
                            }
                            
                            if (!isNaN(dateTime.getTime())) {
                                formattedDate = dateTime.toLocaleDateString();
                                formattedTime = dateTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                            }
                        } catch (e) {
                            console.error('Error parsing scheduledTime:', e);
                        }
                    }
                    
                    const professionalName = appointment.professionalDetails?.name || 'Professional';
                    const problemType = appointment.problemSummary || appointment.issueType || 'N/A';
                    
                    appointmentDiv.innerHTML = `
                        <div class="flex justify-between items-start mb-2">
                            <div class="font-medium text-white">${professionalName}</div>
                            <span class="text-xs ${statusColor} capitalize">${appointment.status.replace('_', ' ')}</span>
                        </div>
                        <div class="text-xs text-white/80 mb-1">
                            <strong>Service:</strong> ${problemType}
                        </div>
                        <div class="text-xs text-white/80 mb-1">
                            <strong>Date:</strong> ${formattedDate}
                        </div>
                        <div class="text-xs text-white/80 mb-2">
                            <strong>Time:</strong> ${formattedTime}
                        </div>
                        ${appointment.status === 'pending' ? `
                            <div class="flex gap-2 mt-2">
                                <button onclick="updateAppointmentStatus('${appointment.id}', 'confirmed')" 
                                        class="flex-1 bg-green-600 hover:bg-green-700 text-white text-xs py-1 px-2 rounded transition">
                                    Confirm
                                </button>
                                <button onclick="updateAppointmentStatus('${appointment.id}', 'cancelled')" 
                                        class="flex-1 bg-red-600 hover:bg-red-700 text-white text-xs py-1 px-2 rounded transition">
                                    Cancel
                                </button>
                            </div>
                        ` : ''}
                        ${appointment.status === 'confirmed' ? `
                            <div class="mt-2 text-xs text-green-400">✅ Appointment confirmed</div>
                            <button data-id="${appointment.id}" onclick="updateAppointmentStatus('${appointment.id}', 'job_completed')" class="mt-2 ml-2 text-sm bg-blue-600 text-white px-3 py-1 rounded-lg hover:bg-blue-700 transition">🔧 Mark as Completed</button>`
                         : ''}
                        ${appointment.status === 'job_completed' ? `
                            <div class="mt-2 text-xs text-yellow-400">📝 Job completed, awaiting feedback</div>
                            <a href="/feedback?professional_id=${encodeURIComponent(appointment.professionalDetails?.professionalId)}&job=${encodeURIComponent(appointment.problemSummary)}&name=${encodeURIComponent(appointment.professionalDetails?.name)}&appointment_id=${appointment.id}" class="mt-2 inline-block text-sm bg-purple-600 text-white px-3 py-1 rounded-lg hover:bg-purple-700 transition">
                            ✍️ Leave a Review
                            </a>
                            <button data-id="${appointment.id}" data-action="terminate" class="mt-2 ml-2 text-sm bg-gray-500 text-white px-3 py-1 rounded-lg hover:bg-gray-600 transition">✅ Finalize</button>`
                         : ''}
                    `;
                    
                    appointmentsList.appendChild(appointmentDiv);
                });
            }
        } catch (error) {
            console.error('Error loading appointments:', error);
            if (appointmentsList) {
                appointmentsList.innerHTML = '<div class="text-red-400 text-center">Error loading appointments</div>';
            }
        }
    }
    
    // Update appointment status
    window.updateAppointmentStatus = async function(appointmentId, status) {
        try {
            const response = await fetch(`/appointments/${appointmentId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ status: status })
            });
            
            if (response.ok) {
                loadAppointments(); // Reload appointments
            } else {
                console.error('Failed to update appointment status');
            }
        } catch (error) {
            console.error('Error updating appointment:', error);
        }
    }
    
    // Load appointments on page load
    loadAppointments();
    
    // Refresh appointments every 30 seconds
    setInterval(loadAppointments, 30000);
    
    // Check for initial message from home page
    const initialMessage = localStorage.getItem('initialMessage');
    if (initialMessage) {
        localStorage.removeItem('initialMessage');
        userInput.value = initialMessage;
        // Automatically send the initial message
        setTimeout(() => {
            sendMessage(initialMessage);
        }, 1000); // Small delay to ensure page is fully loaded
    } else {
        // Add welcome message only if no initial message
        setTimeout(() => {
            addMessage('agent', 'Hello! I\'m your Home Repair Assistant. How can I help you today? You can type your message or use the microphone button to speak.', 'Orchestrator');
        }, 500);
    }
});
