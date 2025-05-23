// Functions to manage the session list in the UI
export function loadUserSessions() {
    // Get the session list from local storage
    let sessions = localStorage.getItem("user_sessions");
    console.log('LoadUserSession called: ', sessions);

    // Get the html elements
    const sessionList = document.getElementById("session-list");
    const sessionsContainer = document.getElementById("sessions-container");
    sessionList.innerHTML = ""; // Clear previous content

    // Sins the senssions are storage like string, we need to parse it
    if (typeof sessions === "string") {
        try {
            sessions = JSON.parse(sessions);
        } catch (e) {
            console.error("Failed to parse sessions", e);
            return;
        }
    }

    // Check if the parsinf was successful
    if (!Array.isArray(sessions)) {
        console.error("Invalid sessions data:", sessions);
        return;
    }

    // Check if the session list is empty
    if (!sessions.length) {
        const empty = document.createElement("p");
        empty.textContent = "No sessions found.";
        sessionList.appendChild(empty);
    } else {
        sessions.forEach(session => {
            // Ensure session is object with id
            const sessionId = typeof session === 'object' ? session.id : session;
            const sessionTitle = typeof session === 'object' && session.title
                ? session.title
                : `Session ${sessionId.slice(0, 6)}...`;

            const item = document.createElement("li");
            item.classList.add("session-item");
            item.textContent = sessionTitle;
            item.dataset.sessionId = sessionId;

            // When the user clicks a session, the UI move to that session
            item.addEventListener("click", () => loadSessionMessages(sessionId));

            console.log(item)

            sessionList.appendChild(item);
        });
    }

    sessionsContainer.classList.remove("hidden");
}



// Function to close the session list sin the UI
export function closeSession() {
    const sessionList = document.getElementById("session-list");
    const sessionsContainer = document.getElementById("sessions-container");

    sessionList.innerHTML = ""; // Clear previous content
    sessionsContainer.classList.add("hidden");
}



// Function to switch to a specific session
function loadSessionMessages(sessionId) {
    //1. Update the session ID in local storage
    localStorage.setItem("session_id", sessionId);

    //2. Get the session messages from server
    // TODO

    //3. Update the chat UI with the session messages
    // TODO
}

