const mongoose = require('mongoose');

const sessionSchema = new mongoose.Schema({
    user_id: {type: mongoose.Schema.Types.ObjectId, ref: 'User'},
    messages: [{
        author: String,
        test: String,
        data: Object
    }]
});

module.exports = mongoose.model('Session', sessionSchema);