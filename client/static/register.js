// register.js

document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");

    form.addEventListener("submit", function (event) {
        event.preventDefault(); // Prevent default form submission

        // Get form values
        const name = form.querySelector("input[name='username']").value.trim();
        const email = form.querySelector("input[name='email']").value.trim();
        const password = form.querySelector("input[name='password']").value;
        const phone = form.querySelector("input[name='phone']").value.trim();

        const city = form.querySelector("input[name='city']").value.trim();
        const zipCode = form.querySelector("input[name='zipCode']").value.trim();

        const diySkillsInput = form.querySelector("input[name='diy_skills']").value.trim();
        const diyToolsInput = form.querySelector("input[name='diy_tools']").value.trim();

        const diy_skills = diySkillsInput ? diySkillsInput.split(',').map(skill => skill.trim()) : [];
        const diy_tools = diyToolsInput ? diyToolsInput.split(',').map(tool => tool.trim()) : [];

        // Build request body
        const userData = {
            name,
            email,
            password,
            phone,
            city,
            zipCode,
            diy_skills,
            diy_tools
        };

        // Send POST request
        fetch("/user", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(userData)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw err; });
            }
            return response.json();
        })
        .then(data => {
            console.log("Registration successful:", data);
            alert("Registration successful! Redirecting...");
            window.location.href = "/signin"; 
        })
        .catch(error => {
            console.error("Registration failed:", error);
            alert(`Registration failed: ${error.message || 'Unknown error'}`);
        });
    });
});