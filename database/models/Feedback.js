const mongoose = require('mongoose');


const feedbackSchema = new mongoose.Schema({
   user_id: {type: mongoose.Schema.Types.ObjectId, ref: 'User'},
   prefessional_id: {type: mongoose.Schema.Types.ObjectId, ref: 'Professional'},
   appointment_id: { type: mongoose.Schema.Types.ObjectId, ref: 'Appointment', unique : true},
   rating: Int32,
   text: String,
   tags: [String],
   sentiments: Double,
   update_trust_score: Double
});

module.exports = mongoose.model('Feedback', feedbackSchema);