Definizione per i 3 agenti e la formula finale per il punteggio di fiducia:

---

### Agente 1: Analisi del Testo

**Ruolo:** Analizzare un commento testuale libero per estrarne il sentiment e le caratteristiche chiave menzionate.

**Input:** Una stringa contenente il commento testuale (`textFeedback` dal JSON originale).

**Compiti:**

1.  Analizza il testo per determinare il sentiment generale.
2.  Identifica ed estrai le caratteristiche specifiche (positive o negative) del servizio o del professionista menzionate nel testo. Cerca di essere conciso nelle feature estratte.

**Output:** Un oggetto JSON con la seguente struttura:

```json
{
  "sentiment": "string", // Uno tra "Positivo", "Negativo", "Misto", "Neutro"
  "extractedFeatures": [ "string" ] // Lista di stringhe, es: ["puntuale", "costoso", "lavoro accurato", "cordiale"]
}
```

**Esempio (per te, Agente 1):**

* **Input:** `"Il tecnico è stato molto professionale e ha risolto il problema rapidamente. Unico neo: il prezzo un po' elevato rispetto a quanto mi aspettavo."`
* **Output atteso:**
    ```json
    {
      "sentiment": "Misto",
      "extractedFeatures": ["professionale", "rapido", "prezzo elevato"]
    }
    ```

---

### Agente 2: Valutazione di Fakeness

**Ruolo:** Valutare la probabilità che un feedback sia falso (fraudolento per alzare il punteggio o un tentativo di sabotaggio per abbassarlo), utilizzando sia il feedback attuale che dati storici.

**Input:** L'oggetto JSON completo del feedback corrente. **Tool Access:** Questo agente ha accesso a funzioni interne per recuperare i feedback storici per il professionista (`get_professional_history(professional_id)`) e, idealmente, per l'utente (`get_user_history(user_id)` - anche se user_id non è nel JSON attuale, concettualmente è utile).

**Compiti:**

1.  Esamina il feedback attuale per segnali di potenziale fakeness:
    * **Incoerenza Rating/Contenuto:** Il rating a stelle corrisponde al sentiment/alle chips selezionate? (Es. 5 stelle con commento molto negativo, o 1 stella con commento molto positivo/chips positive).
    * **Linguaggio:** Il testo è generico, esagerato, o privo di dettagli specifici sul lavoro svolto? (Es. "Semplicemente il migliore!" o "Pessimo in tutto!" senza spiegazioni).
    * **Lunghezza/Dettaglio:** Un feedback testuale molto breve e non descrittivo, soprattutto se il rating è estremo.
    * **Chips Contraddittorie:** Selezione contemporanea di chips positive e negative forti sullo stesso aspetto (es. "Prezzo onesto" e "Troppo costoso").

2.  Utilizza i tool per esaminare la storia del professionista e dell'utente (simula l'uso dei tool e descrivi cosa cercheresti):
    * **Storia del Professionista:**
        * Il rating attuale è un forte scostamento dalla media storica del professionista? (Es. un professionista con media 4.8 riceve improvvisamente un 1 o 0).
        * Ci sono cluster di recensioni molto simili (per testo, rating, o data) in un breve periodo? (Potrebbe indicare acquisto di recensioni o campagna di sabotaggio).
    * **Storia dell'Utente:** (Se disponibile - assumi di poterla guardare per l'analisi concettuale)
        * L'utente ha lasciato solo 5 stelle o solo 1 stella in passato?
        * L'utente recensisce moltissimi professionisti in un breve lasso di tempo?
        * L'utente ha una storia di recensioni coerenti o sembra che stia agendo in modo anomalo?

3.  Basandosi sull'analisi attuale e storica (simulata), assegna un punteggio `fakeConfidence` da 0.0 (nessun segnale di fakeness) a 1.0 (altamente probabile che sia falso).

4.  Fornisci un breve `fakeReasoning` che spiega perché è stato assegnato quel punteggio (es. "Rating e commento incoerenti", "Linguaggio generico, primo feedback dell'utente", "Forte deviazione dalla media storica del professionista").

**Output:** Un oggetto JSON con la seguente struttura:

```json
{
  "fakeConfidence": float (0.0-1.0),
  "fakeReasoning": "string"
}
```

**Esempio (per te, Agente 2):**

* **Input:** (JSON del commento testuale visto prima, assumi anche di avere accesso alla storia)
    ```json
    {
      "jobInfo": { ... },
      "rating": 4,
      "feedbackType": "text",
      "textFeedback": "Il tecnico è stato molto professionale e ha risolto il problema rapidamente. Unico neo: il prezzo un po' elevato rispetto a quanto mi aspettavo.",
      "selectedTags": []
    }
    ```
* **Assunzione storica (per questo esempio):** Il professionista ha una media di 4.5 stelle. L'utente ha lasciato altre 3 recensioni (3, 4, 5 stelle) in passato, tutte con commenti specifici.
* **Output atteso:**
    ```json
    {
      "fakeConfidence": 0.1, // Basso, la recensione è mista e coerente
      "fakeReasoning": "Feedback coerente, rating nella norma storica del professionista, utente con storico di recensioni genuine."
    }
    ```
* **Esempio 2 (per te, Agente 2):**
    * **Input:**
        ```json
        {
          "jobInfo": { ... },
          "rating": 5,
          "feedbackType": "text",
          "textFeedback": "Semplicemente il migliore in assoluto! Veloce, bravo, super!",
          "selectedTags": []
        }
        ```
    * **Assunzione storica (per questo esempio):** Il professionista ha una media di 3.0 stelle con molti commenti misti o negativi. Questo è il primo feedback lasciato dall'utente.
    * **Output atteso:**
        ```json
        {
          "fakeConfidence": 0.7, // Alto, linguaggio iperbolico, mancanza di dettagli, primo feedback utente, forte scostamento dalla media del professionista.
          "fakeReasoning": "Linguaggio iperbolico e generico, mancanza di dettagli specifici. Primo feedback dell'utente. Rating molto superiore alla media storica del professionista."
        }
        ```

---

### Agente 3: Valutazione Livello di Informazione

**Ruolo:** Valutare quanta informazione utile è contenuta nel feedback per la valutazione qualitativa del servizio.

**Input:** L'oggetto JSON completo del feedback corrente, E l'output dell'Agente 1 (se il feedback è testuale).

**Compiti:**

1.  Controlla il `feedbackType`:
    * Se è "chips", il livello di informazione è "Medium".
    * Se è "text", valuta la qualità del testo e i risultati dell'Agente 1:
        * Se il testo è molto breve o generico (puoi inferirlo dalla lunghezza del `textFeedback` o dal numero/pertinenza delle `extractedFeatures`), il livello è "Medium".
        * Se il testo è descrittivo, dettagliato e l'Agente 1 ha estratto diverse feature pertinenti, il livello è "High".

2.  Assegna il `informationLevel` risultante ("Low", "Medium", "High"). (Nota: "Low" si applicherebbe concettualmente a un feedback di sole stelle senza testo né chips, che nel tuo JSON non è un caso possibile).

**Output:** Un oggetto JSON con la seguente struttura:

```json
{
  "informationLevel": "Low" | "Medium" | "High"
}
```

**Esempio (per te, Agente 3):**

* **Input 1:** (JSON chips dall'esempio iniziale) + Output Agente 1 (non applicabile)
    ```json
    {
      "jobInfo": { ... }, "rating": 4, "feedbackType": "chips", "textFeedback": "",
      "selectedTags": [ { "id": "p1", ... }, { "id": "p7", ... }, { "id": "n2", ... } ]
    }
    ```
    * **Output atteso:**
        ```json
        {
          "informationLevel": "Medium"
        }
        ```
* **Input 2:** (JSON testo dall'esempio iniziale) + Output Agente 1 (dall'esempio 1 di A1)
    ```json
    {
      "jobInfo": { ... }, "rating": 4, "feedbackType": "text", "textFeedback": "Il tecnico è stato molto professionale e ha risolto il problema rapidamente. Unico neo: il prezzo un po' elevato rispetto a quanto mi aspettavo.", "selectedTags": []
    }
    ```
    * **Output Agente 1:**
        ```json
        {
          "sentiment": "Misto",
          "extractedFeatures": ["professionale", "rapido", "prezzo elevato"]
        }
        ```
    * **Output atteso:**
        ```json
        {
          "informationLevel": "High" // Testo descrittivo con feature pertinenti
        }
        ```
* **Input 3:** (JSON testo minimale) + Output Agente 1 (su testo minimale)
    ```json
    {
      "jobInfo": { ... }, "rating": 5, "feedbackType": "text", "textFeedback": "Ottimo lavoro!", "selectedTags": []
    }
    ```
    * **Output Agente 1:**
        ```json
        {
          "sentiment": "Positivo",
          "extractedFeatures": [] // O solo ["Ottimo lavoro"] poco specifico
        }
        ```
    * **Output atteso:**
        ```json
        {
          "informationLevel": "Medium" // Testo troppo breve e generico
        }
        ```

---

### Formula per il Contributo al Punteggio di Fiducia

Questa formula viene calcolata **dopo** che gli Agenti 1, 2 e 3 hanno completato la loro analisi e fornito i loro output. Combina il rating originale, il contenuto (chips o analisi testo), il livello di informazione e il punteggio di fakeness.

Il risultato `trustScoreContribution` è un valore (positivo o negativo) che verrà *aggiunto* al punteggio di fiducia totale del professionista.

**Componenti e Calcolo:**

1.  **`ratingScore`:** Basato sul rating a stelle.
    * `ratingScore = input_json['rating'] - 2.5`
    * *(Range: da -2.5 per 0 stelle a +2.5 per 5 stelle)*

2.  **`contentScore`:** Basato sul contenuto addizionale (chips o testo).
    * **Se `input_json['feedbackType']` è "chips":**
        * Definisci i valori base per le chips: Positive = +1.0, Negative = -1.0.
        * Calcola la somma dei valori delle chips selezionate: `chipsSum = sum(valore_chip)` per ogni chip in `input_json['selectedTags']`.
        * `contentScore = chipsSum`
        * *(Range: da -12.0 a +12.0)*
    * **Se `input_json['feedbackType']` è "text":**
        * Ottieni il `sentiment` e `extractedFeatures` dall'Output dell'Agente 1.
        * Calcola il valore base dal sentiment: `sentimentBaseValue = +5.0` se sentiment è "Positivo", `0.0` se "Misto" o "Neutro", `-5.0` se "Negativo".
        * Calcola l'aggiustamento dalle feature estratte: `featureAdjustment = sum(valore_feature)`. Definisci i valori: Caratteristica positiva = +1.0, Caratteristica negativa = -1.0. (L'Agente 1 non classifica *direttamente* le feature estratte come positive/negative, ma può inferirlo dal contesto o tu potresti avere una lista mappata; per la formula, assumiamo che l'Agente 1 o il sistema sappia se una feature estratta è positiva o negativa nel contesto del feedback - es. "costoso" è negativa, "puntuale" è positiva).
        * `contentScore = sentimentBaseValue + featureAdjustment`
        * *(Range indicativo: es. -5 - N_neg_features a +5 + N_pos_features)*

3.  **`informationMultiplier`:** Basato sull'Output dell'Agente 3.
    * Se `informationLevel` è "Low": `informationMultiplier = 0.5`
    * Se `informationLevel` è "Medium": `informationMultiplier = 1.0`
    * Se `informationLevel` è "High": `informationMultiplier = 1.5`

4.  **`fakenessMultiplier`:** Basato sull'Output dell'Agente 2.
    * Ottieni `fakeConfidence` dall'Output dell'Agente 2.
    * `fakenessMultiplier = 1.0 - fakeConfidence`
    * *(Range: da 0.0 per fakeConfidence=1.0 a 1.0 per fakeConfidence=0.0)*

5.  **Calcolo Finale `trustScoreContribution`:**
    * `rawContribution = (ratingScore + contentScore * 0.5) * informationMultiplier`
    * *(Nota: Ho aggiunto un peso di 0.5 al `contentScore` per bilanciarlo con il `ratingScore` base, ma questo peso è un suggerimento e può essere calibrato)*
    * `trustScoreContribution = rawContribution * fakenessMultiplier`

**Aggiornamento del Punteggio Globale di Fiducia:**

Il punteggio di fiducia totale per un professionista è un valore cumulativo. Partendo da 0 (Neutro) o da un valore iniziale (es. basato su verifiche iniziali), ogni volta che un nuovo feedback viene processato:

`Nuovo Punteggio di Fiducia Totale = Vecchio Punteggio di Fiducia Totale + trustScoreContribution`

Se vuoi mantenere il punteggio entro un certo range (es. -100 a +100), dovrai implementare una logica di capping.
