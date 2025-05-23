const mongoose = require('mongoose');

const appointmentSchema = new mongoose.Schema({
   user_id:  {type: mongoose.Schema.Types.ObjectId, ref: 'User'},
   professional_id: {type: mongoose.Schema.Types.ObjectId, ref: 'Professional'},
   location: {
        city: String,
        zipCode: String,
    },
    scheduled_time: Date, 
    confermation_dead_line: Date,
    problem_summary: String,
    status: String,
});

module.exports = mongoose.model('Appointment', appointmentSchema);