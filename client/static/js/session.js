export function loadUserSessions(sessions) {
    console.log('LoadUserSession called: ', sessions);

    const sessionList = document.getElementById("session-list");
    const sessionsContainer = document.getElementById("sessions-container");

    sessionList.innerHTML = ""; // Clear previous content

    if (!Array.isArray(sessions)) {
        console.error("Invalid sessions data:", sessions);
        sessionsContainer.classList.add("hidden");
        return;
    }

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

            // Uncomment when ready
            // item.addEventListener("click", () => loadSessionMessages(sessionId));

            console.log(item)

            sessionList.appendChild(item);
        });
    }

    sessionsContainer.classList.remove("hidden");
}
