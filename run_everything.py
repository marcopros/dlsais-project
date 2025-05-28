import subprocess

commands = [
    ["python", "-m", "diagnosis_agent_app.server"],
    ["bash", "-c", "cd feedback_agent && sh start_server.sh"],
    ["python", "-m", "matching_agent_app.server"],
    ["python", "-m", "orchestrator.server"],
    ["python", "-m", "appointment_agent.server"],
    ["python", "-m", "client.server"],
]

processes = []

for cmd in commands:
    print(f"Avvio: {' '.join(cmd)}")
    p = subprocess.Popen(cmd)
    processes.append(p)

# Opzionale: attendi che tutti i processi finiscano (blocca lo script finché i server sono attivi)
try:
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    print("Interruzione manuale, chiusura di tutti i processi...")
    for p in processes:
        p.terminate()
