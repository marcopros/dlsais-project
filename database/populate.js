const mongoose = require('mongoose');
const User = require('./models/User');
const Professional = require('./models/Professional');
const Request = require('./models/Request');

require('dotenv').config({ path: '.env' });

const uri = process.env.MONGODB_URI;
if (!uri) {
    console.error("MongoDB URI is not defined in the environment variables.");
    process.exit(1);
}

const professionalsData = require('./mockProfessionalsData');
const usersData = require('./mockUsersData');
const requestsData = require('./mockRequestData');

async function populate() {
    try {
        await mongoose.connect(uri);
        console.log("Connected to INTERNAL Database");

        // Svuota le collezioni prima di inserire i dati mock
        await Professional.deleteMany({});
        await User.deleteMany({});
        await Request.deleteMany({});

        await Professional.insertMany(professionalsData);
        await User.insertMany(usersData);
        await Request.insertMany(requestsData);
        console.log("Professionals, Users and Requests successfully inserted into the database");

    } catch (err) {
        console.error("Error connecting to MongoDB Atlas:", err.message);
    } finally {
        await mongoose.connection.close();
    }
}

populate();
