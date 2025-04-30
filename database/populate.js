const mongoose = require('mongoose');
const User = require('./models/User');
const Professional = require('./models/Professional');
const Request = require('./models/Request');

require('dotenv').config({ path: '../.env' }); 

const uri = process.env.MONGODB_URI;
if (!uri) {
    console.error("MongoDB URI is not defined in the environment variables.");
    process.exit(1);
}

const professionalsData = require('./mockProfessionalsData'); // Importa i dati dal file mockData.js


async function populate() {
    try {
        await mongoose.connect(uri);
        console.log("Connected to INTERNAL Database");

        // Popolare il database con i dati del mockup
        await Professional.insertMany(professionalsData);
        console.log("Data successfully inserted into the database");

    } catch (err) {
        console.error("Error connecting to MongoDB Atlas:", err.message);
    } finally {
        // Chiudere la connessione
        mongoose.connection.close();
    }
}

populate();


populate();
