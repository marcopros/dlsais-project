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

        // Sanitize agent name for class usage
        const safeRole = role.replace(/\s+/g, "-").toLowerCase(); // e.g., "diagnosis-agent"
        agentHeader.classList.add(safeRole); // now it's a single token

        agentHeader.textContent = role; // display full name
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

