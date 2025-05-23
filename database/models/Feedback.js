const mongoose = require('mongoose');

const feedbackSchema = new mongoose.Schema({
   user_id: {type: mongoose.Schema.Types.ObjectId, ref: 'User'},
   prefessional_id: {type: mongoose.Schema.Types.ObjectId, ref: 'Professional'},
   appointment_id: { type: mongoose.Schema.Types.ObjectId, ref: 'Appointment', unique : true},
   rating: Number,
   text: String,
   tags: [String],
   sentiments: Number,
   update_trust_score: Number
});

module.exports = mongoose.model('Feedback', feedbackSchema);