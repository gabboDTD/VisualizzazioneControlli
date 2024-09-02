
# VisualizzazioneControlli

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Poetry](https://img.shields.io/badge/Poetry-1.1.12+-green.svg)

## Descrizione del Progetto
Le verifiche dell'unità di missione richiedono un grande sforzo da parte del personale a causa dei numerosi soggetti coinvolti e della documentazione prodotta, che risulta essere molto varia e contenente errori.

L'obiettivo del progetto è sviluppare l'interfaccia utilizzata per effettuare i controlli sui documenti che sia in grado di:
- Identificare le candidature con documentazione incompleta o incorretta.
- Segnalare i documenti mancanti e quelli contenenti dati non corretti.
- Evidenziare i dati mancanti o incorretti all'interno di ciascun documento di ogni candidatura.

## Funzionalità
1. **Identificazione della Documentazione Incompleta o Inorretta**:
   - L'interfaccia permette di analizzare ogni candidatura per verificare la completezza e la correttezza dei documenti.

2. **Segnalazione dei Documenti Mancanti o Inorretti**:
   - L'interfaccia genera una lista di documenti mancanti o contenenti errori.

3. **Evidenziazione dei Dati Mancanti o Inorretti**:
   - L'interfaccia analizza ogni documento in dettaglio per evidenziare i dati mancanti o incorretti.

## Requisiti
- Python 3.9+
- Poetry

## Installazione
1. Clona il repository:
   ```bash
   git clone https://github.com/gabboDTD/VisualizzazioneControlli.git
   cd VisualizzazioneControlli
   ```

2. Installa le dipendenze utilizzando Poetry:
   ```bash
   poetry install
   ```

3. Attivazione del virtual environment:
   ```bash
   poetry shell
   ```

## Utilizzo
Per avviare l'interfaccia di controllo automatico dei documenti, eseguire:
   ```bash
   cd flask_backend
   python app_v2.py
   
   cd streamlit_frontend
   streamlit run streamlit_app_v2.py
   ```

