import { loadUserSessions, closeSession } from './session.js';

const loginModal = document.getElementById("login-modal");
const registerModal = document.getElementById("register-modal");
const profileIcon = document.getElementById("profile-icon")


//--------------------------------------------- LOGIN ICON ---------------------------------------------//
// Function to menage the login model
const manageLoginModal = () => {
    if (loginModal.style.display === "block") {
        loginModal.style.display = "none";
    } else {
        loginModal.style.display = "block";
    }
};

// Add the open LoginModel listener to the profile icon
profileIcon.addEventListener("click", manageLoginModal);

// Function to menage the profile menu
const manageProfileMenu = () => {
    const profile = document.getElementById("profile-dropdown");
    if (profile.style.display === "block") {
        profile.style.display = "none";
    } else {
        profile.style.display = "block";
    }
};

// Function to menage the page login update
export const managePageLoginUpdate = () => {
    const name = localStorage.getItem("user_name");
    const token = localStorage.getItem("access_token");
    const sessions = localStorage.getItem("user_sessions");

    if (token) {

        // Switch to logged-in state
        profileIcon.classList.remove("profile-icon-unlogged", "fas", "fa-user-circle");
        profileIcon.classList.add("profile-icon-logged");

        // Remove the open LoginModel listener
        profileIcon.removeEventListener("click", manageLoginModal);

        // Add the open ProfileMenu listener
        profileIcon.addEventListener("click", manageProfileMenu);

        // Open the session list
        loadUserSessions(sessions)

        // Set first letter
        profileIcon.textContent = name && typeof name === "string"
            ? name.charAt(0).toUpperCase()
            : "U";

    } else {
        // Switch back to unlogged state
        profileIcon.classList.remove("profile-icon-logged");
        profileIcon.classList.add("profile-icon-unlogged");
        profileIcon.classList.add("fas", "fa-user-circle"); // Restore FA icon

        // Add the open LoginModel listener
        profileIcon.addEventListener("click", manageLoginModal);

        // Remove the open ProfileMenu listener
        profileIcon.removeEventListener("click", manageProfileMenu);

        // Close the session if logged out
        closeSession(); 

        // Reset content
        profileIcon.textContent = "";
    }
};

//---------------------------------------------- LOGOUT ------------------------------------------------//
const handleLogout = () => {

    // Close the profile menu
    const profile = document.getElementById("profile-dropdown");
    if (profile) {
        profile.style.display = "none";
    }

    // Clear local storage
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_sessions");
    localStorage.removeItem("session_id");
    localStorage.removeItem("user_name");
    localStorage.removeItem("user_email");
    localStorage.removeItem("user_phone");

    // Update the page to reflect the logged-out state
    managePageLoginUpdate();
}

const logoutButton = document.getElementById("logout-button");
if (logoutButton) {
    logoutButton.addEventListener("click", handleLogout);
}



//--------------------------------------------- LOGIN MODAL ---------------------------------------------//
// Function to handle the login submission
const handleLoginSubmit = async (event) => {
    event.preventDefault();

    let email = document.getElementById("login-email").value;
    let password = document.getElementById("login-password").value;

    const response = await fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
    });

    const data = await response.json();
    console.log(data)

    if (response.ok && data.access_token) {
        alert("Login successful!");
        loginModal.style.display = "none";

        // Save the user data in local storage
        localStorage.setItem('user_name', data.user.name);
        localStorage.setItem('user_email', data.user.email);
        localStorage.setItem('user_phone', data.user.phone);
        localStorage.setItem('access_token', data.access_token);

        // Save sessions (if any)
        if (data.sessions && data.sessions.length > 0) {
            localStorage.setItem('user_sessions', JSON.stringify(data.sessions));
        } 

        // Update the page to reflect the logged-in state
        managePageLoginUpdate()
      
    } else {
        alert(data.detail || "Login failed.");
    }
};

// Add submit listeners for forms
const loginForm = document.getElementById("login-form");
if (loginForm) {
  loginForm.addEventListener("submit", handleLoginSubmit);

  // Add listener to register button
  const openRegisterBtn = document.getElementById("open-register");
  openRegisterBtn.addEventListener("click", () => {
    loginModal.style.display = "none";
    registerModal.style.display = "block";
  });

  // Close login modal when clicking the close button
  const closeLoginBtn = document.getElementById("close-login");
  closeLoginBtn.addEventListener("click", () => {
    loginModal.style.display = "none";
  });
}


//------------------------------------------ REGISTRATION MODAL ------------------------------------------//
// Function to handle the registration submission
const handleRegisterSubmit = async (event) => {
  event.preventDefault();

  let name = document.getElementById("register-name").value;
  let email = document.getElementById("register-email").value;
  let password = document.getElementById("register-password").value;
  let phone = document.getElementById("register-phone").value;
  
  if (!name || !email || !password || !phone) {
      console.error("Missing elements for registration form");
      return;
  }

  const response = await fetch('/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name, email, password, phone }),
  });

  const data = await response.json();

  if (data.success) {
    alert("Registration successful!");
    registerModal.style.display = "none"; // Close register modal
  } else {
    alert(data.message); // Show error message
  }
};

// Add submit listeners for forms
const registerForm = document.getElementById("registration-form");
if (registerForm) {
  registerForm.addEventListener("submit", handleRegisterSubmit);

  const closeRegisterBtn = document.getElementById("close-register");
  closeRegisterBtn.addEventListener("click", () => {
    registerModal.style.display = "none";
  });

}

// Close modals when clicking outside of them
window.addEventListener("click", (event) => {
  if (event.target === loginModal) loginModal.style.display = "none";
  if (event.target === registerModal) registerModal.style.display = "none";
});


