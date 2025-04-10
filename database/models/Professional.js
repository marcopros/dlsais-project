const mongoose = require('mongoose');

const ProfessionalSchema = new mongoose.Schema({
    name: String,
    email: { type: String, unique: true},
    password: String,
    phone: String,
    profession: String,
    rating: Number
});

module.exports = mongoose.model('Professional', ProfessionalSchema);