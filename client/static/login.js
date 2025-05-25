document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("loginForm");

    form.addEventListener("submit", function (event) {
        event.preventDefault(); // Prevent default form behavior

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        const userData = {
            email,
            password
        };

        // Send POST request to login endpoint
        fetch("/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(userData)
        })
        .then(async (response) => {
            let data;
            try {
                data = await response.json();
            } catch {
                throw new Error("Server returned invalid JSON");
            }

            if (!response.ok) {
                throw new Error(data.message || "Login failed");
            }

            return data;
        })
        .then((data) => {
            console.log("Login successful:", data);

            // Save token and user info in localStorage
            localStorage.setItem("authToken", data.token);
            localStorage.setItem("user", JSON.stringify(data.user));

            alert("✅ Login successful!");
            window.location.href = "/"; // Redirect to dashboard
        })
        .catch((error) => {
            console.error("Login error:", error);
            alert(`⚠️ Login failed: ${error.message}`);
        });
    });
});