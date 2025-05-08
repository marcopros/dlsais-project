const initialScreen = document.getElementById("initial-screen");
const chatBox = document.getElementById("chat-box");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");

let chatContainer 
let chatStart = false


async function startChat() {
    console.log('Start chat');

    // Remove <h1> and <p> elements
    const heading = document.querySelector('#central-part h1');
    const description = document.querySelector('#central-part p.description');
    if (heading) heading.remove();
    if (description) description.remove();

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
        chatContainer.appendChild(chatForm);    // move existing form below the chat box
        document.getElementById('central-part').appendChild(chatContainer);
    } 

    chatContainer.classList.remove('hidden');
    chatStart = true;

    await new Promise((resolve) => setTimeout(resolve, 0));
    chatStart = true

    userInput.focus();
}


// Aggiunge un messaggio alla chat
function appendMessage(role, text) {
    const chatBoxEl = document.getElementById("chat-box");
    if (!chatBoxEl) {
        console.error("chatBox element not found.");
        return;
    }

    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", role);

    const bubble = document.createElement("div");
    bubble.classList.add("text-bubble", role);
    bubble.textContent = text;

    msgDiv.appendChild(bubble);
    chatBoxEl.appendChild(msgDiv);
    chatBoxEl.scrollTop = chatBoxEl.scrollHeight;
}

// Gestione invio messaggio
chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text) return;

    if (!chatStart){
        await startChat(); // Ensure the chat UI is ready
    }

    appendMessage("user", text);
    userInput.value = "";
    userInput.focus();

    // Show typing indicator
    const chatBoxEl = document.getElementById("chat-box");
    const typingEl = document.createElement("div");
    typingEl.classList.add("message", "bot");
    typingEl.id = "typing-indicator";

    const typingBubble = document.createElement("div");
    typingBubble.classList.add("text-bubble", "bot", "typing");

    // Add 3 animated dots
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement("div");
        dot.classList.add("typing-dot");
        typingBubble.appendChild(dot);
    }

    typingEl.appendChild(typingBubble);
    chatBoxEl.appendChild(typingEl);

    try {
        const res = await fetch("/send_message", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });

        const data = await res.json();

        // Remove typing animation
        typingEl.remove();

        if (data.response) {
            appendMessage("bot", data.response);
        } else {
            appendMessage("bot", "[Error: No answer received]");
        }
    } catch (err) {
        typingEl.remove();
        console.error("Errore to obtain an answer:", err);
        appendMessage("bot", "[Error: Impossible to obtain an answer]");
    }
});
