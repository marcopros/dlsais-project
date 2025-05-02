import { useState, useEffect } from 'react';
import { Star, Check, X, ArrowRight, MessageSquare, Tag, RefreshCw, ArrowLeft } from 'lucide-react';

export default function FeedbackForm() {
  const [step, setStep] = useState(1);
  const [rating, setRating] = useState(0);
  const [inputMethod, setInputMethod] = useState(null); // 'text' o 'chips'
  const [textComment, setTextComment] = useState('');
  const [selectedChips, setSelectedChips] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  
  // Dati di esempio del lavoro
const jobData = {
    jobTitle: "Electrical System Repair",
    professional: "Marco Bianchi, Electrician",
    date: "April 28, 2025"
};

// Chip options
const positiveChips = [
    { id: 'p1', text: '👍 Professional', category: 'positive' },
    { id: 'p2', text: '⏱️ Punctual', category: 'positive' },
    { id: 'p3', text: '💰 Fair price', category: 'positive' },
    { id: 'p4', text: '🧹 Clean and tidy', category: 'positive' },
    { id: 'p5', text: '🤝 Polite', category: 'positive' },
    { id: 'p6', text: '🔧 Accurate work', category: 'positive' },
    { id: 'p7', text: '📱 Excellent communication', category: 'positive' },
    { id: 'p8', text: '🚀 Fast and efficient', category: 'positive' },
    { id: 'p9', text: '🎓 Very competent', category: 'positive' },
    { id: 'p10', text: '♻️ Sustainable', category: 'positive' },
    { id: 'p11', text: '🛠️ Modern equipment', category: 'positive' },
    { id: 'p12', text: '🔄 Flexible', category: 'positive' }
];
  
const negativeChips = [
    { id: 'n1', text: '⏰ Late', category: 'negative' },
    { id: 'n2', text: '💸 Too expensive', category: 'negative' },
    { id: 'n3', text: '🗣️ Poor communication', category: 'negative' },
    { id: 'n4', text: '🛠️ Incomplete work', category: 'negative' },
    { id: 'n5', text: '😕 Unprofessional', category: 'negative' },
    { id: 'n6', text: '🧰 Inadequate equipment', category: 'negative' },
    { id: 'n7', text: '📝 Inaccurate estimate', category: 'negative' },
    { id: 'n8', text: '⚠️ Safety issues', category: 'negative' },
    { id: 'n9', text: '🗑️ Left a mess', category: 'negative' },
    { id: 'n10', text: '⌛ Too slow', category: 'negative' },
    { id: 'n11', text: '💦 Non-durable result', category: 'negative' },
    { id: 'n12', text: '🔙 Required additional interventions', category: 'negative' }
];
  
  const handleRatingSelect = (value) => {
    setRating(value);
    // Animazione prima di passare al prossimo step
    setTimeout(() => setStep(2), 300);
  };
  
  const toggleChip = (chipId) => {
    if (selectedChips.includes(chipId)) {
      setSelectedChips(selectedChips.filter(id => id !== chipId));
    } else {
      setSelectedChips([...selectedChips, chipId]);
    }
  };
  
  const selectInputMethod = (method) => {
    setInputMethod(method);
    // Reset di eventuali input precedenti quando cambiamo metodo
    if (method === 'text') {
      setSelectedChips([]);
    } else if (method === 'chips') {
      setTextComment('');
    }
  };
  
  const handleSubmit = () => {
    setIsSubmitting(true);
    
    // Creazione dell'oggetto JSON da inviare
    const feedbackData = {
      jobInfo: jobData,
      rating: rating,
      feedbackType: inputMethod,
      textFeedback: inputMethod === 'text' ? textComment : '',
      selectedTags: inputMethod === 'chips' ? 
        [...positiveChips, ...negativeChips]
          .filter(chip => selectedChips.includes(chip.id))
          .map(chip => ({ id: chip.id, text: chip.text, category: chip.category })) : []
    };
    
    console.log('Feedback JSON:', JSON.stringify(feedbackData, null, 2));
    
    // Simulazione invio dati
    setTimeout(() => {
      setIsSubmitting(false);
      setIsSubmitted(true);
    }, 1000);
  };
  
  const resetForm = () => {
    setStep(1);
    setRating(0);
    setInputMethod(null);
    setTextComment('');
    setSelectedChips([]);
    setIsSubmitted(false);
  };
  
  const canSubmit = rating > 0 && (
    (inputMethod === 'text' && textComment.trim().length > 0) || 
    (inputMethod === 'chips' && selectedChips.length > 0)
  );

  return (
    <div className="bg-gray-50 min-h-screen flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-md overflow-hidden transition-all duration-300">
        {isSubmitted ? (
          <div className="p-8 flex flex-col items-center justify-center space-y-6">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <Check className="text-green-500 w-8 h-8" />
            </div>
            <h2 className="text-2xl font-bold text-center">Grazie per il tuo feedback!</h2>
            <p className="text-gray-600 text-center">Il tuo parere è molto importante per migliorare i nostri servizi.</p>
            <button
              onClick={resetForm}
              className="flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Invia un altro feedback</span>
            </button>
          </div>
        ) : (
          <>
            {/* Header con informazioni lavoro */}
            <div className="bg-blue-600 text-white p-6">
              <h1 className="text-2xl font-bold mb-2">{jobData.jobTitle}</h1>
              <p className="text-blue-100">{jobData.professional}</p>
              <p className="text-blue-200 text-sm">{jobData.date}</p>
            </div>
            
            {/* Progress Steps */}
            <div className="flex justify-center mt-4 mb-2">
              <div className={`w-4 h-4 rounded-full ${step === 1 ? 'bg-blue-600' : 'bg-blue-300'} mx-1`}></div>
              <div className={`w-4 h-4 rounded-full ${step === 2 ? 'bg-blue-600' : 'bg-blue-300'} mx-1`}></div>
            </div>
            
            {/* Step 1: Valutazione con stelle */}
            {step === 1 && (
              <div className="p-6 animate-fadeIn">
                <h2 className="text-xl font-semibold text-center mb-6">Come valuti questo lavoro?</h2>
                <div className="flex justify-center space-x-2 mb-8">
                  {[1, 2, 3, 4, 5].map((value) => (
                    <button
                      key={value}
                      onClick={() => handleRatingSelect(value)}
                      className="focus:outline-none transition-transform hover:scale-110"
                    >
                      <Star
                        className={`w-10 h-10 ${value <= rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300'}`}
                      />
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            {/* Step 2: Commento testuale o Chips */}
            {step === 2 && (
              <div className="p-6 animate-fadeIn">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold text-center">Lascia un feedback dettagliato</h2>
                </div>
                
                {/* Toggle tra commento testuale e chips */}
                <div className="flex justify-center space-x-4 mb-6">
                  <button
                    onClick={() => selectInputMethod('text')}
                    className={`flex items-center px-4 py-2 rounded-lg ${inputMethod === 'text'
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
                  >
                    <MessageSquare className="w-4 h-4 mr-2" />
                    <span>Scrivi</span>
                  </button>
                  <button
                    onClick={() => selectInputMethod('chips')}
                    className={`flex items-center px-4 py-2 rounded-lg ${inputMethod === 'chips'
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
                  >
                    <Tag className="w-4 h-4 mr-2" />
                    <span>Seleziona</span>
                  </button>
                </div>
                
                {/* Condizionale per il metodo selezionato */}
                {inputMethod === 'text' && (
                  <div className="animate-fadeIn">
                    <textarea
                      value={textComment}
                      onChange={(e) => setTextComment(e.target.value)}
                      placeholder="Scrivi il tuo commento qui..."
                      className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 h-32"
                    />
                  </div>
                )}
                
                {inputMethod === 'chips' && (
                  <div className="space-y-6 animate-fadeIn">
                    <div>
                      <h3 className="font-medium text-green-600 mb-3">Aspetti positivi</h3>
                      <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto p-1">
                        {positiveChips.map((chip) => (
                          <button
                            key={chip.id}
                            onClick={() => toggleChip(chip.id)}
                            className={`px-3 py-2 rounded-full text-sm transition-all ${
                              selectedChips.includes(chip.id)
                                ? 'bg-green-100 text-green-800 border-2 border-green-500'
                                : 'bg-gray-100 text-gray-800 border border-gray-300 hover:bg-gray-200'
                            }`}
                          >
                            {chip.text}
                          </button>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <h3 className="font-medium text-red-600 mb-3">Aspetti da migliorare</h3>
                      <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto p-1">
                        {negativeChips.map((chip) => (
                          <button
                            key={chip.id}
                            onClick={() => toggleChip(chip.id)}
                            className={`px-3 py-2 rounded-full text-sm transition-all ${
                              selectedChips.includes(chip.id)
                                ? 'bg-red-100 text-red-800 border-2 border-red-500'
                                : 'bg-gray-100 text-gray-800 border border-gray-300 hover:bg-gray-200'
                            }`}
                          >
                            {chip.text}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Tasto submit */}
                <div className="mt-8 flex space-x-3">
                  <button
                    onClick={() => setStep(1)}
                    className="px-3 py-3 rounded-lg bg-gray-200 text-gray-700 hover:bg-gray-300 transition-all flex items-center justify-center"
                  >
                    <ArrowLeft className="w-5 h-5" />
                  </button>
                  
                  <button
                    onClick={handleSubmit}
                    disabled={!canSubmit || isSubmitting}
                    className={`flex-1 py-3 rounded-lg flex items-center justify-center space-x-2 transition-all ${
                      canSubmit && !isSubmitting
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    {isSubmitting ? (
                      <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full"></div>
                    ) : (
                      <>
                        <span>Invia feedback</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
      
      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out forwards;
        }
      `}</style>
    </div>
  );
}