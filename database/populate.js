const mongoose = require('mongoose');
const User = require('./models/User');
const Professional = require('./models/Professional');
const Request = require('./models/Request');

const uri = 'mongodb+srv://marco:unitn25@dlsais-cluster.vkxu2tc.mongodb.net/?retryWrites=true&w=majority&appName=dlsais-cluster';

mongoose.connect(uri)
    .then(() => console.log('Connected to MongoDB Atlas'))
    .catch(err => console.error('Error connecting to MongoDB Atlas:', err));

