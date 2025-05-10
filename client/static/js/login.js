document.addEventListener("DOMContentLoaded", function () {
const loginModal = document.getElementById("login-modal");
const registerModal = document.getElementById("register-modal");

const openRegisterBtn = document.getElementById("open-register");
const closeLoginBtn = document.getElementById("close-login");
const closeRegisterBtn = document.getElementById("close-register");

const profileIcon = document.getElementById("profile-icon");

const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("registration-form");

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

  if (response.ok && data.access_token) {
    alert("Login successful!");
    loginModal.style.display = "none";
    localStorage.setItem('access_token', data.access_token);
  } else {
    alert(data.detail || "Login failed."); 
  }
};

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

// Attach event listeners
if (profileIcon) {
  profileIcon.addEventListener("click", () => {
    loginModal.style.display = "block";
  });
}

openRegisterBtn.addEventListener("click", () => {
  loginModal.style.display = "none";
  registerModal.style.display = "block";
});

closeLoginBtn.addEventListener("click", () => {
  loginModal.style.display = "none";
});

closeRegisterBtn.addEventListener("click", () => {
  registerModal.style.display = "none";
});

window.addEventListener("click", (event) => {
  if (event.target === loginModal) loginModal.style.display = "none";
  if (event.target === registerModal) registerModal.style.display = "none";
});

// Add submit listeners for forms
if (loginForm) {
  loginForm.addEventListener("submit", handleLoginSubmit);
}

if (registerForm) {
  registerForm.addEventListener("submit", handleRegisterSubmit);
}
});
