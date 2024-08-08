import os
import yaml
import streamlit as st
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import requests
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def color_cells(val):
    color = 'white'
    if val in ['Documento non supportato', 'Controllo non supportato']:
        color = 'blue'
    elif val in ['Documento valido', 'Codice corretto', 'Firma presente', 'Documento p7m', 'Dati corretti', 'Compilazione corretta', 'Positivo']:
        color = 'lightgreen'
    elif val in ['Documento errato', 'Codice errato', 'Verifica manuale', 'Dati non corrispondenti', 'Compilazione errata', 'Negativo']:
        color = 'orange'
    elif val in ['Errore nel controllo', 'Errori nei controlli', 'EOF marker not found']:
        color = 'yellow'
    elif val in ['Documento non presente', 'Codice assente', 'Firma assente', 'Campo nullo']:
        color = 'red'
    return f'background-color: {color}'

@st.cache_data(ttl=3600)  # Set Time to live
def fetch_data():
    api_url = os.getenv('API_URL')+'data'
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        # Convert the JSON data to a DataFrame
        df = pd.DataFrame(data)
        candidatura_options = df['candidature_ids'].unique()
        return candidatura_options
    else:
        st.error('Failed to fetch data from backend')
        return None

@st.cache_data(ttl=3600)  # Set time to live
def fetch_data2(id_candidatura):
    api_url = os.getenv('API_URL')+'detail/'+id_candidatura
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()

        # Extract the query data
        query_data = data['query']

        # Extract relevant information for the DataFrame
        records = []
        for entry in query_data:
            records.append({
                'documentClass': entry['documentClass'],
                'candidatureId': entry['candidatureId'],
                'esitoCheckReason': entry['esitoCheckReason']
            })

        # Create a DataFrame
        df_documents = pd.DataFrame(records)

        # Set 'documentClass' as the index
        df_documents.set_index('documentClass', inplace=True)

        # Select only the 'candidatureId' and 'esitoCheckReason' columns
        df_documents = df_documents[['esitoCheckReason']]

        # Find the document with documentClass "Stato_Checklist_Asseverazione"
        checklist_document = next(doc for doc in query_data if doc['documentClass'] == "Stato_Checklist_Asseverazione")

        # Extract relevant information for the DataFrame
        records = []
        for check in checklist_document['dettaglioCheck']:
            records.append({
                'nomeCheck': check['nomeCheck'],
                'candidatureId': checklist_document['candidatureId'],
                'Descrizione': check['Descrizione']
            })

        # Create a DataFrame
        df_checklist = pd.DataFrame(records)

        # Set 'nomeCheck' as the index
        df_checklist.set_index('nomeCheck', inplace=True)

        # Select only the 'candidatureId' and 'Descrizione' columns
        df_checklist = df_checklist[['Descrizione']]

        return df_documents, df_checklist
    else:
        st.error('Failed to fetch data from backend')
        return None, None

# Load config file
config_path = os.getenv('CONFIG_PATH', 'config.yaml')
with open(config_path, 'r', encoding='utf-8') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Create the authenticator object
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized']
)

# Create a login widget
try:
    authenticator.login()
except stauth.LoginError as e:
    st.error(e)

if st.session_state["authentication_status"]:
    authenticator.logout()
    st.write(f'Welcome *{st.session_state["name"]}*')

    candidatura_options = fetch_data()

    if candidatura_options is not None:
        st.title('Matrice dei controlli formali')

        st.write("""
        Questa app consente di selezionare una candidatura e visualizzare i dettagli dei controlli formali sui documenti associati. 
        Ogni cella contiene un colore che indica se i controlli sul documento sono OK (verde chiaro), se manca il documento (rosso), 
        se il documento contiene errori (arancione), o se il controllo non è supportato.
        """)

        st.sidebar.title("Ricerca Candidature")
        selected_candidatura = st.sidebar.text_input('Cerca il nome della candidatura')

        if selected_candidatura:
            if selected_candidatura in candidatura_options:
                st.write(f"Dettagli per la candidatura '{selected_candidatura}':")
                df_documents, df_checklist = fetch_data2(selected_candidatura)
                st.dataframe(df_documents.style.applymap(color_cells))
                document_options = df_documents.index.tolist()
                selected_document = st.sidebar.selectbox('Seleziona il documento', [''] + document_options)

                if selected_document:
                    if selected_document == 'Stato_Checklist_Asseverazione':
                        st.write(f"Dettagli dei controlli per il documento '{selected_document}':")
                        st.dataframe(df_checklist.style.applymap(color_cells))
                    else:
                        st.write(f"Documento non ancora supportato")            
            else:
                st.write("Candidatura non trovata")

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')

# Saving config file
with open(config_path, 'w', encoding='utf-8') as file:
    yaml.dump(config, file, default_flow_style=False)
