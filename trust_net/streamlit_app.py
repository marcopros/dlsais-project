import streamlit as st
import datetime
from trust_net import NetworkOfTrust
import networkx as nx
import matplotlib.pyplot as plt
import json
import os

# Percorso della cartella tests
TESTS_DIR = "tests/"

# Funzione per caricare le azioni da un file JSON
def load_actions_from_json(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        actions = []
        for action in data:
            func_name = action['function']
            params = action['params']
            actions.append((func_name, params))
        return actions
    except json.JSONDecodeError as e:
        st.error(f"Errore nel parsing del file JSON {file_path}: {str(e)}")
        return []
    except Exception as e:
        st.error(f"Errore durante il caricamento del file {file_path}: {str(e)}")
        return []

# Ottieni la lista dei file JSON nella cartella tests
try:
    test_files = [f for f in os.listdir(TESTS_DIR) if f.endswith('.json')]
except FileNotFoundError:
    st.error("La cartella 'tests/' non esiste. Creala e aggiungi file JSON validi.")
    test_files = []

# Seleziona il file di test
if test_files:
    selected_test = st.selectbox("Seleziona un file di test", test_files)
else:
    selected_test = None
    st.warning("Nessun file JSON trovato nella cartella 'tests/'.")

# Carica le azioni dal file selezionato
actions = []
if selected_test:
    actions = load_actions_from_json(os.path.join(TESTS_DIR, selected_test))

# Stato sessione
if 'idx' not in st.session_state or st.session_state.get('current_test') != selected_test:
    st.session_state.idx = 0
    st.session_state.current_test = selected_test

# Ricrea rete in base alle azioni fino a idx
net = NetworkOfTrust()
for i in range(st.session_state.idx):
    if i < len(actions):
        func, params = actions[i]
        try:
            getattr(net, func)(**params)
        except AttributeError:
            st.error(f"Funzione '{func}' non trovata in NetworkOfTrust.")
        except Exception as e:
            st.error(f"Errore nell'esecuzione dell'azione {func}: {str(e)}")

def draw_graph(graph):
    pos = nx.spring_layout(graph)
    plt.figure(figsize=(6,6))
    nx.draw_networkx_nodes(graph, pos, node_size=500)
    nx.draw_networkx_labels(graph, pos)
    nx.draw_networkx_edges(graph, pos)
    plt.axis('off')
    st.pyplot(plt)

# Interfaccia
st.title('Network of Trust Simulator')
col1, col2 = st.columns(2)
with col1:
    if st.button('Prev') and st.session_state.idx > 0:
        st.session_state.idx -= 1
with col2:
    if st.button('Next') and st.session_state.idx < len(actions):
        st.session_state.idx += 1

st.write(f"Azione corrente: {st.session_state.idx} / {len(actions)}")
# Mostra grafico
st.subheader('Grafico della rete')
draw_graph(net._graph)

# Mostra punteggi
st.subheader('Trust Scores')
try:
    scores = net.recommend_professionals('U1', top_n=10)
    st.dataframe(scores)
except Exception as e:
    st.error(f"Errore nel calcolo dei trust scores: {str(e)}")

# Mostra azione eseguita
st.subheader('Ultima azione')
if st.session_state.idx > 0 and st.session_state.idx <= len(actions):
    st.json(actions[st.session_state.idx-1])