const mongoose = require('mongoose');
const { type } = require('os');

const requestSchema = new mongoose.Schema({
    userId: {type: mongoose.Schema.Types.ObjectId, ref: 'User'},
    professionalId: {type: mongoose.Schema.Types.ObjectId, ref:'Professional'},
    date: Date,
    status: {type: String, enum: ['pending', 'accepted', 'rejected'], default: 'pending'},
    description: String
});

module.exports = mongoose.model('Request', requestSchema);