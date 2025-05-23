const appointments = [
    {
        "user_id": "663a1f1e2b1c4a0012a3b456", // Alice Johnson
        "professional_id": "673b2e3f4c5d6a0012b4c567", // Mario Rossi (plumber)
        "location": {
            "city": "Milan",
            "zipCode": "20100"
        },
        "scheduled_time": new Date("2025-05-30T09:00:00.000Z"),
        "confermation_dead_line": new Date("2025-05-29T09:00:00.000Z"),
        "problem_summary": "Water leak from kitchen faucet",
        "status": "scheduled"
    },
    {
        "user_id": "663a1f1e2b1c4a0012a3b458", // Bob Smith
        "professional_id": "673b2e3f4c5d6a0012b4c568", // Luca Bianchi (electrician)
        "location": {
            "city": "Milan",
            "zipCode": "20121"
        },
        "scheduled_time": new Date("2025-05-28T14:30:00.000Z"),
        "confermation_dead_line": new Date("2025-05-27T14:30:00.000Z"),
        "problem_summary": "Light switch not working in living room",
        "status": "confirmed"
    },
    {
        "user_id": "663a1f1e2b1c4a0012a3b460", // Charlie Brown
        "professional_id": "673b2e3f4c5d6a0012b4c569", // Raffaele Verdi (plumber)
        "location": {
            "city": "Milan",
            "zipCode": "20122"
        },
        "scheduled_time": new Date("2025-06-02T10:15:00.000Z"),
        "confermation_dead_line": new Date("2025-06-01T10:15:00.000Z"),
        "problem_summary": "Clogged sink drain",
        "status": "scheduled"
    },
    {
        "user_id": "663a1f1e2b1c4a0012a3b462", // Diana Prince
        "professional_id": "673b2e3f4c5d6a0012b4c570", // Alessandro Galli (plumber)
        "location": {
            "city": "Milan",
            "zipCode": "20131"
        },
        "scheduled_time": new Date("2025-05-26T16:00:00.000Z"),
        "confermation_dead_line": new Date("2025-05-25T16:00:00.000Z"),
        "problem_summary": "New shower enclosure installation",
        "status": "in_progress"
    },
    {
        "user_id": "663a1f1e2b1c4a0012a3b464", // Ethan Hunt
        "professional_id": "673b2e3f4c5d6a0012b4c571", // Federico Moretti (plumber)
        "location": {
            "city": "Turin",
            "zipCode": "10100"
        },
        "scheduled_time": new Date("2025-05-25T08:00:00.000Z"),
        "confermation_dead_line": new Date("2025-05-24T08:00:00.000Z"),
        "problem_summary": "Boiler not turning on - emergency",
        "status": "completed"
    },
    {
        "user_id": "663a1f1e2b1c4a0012a3b466", // Fiona Gallagher
        "professional_id": "673b2e3f4c5d6a0012b4c572", // Elisa Conti (plumber)
        "location": {
            "city": "Rome",
        "zipCode": "00100"
        },
        "scheduled_time": new Date("2025-06-01T11:30:00.000Z"),
        "confermation_dead_line": new Date("2025-05-31T11:30:00.000Z"),
        "problem_summary": "Bathroom pipe cleaning and replacement",
        "status": "scheduled"
    },
    {
        "user_id": "663a1f1e2b1c4a0012a3b468", // George Miller
        "professional_id": "673b2e3f4c5d6a0012b4c573", // Giorgio Rinaldi (plumber)
        "location": {
            "city": "Milan",
            "zipCode": "20123"
        },
        "scheduled_time": new Date("2025-05-29T15:45:00.000Z"),
        "confermation_dead_line": new Date("2025-05-28T15:45:00.000Z"),
        "problem_summary": "Routine boiler maintenance",
        "status": "confirmed"
    },
    {
        "user_id": "663a1f1e2b1c4a0012a3b470", // Hannah Lee
        "professional_id": "673b2e3f4c5d6a0012b4c574", // Martina De Angelis (plumber)
        "location": {
            "city": "Naples",
            "zipCode": "80100"
        },
        "scheduled_time": new Date("2025-06-03T13:00:00.000Z"),
        "confermation_dead_line": new Date("2025-06-02T13:00:00.000Z"),
        "problem_summary": "New sewage system installation",
        "status": "scheduled"
    },
    {
        "user_id": "663a1f1e2b1c4a0012a3b472", // Ian Wright
        "professional_id": "673b2e3f4c5d6a0012b4c575", // Marco Fontana (electrician)
        "location": {
            "city": "Florence",
            "zipCode": "50100"
        },
        "scheduled_time": new Date("2025-05-27T10:00:00.000Z"),
        "confermation_dead_line": new Date("2025-05-26T10:00:00.000Z"),
        "problem_summary": "Home automation system and LED lights installation",
        "status": "confirmed"
    },
    {
        "user_id": "663a1f1e2b1c4a0012a3b474", // Julia Roberts
        "professional_id": "673b2e3f4c5d6a0012b4c576", // Giulia Verdi (plumber)
        "location": {
            "city": "Bologna",
            "zipCode": "40100"
        },
        "scheduled_time": new Date("2025-06-04T09:30:00.000Z"),
        "confermation_dead_line": new Date("2025-06-03T09:30:00.000Z"),
        "problem_summary": "Complete bathroom renovation",
        "status": "scheduled"
    },
    {
        "user_id": "663a1f1e2b1c4a0012a3b456", // Alice Johnson (secondo appuntamento)
        "professional_id": "673b2e3f4c5d6a0012b4c577", // Sara Neri (painter)
        "location": {
            "city": "Milan",
            "zipCode": "20100"
        },
        "scheduled_time": new Date("2025-05-31T14:00:00.000Z"),
        "confermation_dead_line": new Date("2025-05-30T14:00:00.000Z"),
        "problem_summary": "Living room and bedroom painting",
        "status": "scheduled"
    },
    {
        "user_id": "663a1f1e2b1c4a0012a3b468", // George Miller (secondo appuntamento)
        "professional_id": "673b2e3f4c5d6a0012b4c578", // Francesca Romano (handyman)
        "location": {
            "city": "Milan",
            "zipCode": "20123"
        },
        "scheduled_time": new Date("2025-05-24T17:00:00.000Z"),
        "confermation_dead_line": new Date("2025-05-23T17:00:00.000Z"),
        "problem_summary": "IKEA furniture assembly and door repair",
        "status": "cancelled"
    }
];

module.exports = appointments;