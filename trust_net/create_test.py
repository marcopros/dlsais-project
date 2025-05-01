from datetime import datetime, timedelta
import json
import os

# Directory per i test
test_dir = "tests"
os.makedirs(test_dir, exist_ok=True)

# Funzione helper per creare date in passato
def days_ago(n):
    return (datetime.now() - timedelta(days=n)).isoformat()

# Generazione del test: feedback che peggiorano nel tempo
actions = []

# Aggiunta utente e professionista
actions.append(["add_user", {"user_id": "U1", "name": "Mario"}])
actions.append(["add_professional", {
    "professional_id": "P1",
    "name": "Idraulico Bruno",
    "specializations": ["Idraulico"],
    "service_area": "Roma",
    "verified": True
}])

# Aggiunta di 12 servizi distribuiti su un anno, feedback peggiorano
initial_scores = [
    (5, 5, 4, 5),
    (5, 4, 4, 5),
    (4, 4, 3, 4),
    (4, 4, 3, 4),
    (3, 3, 3, 3),
    (3, 2, 2, 3),
    (2, 2, 2, 2),
    (2, 2, 1, 2),
    (1, 2, 1, 1),
    (1, 1, 3, 1),
    (1, 2, 1, 1),
    (1, 1, 1, 1),
]

for i, (q, pu, pz, co) in enumerate(initial_scores):
    service_id = f"S{i+1}"
    feedback_id = f"F{i+1}"
    days_before = 30 * (len(initial_scores) - i)  # feedback più vecchi prima
    actions.append(["add_service_interaction", {
        "service_id": service_id,
        "user_id": "U1",
        "professional_id": "P1",
        "service_type": "Riparazione tubo",
        "date": days_ago(days_before),
        "status": "Completed"
    }])
    actions.append(["add_feedback", {
        "service_id": service_id,
        "feedback_id": feedback_id,
        "overall_rating": (q + pu + pz + co) / 4,
        "quality": q,
        "punctuality": pu,
        "price": pz,
        "courtesy": co,
        "text": f"Servizio valutato al livello {q}-{pu}-{pz}-{co}",
        "date": days_ago(days_before)
    }])

# Salva il test
test_path = os.path.join(test_dir, "decaying_feedback.json")
with open(test_path, "w") as f:
    json.dump(actions, f, indent=2)

test_path
