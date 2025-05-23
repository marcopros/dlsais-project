const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
    name: String,
    email: { type: String, unique : true},
    password: String,
    phone: String,
    location: {
        city: String,
        zipCode: String,
    },
    diy_preference:{
        diy_skills: [String],  // skills of the users in the diy 
        diy_tools: [String],   // tools avaible for the user to make diy
    },
    trusted_users: [String],
    feedbacks: [String],    
    sessions: [String] 
});

module.exports = mongoose.model('User', userSchema);