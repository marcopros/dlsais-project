const mongoose = require('mongoose');
const User = require('./models/User');
const Professional = require('./models/Professional');
const Request = require('./models/Request');
require('dotenv').config();

const uri = process.env.MONGODB_URI;

async function populate() {
    try {
        await mongoose.connect(uri);
        console.log("Connected to INTERNAL Database");
    } catch (err) {
        console.error("Error connecting to MongoDB Atlas:", err.message);
    }
}

populate();
