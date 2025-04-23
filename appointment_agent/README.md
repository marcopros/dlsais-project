# 📅 Appointment Agent - Home Repair Assistant

This agent is part of the [Home Repair Assistant](../README.md) project from the University of Trento (A.Y. 2024/2025).

---

## 🔹 Agent Purpose

The `Appointment Agent` is responsible for facilitating the booking of an appointment between the user and the selected professional, after the `Matching Agent` has provided the options.

**Behaviour:**

1.  **Receives Input:** Accepts the chosen professional's details, the problem description, and a list (currently simulated) of availability slots for that professional.
2.  **Interacts with the User:**
    - Confirms the professional's choice.
    - If there are available slots, presents them to the user in a numbered list.
    - Asks the user to select the desired slot by entering the corresponding number.
    - If there are no slots, informs the user of the unavailability.
3.  **Simulates Booking:**
    - Confirms the selected slot to the user.
    - Informs the user that the request has been sent to the professional (this part is simulated, a real contact does not occur).
4.  **Produces Output:**
    - Guidance and confirmation messages for the user.
    - Returns a final state (`PENDING_CONFIRMATION` or `NO_SLOTS_AVAILABLE`) and the requested appointment details (via `output_key="appointment_result"`), useful for the orchestrator agent.

> 💡 **Current Limitation:** The agent works with simulated availability lists passed by the orchestrator and simulates sending the request to the professional. It does not interact with real calendars or external APIs for booking or confirmation.

---

## ⚙️ System Architecture (Simplified Flow)

This agent fits into the flow managed by an orchestrator agent:
