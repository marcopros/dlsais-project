const UsersData = [
    {
        _id: "663a1f1e2b1c4a0012a3b456",
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
        trusted_users: ["bob.smith@example.com", "charlie.brown@example.com"],
        feedbacks: [],
        sessions: []
    },
    {
        _id: "663a1f1e2b1c4a0012a3b458",
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
        trusted_users: ["alice.johnson@example.com"],
        feedbacks: [],
        sessions: []
    },
    {
        _id: "663a1f1e2b1c4a0012a3b460",
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
        trusted_users: ["alice.johnson@example.com", "diana.prince@example.com"],
        feedbacks: [],
        sessions: []
    },
    {
        _id: "663a1f1e2b1c4a0012a3b462",
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
        trusted_users: ["ethan.hunt@example.com"],
        feedbacks: [],
        sessions: []
    },
    {
        _id: "663a1f1e2b1c4a0012a3b464",
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
        trusted_users: ["fiona.gallagher@example.com", "george.miller@example.com"],
        feedbacks: [],
        sessions: []
    },
    {
        _id: "663a1f1e2b1c4a0012a3b466",
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
        trusted_users: ["hannah.lee@example.com"],
        feedbacks: [],
        sessions: []
    },
    {
        _id: "663a1f1e2b1c4a0012a3b468",
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
        trusted_users: ["ian.wright@example.com", "julia.roberts@example.com"],
        feedbacks: [],
        sessions: []
    },
    {
        _id: "663a1f1e2b1c4a0012a3b470",
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
        trusted_users: ["alice.johnson@example.com"],
        feedbacks: [],
        sessions: []
    },
    {
        _id: "663a1f1e2b1c4a0012a3b472",
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
        trusted_users: [],
        feedbacks: [],
        sessions: []
    },
    {
        _id: "663a1f1e2b1c4a0012a3b474",
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
        trusted_users: ["george.miller@example.com"],
        feedbacks: [],
        sessions: []
    }
];

module.exports = UsersData;