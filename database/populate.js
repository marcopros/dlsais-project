const mongoose = require('mongoose');
const User = require('./models/User');
const Professional = require('./models/Professional');
const Request = require('./models/Request');
const Appointment = require('./models/Appointment');
const Feedback = require('./models/Feedback');

require('dotenv').config({ path: '../.env' });

const uri = process.env.MONGODB_URI;
if (!uri) {
    console.error("MongoDB URI is not defined in the environment variables.");
    process.exit(1);
}

const professionalsData = require('./mockProfessionalsData');
const usersData = require('./mockUsersData');
const requestsData = require('./mockRequestData');
const appointmentsData = require('./mockAppointmentsData');
const feedbacksData = require('./mockFeedbacksData');

async function populate() {
    try {
        await mongoose.connect(uri);
        console.log("Connected to INTERNAL Database");

        // Svuota le collezioni prima di inserire i dati mock
        await Professional.deleteMany({});
        await User.deleteMany({});
        await Request.deleteMany({});
        await Appointment.deleteMany({});
        await Feedback.deleteMany({});

        // Inserisci i dati mock nell'ordine corretto (prima le dipendenze)
        await Professional.insertMany(professionalsData);
        console.log("Professionals successfully inserted");
        
        await User.insertMany(usersData);
        console.log("Users successfully inserted");
        
        await Request.insertMany(requestsData);
        console.log("Requests successfully inserted");
        
        await Appointment.insertMany(appointmentsData);
        console.log("Appointments successfully inserted");
        
        await Feedback.insertMany(feedbacksData);
        console.log("Feedbacks successfully inserted");
        
        console.log("All mock data successfully inserted into the database");

    } catch (err) {
        console.error("Error populating database:", err.message);
    } finally {
        await mongoose.connection.close();
    }
}

populate();
