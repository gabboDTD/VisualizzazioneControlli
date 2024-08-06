import yaml
import streamlit as st
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities import (CredentialsError, ForgotError, Hasher, LoginError, RegisterError, ResetError, UpdateError)
import requests
import pandas as pd

def color_cells(val):
    color = 'white'
    if val in ['Documento non supportato', 'Controllo non supportato']:
        color = 'blue'
    elif val in ['Documento valido', 'Codice corretto', 'Firma presente', 'Documento p7m', 'Dati corretti', 'Compilazione corretta', 'Positivo']:
        color = 'lightgreen'
    elif val in ['Documento errato', 'Codice errato', 'Verifica manuale', 'Dati non corrispondenti', 'Compilazione errata', 'Negativo']:
        color = 'orange'
    elif val in ['Errore nel controllo', 'Errori nei controlli']:
        color = 'yellow'
    elif val in ['Documento non presente', 'Codice assente', 'Firma assente', 'Campo nullo']:
        color = 'red'
    return f'background-color: {color}'

# Load config file
with open('config.yaml', 'r', encoding='utf-8') as file:
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
except LoginError as e:
    st.error(e)

if st.session_state["authentication_status"]:
    authenticator.logout()
    st.write(f'Welcome *{st.session_state["name"]}*')

    @st.cache_data
    def fetch_data():
        response = requests.get('http://127.0.0.1:5000/api/data')
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame.from_dict(data['df'])
            df_checklist = pd.DataFrame.from_dict(data['df_checklist'])
            return df, df_checklist
        else:
            st.error('Failed to fetch data from backend')
            return None, None

    df, df_checklist = fetch_data()

    if df is not None:
        st.title('Matrice dei controlli formali')

        st.write("""
        Questa app consente di selezionare una candidatura e visualizzare i dettagli dei controlli formali sui documenti associati. 
        Ogni cella contiene un colore che indica se i controlli sul documento sono OK (verde chiaro), se manca il documento (rosso), 
        se il documento contiene errori (arancione), o se il controllo non è supportato.
        """)

        st.sidebar.title("Ricerca Candidature")
        candidatura_options = df.index.unique().tolist()
        selected_candidatura = st.sidebar.text_input('Cerca il nome della candidatura')

        if selected_candidatura:
            if selected_candidatura in df.index:
                st.write(f"Dettagli per la candidatura '{selected_candidatura}':")
                st.dataframe(df.loc[[selected_candidatura]].T.style.applymap(color_cells))
                document_options = df.columns.tolist()
                selected_document = st.sidebar.selectbox('Seleziona il documento', [''] + document_options)

                if selected_document:
                    if selected_document == 'Stato_Checklist_Asseverazione':
                        st.write(f"Dettagli dei controlli per il documento '{selected_document}':")
                        st.dataframe(df_checklist.loc[selected_candidatura, :].to_frame().style.applymap(color_cells))
                    else:
                        st.write(f"Documento non ancora supportato")            
            else:
                st.write("Candidatura non trovata")

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')

# Saving config file
with open('config.yaml', 'w', encoding='utf-8') as file:
    yaml.dump(config, file, default_flow_style=False)
