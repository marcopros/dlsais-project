const mongoose = require('mongoose');
const ObjectId = mongoose.Types.ObjectId;

const UsersData = [
    {
        name: "Alice Johnson",
        email: "alice.johnson@example.com",
        password: "password123",
        phone: "+39 333 1111111",
        location: {
            city: "Milan",
            zipCode: "20100"
        },
        diy_preference: {
            diy_skills: ["basic plumbing", "painting"],
            diy_tools: ["screwdriver", "hammer", "wrench", "paintbrush"]
        },
        trusted_professionals: [],
        trusted_users: [],
        feedbacks: [],
        sessions: []
    },
    {
        name: "Bob Smith",
        email: "bob.smith@example.com",
        password: "password123",
        phone: "+39 333 2222222",
        location: {
            city: "Milan",
            zipCode: "20121"
        },
        diy_preference: {
            diy_skills: ["electrical work", "carpentry"],
            diy_tools: ["drill", "multimeter", "saw", "level"]
        },
        trusted_professionals: [],
        trusted_users: [],
        feedbacks: [],
        sessions: []
    },
    {
        name: "Charlie Brown",
        email: "charlie.brown@example.com",
        password: "password123",
        phone: "+39 333 3333333",
        location: {
            city: "Milan",
            zipCode: "20122"
        },
        diy_preference: {
            diy_skills: [],
            diy_tools: ["screwdriver", "hammer"]
        },
        trusted_professionals: [],
        trusted_users: [],
        feedbacks: [],
        sessions: []
    },
    {
        name: "Diana Prince",
        email: "diana.prince@example.com",
        password: "password123",
        phone: "+39 333 4444444",
        location: {
            city: "Milan",
            zipCode: "20131"
        },
        diy_preference: {
            diy_skills: ["gardening", "tile work"],
            diy_tools: ["trowel", "tile cutter", "gardening tools", "measuring tape"]
        },
        trusted_professionals: [],
        trusted_users: [],
        feedbacks: [],
        sessions: []
    },
    {
        name: "Ethan Hunt",
        email: "ethan.hunt@example.com",
        password: "password123",
        phone: "+39 333 5555555",
        location: {
            city: "Turin",
            zipCode: "10100"
        },
        diy_preference: {
            diy_skills: ["plumbing", "electrical work", "carpentry"],
            diy_tools: ["pipe wrench", "multimeter", "drill", "saw", "hammer", "screwdriver"]
        },
        trusted_professionals: [],
        trusted_users: [],
        feedbacks: [],
        sessions: []
    },
    {
        name: "Fiona Gallagher",
        email: "fiona.gallagher@example.com",
        password: "password123",
        phone: "+39 333 6666666",
        location: {
            city: "Rome",
            zipCode: "00100"
        },
        diy_preference: {
            diy_skills: ["painting", "basic repairs"],
            diy_tools: ["paintbrush", "roller", "screwdriver", "hammer"]
        },
        trusted_professionals: [],
        trusted_users: [],
        feedbacks: [],
        sessions: []
    },
    {
        name: "George Miller",
        email: "george.miller@example.com",
        password: "password123",
        phone: "+39 333 7777777",
        location: {
            city: "Milan",
            zipCode: "20123"
        },
        diy_preference: {
            diy_skills: ["woodworking", "furniture assembly"],
            diy_tools: ["saw", "drill", "sandpaper", "wood glue", "clamps"]
        },
        trusted_professionals: [],
        trusted_users: [],
        feedbacks: [],
        sessions: []
    },
    {
        name: "Hannah Lee",
        email: "hannah.lee@example.com",
        password: "password123",
        phone: "+39 333 8888888",
        location: {
            city: "Naples",
            zipCode: "80100"
        },
        diy_preference: {
            diy_skills: ["basic plumbing", "painting"],
            diy_tools: ["wrench", "plunger", "paintbrush", "ladder"]
        },
        trusted_professionals: [],
        trusted_users: [],
        feedbacks: [],
        sessions: []
    },
    {
        name: "Ian Wright",
        email: "ian.wright@example.com",
        password: "password123",
        phone: "+39 333 9999999",
        location: {
            city: "Florence",
            zipCode: "50100"
        },
        diy_preference: {
            diy_skills: ["electrical troubleshooting"],
            diy_tools: ["multimeter", "wire strippers", "electrical tape", "screwdriver"]
        },
        trusted_professionals: [],
        trusted_users: [],
        feedbacks: [],
        sessions: []
    },
    {
        name: "Julia Roberts",
        email: "julia.roberts@example.com",
        password: "password123",
        phone: "+39 333 0000000",
        location: {
            city: "Bologna",
            zipCode: "40100"
        },
        diy_preference: {
            diy_skills: [],
            diy_tools: ["hammer", "screwdriver"]
        },
        trusted_professionals: [],
        trusted_users: [],
        feedbacks: [],
        sessions: []
    }
];

module.exports = UsersData;
