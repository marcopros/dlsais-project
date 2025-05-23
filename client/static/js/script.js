const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 120000); // 120 seconds

const initialScreen = document.getElementById("initial-screen");
const chatBox = document.getElementById("chat-box");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const loginForm = document.getElementById("login-form");

let chatContainer 
let chatStart = false


// Function to handel the firs message of the user 
async function startChat() {
    console.log('Start chat');

    // Remove <h1> and <p> elements
    const heading = document.querySelector('#central-part h1');
    const description = document.querySelector('#central-part p.description');
    if (heading) heading.remove();
    if (description) description.remove();

    // Add the chat container
    // Check if chat-container already exists
    chatContainer = document.getElementById('chat-container');
    if (!chatContainer) {
        chatContainer = document.createElement('div');
        chatContainer.id = 'chat-container';
        chatContainer.classList.remove('hidden');
        chatContainer.style.display = 'flex';
        chatContainer.style.flexDirection = 'column';
        chatContainer.style.gap = '10px';

        const newChatBox = document.createElement('div');
        newChatBox.id = 'chat-box';

        chatContainer.appendChild(newChatBox);
        chatContainer.appendChild(chatForm);        // move existing form below the chat box
        document.getElementById('central-part').appendChild(chatContainer);
    } 

    chatContainer.classList.remove('hidden');
    chatStart = true;

    await new Promise((resolve) => setTimeout(resolve, 0));
    chatStart = true

    userInput.focus();
}


// Append a message to the chat box
function appendMessage(role, text) {
    const chatBoxEl = document.getElementById("chat-box");
    if (!chatBoxEl) {
        console.error("chatBox element not found.");
        return;
    }

    const msgDiv = document.createElement("div");
    const isUser = role === "user";

    msgDiv.classList.add("message");
    msgDiv.classList.add(isUser ? "user" : "bot");

    const bubbleContainer = document.createElement("div");
    bubbleContainer.classList.add("text-bubble");

    if (!isUser) {
        const agentHeader = document.createElement("div");
        agentHeader.classList.add("agent-header");

        // Convert agent name to lowercase with hyphens for CSS class naming convention
        const safeRole = (typeof role === 'string') 
            ? role.replace(/\s+/g, "-").toLowerCase() 
            : "unknown-agent";
            
        // Add the appropriate class based on the agent type
        if (safeRole.includes("diagnosis")) {
            agentHeader.classList.add("diagnosis-agent");
        } else if (safeRole.includes("matching")) {
            agentHeader.classList.add("matching-agent");
        } else if (safeRole.includes("appointment")) {
            agentHeader.classList.add("appointment-agent");
        } else if (safeRole.includes("feedback")) {
            agentHeader.classList.add("feedback-agent");
        } else if (safeRole.includes("orchestrator")) {
            agentHeader.classList.add("orchestrator");
        } else if (safeRole.includes("system")) {
            agentHeader.classList.add("system");
        } else if (safeRole.includes("error")) {
            agentHeader.classList.add("error");
        } else {
            agentHeader.classList.add("agent");
        }
        
        agentHeader.textContent = role || "Agent"; // Display the actual agent name
        bubbleContainer.appendChild(agentHeader);
    }

    const messageText = document.createElement("div");
    messageText.classList.add("message-text");
    messageText.textContent = text;

    bubbleContainer.appendChild(messageText);
    msgDiv.appendChild(bubbleContainer);
    chatBoxEl.appendChild(msgDiv);
    chatBoxEl.scrollTop = chatBoxEl.scrollHeight;
}


// Handel the send of a user message
chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = userInput.value.trim();    // Get the user input
    if (!text) return;

    if (!chatStart) {                       // Check if chat has started, otherwise start it
        await startChat();                  // Ensure the chat UI is ready
    }

    appendMessage("user", text);            // Append the user message in the chat box
    userInput.value = "";                   // Clear the input field    
    userInput.focus();

    // Show typing indicator while waiting for the agent response
    const chatBoxEl = document.getElementById("chat-box");
    const typingEl = document.createElement("div");
    typingEl.classList.add("message", "bot");
    typingEl.id = "typing-indicator";

    const typingBubble = document.createElement("div");
    typingBubble.classList.add("text-bubble", "bot", "typing");

    for (let i = 0; i < 3; i++) {
        const dot = document.createElement("div");
        dot.classList.add("typing-dot");
        typingBubble.appendChild(dot);
    }

    typingEl.appendChild(typingBubble);
    chatBoxEl.appendChild(typingEl);

    const token = localStorage.getItem("access_token");     // Get the authentication token
    const sessionId = localStorage.getItem("session_id");   // Get session_id if available

    try {
        const res = await fetch("/send_message", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({
                message: text,
                session_id: sessionId || undefined          // Send session_id if exists
            }),
        });

        clearTimeout(timeoutId);
        const data = await res.json();
        console.log("Response from server:", data);
        typingEl.remove();

        // If not logged in, open the login pop-up
        if (res.status === 401) {
            localStorage.removeItem("access_token");
            loginModal.style.display = "block";
            return;
        }

        if (res.ok && data.response) {
            // Save new session_id if server returned one
            if (data.session_id) {
                localStorage.setItem("session_id", data.session_id);
            }

            // Append the bot response in the chat box
            appendMessage(data.agent, data.response);
        } else {
            appendMessage(data.agent, `[Error: ${data.detail || "No answer received"}]`);
        }

    } catch (err) {
        typingEl.remove();
        console.error("Errore to obtain an answer:", err);
        appendMessage("ERROR", "[Error: Timeout or connection error]");
    }
});

// Display a welcome message when the page loads
// Using a variable to track if welcome message has been displayed
let welcomeMessageDisplayed = false;

window.addEventListener('DOMContentLoaded', async () => {
    // Only display welcome message if it hasn't been displayed yet
    if (!welcomeMessageDisplayed) {
        welcomeMessageDisplayed = true;
        
        // Wait a short time to ensure everything is loaded
        setTimeout(() => {
            if (!chatStart) {
                startChat().then(() => {
                    // After chat is initialized, add welcome message
                    appendMessage("Orchestrator", "Hello! I'm your home repair assistant. What problem are you experiencing with your home today?");
                });
            }
        }, 500);
    }
});

