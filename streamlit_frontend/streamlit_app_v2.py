import os
import base64
import requests
import pandas as pd
import yaml
from yaml.loader import SafeLoader
from dotenv import load_dotenv
import streamlit as st
import streamlit_authenticator as stauth

# Load environment variables from .env file
load_dotenv()

BLUE = 'blue'
LIGHT_GREEN = 'lightgreen'
ORANGE = 'orange'
YELLOW = 'yellow'
RED = 'red'

API_URL_KEY = 'API_URL'
CONFIG_PATH_KEY = 'CONFIG_PATH'

def color_cells(val):
    color_mapping = {
        'Documento non supportato': BLUE,
        'Controllo non supportato': BLUE,
        'Documento valido': LIGHT_GREEN,
        'Codice corretto': LIGHT_GREEN,
        'Firma presente': LIGHT_GREEN,
        'Documento p7m': LIGHT_GREEN,
        'Dati corretti': LIGHT_GREEN,
        'Compilazione corretta': LIGHT_GREEN,
        'Positivo': LIGHT_GREEN,
        'Documento errato': ORANGE,
        'Codice errato': ORANGE,
        'Verifica manuale': ORANGE,
        'Dati non corrispondenti': ORANGE,
        'Compilazione errata': ORANGE,
        'Negativo': ORANGE,
        'Errore nel controllo': YELLOW,
        'Errori nei controlli': YELLOW,
        'EOF marker not found': YELLOW,
        'Codice assente': RED,
        'Firma assente': RED,
        'Campo nullo': RED,
        'Documento non presente': RED,
    }
    return f'background-color: {color_mapping.get(val, "white")}'

@st.cache_data(ttl=3600)
def fetch_documents(path):
    api_url = os.getenv(API_URL_KEY) + 'document/' + path
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        return data.get("file_content_base64")
    else:
        st.error('Failed to fetch document from backend')
        return None

@st.cache_data(ttl=3600)  # Set Time to live
def fetch_data():
    api_url = os.getenv(API_URL_KEY)+'data'
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
    api_url = os.getenv(API_URL_KEY)+'detail/'+id_candidatura
    response = requests.get(api_url)
    if response.status_code == 200:

        data = response.json()

        # Extract the query data
        query_data = data['query']

        return query_data
    else:
        st.error('Failed to fetch data from backend')
        return None

# Function to visualize the document
def visualize_document(paths3):
    base64_pdf = fetch_documents(paths3)
    if base64_pdf:
        st.success("File read successfully!")
        st.write("## Selected PDF")
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="900" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.error("Failed to fetch document from API")

def prepro(query_data):
    # Extract relevant information for the DataFrame
    records = []
    for entry in query_data:
        records.append({
            'documentClass': entry['documentClass'],
            'candidatureId': entry['candidatureId'],
            'esitoCheckReason': entry['esitoCheckReason'],
            'documentName': entry['documentName'],
            'documentPathS3': entry['documentPathS3']
        })

    # Create a DataFrame
    df_documents = pd.DataFrame(records)

    # Set 'documentClass' as the index
    df_documents.set_index('documentClass', inplace=True)

    # Select only the necessary columns
    df_documents = df_documents[['esitoCheckReason','documentName','documentPathS3']]

    # Find the document with documentClass "Stato_Checklist_Asseverazione"
    checklist_document = next(doc for doc in query_data if doc['documentClass'] == "Stato_Checklist_Asseverazione")

    # if checklist_document 
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

# Function to read and decrypt p7m file
def read_p7m(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    
    # Parse the PKCS#7 signature
    pkcs7_data = pkcs7.load_pem_pkcs7_signed_data(data)
    
    # Extract the payload content
    content = pkcs7_data.get_payload()
    
    return content

# Function to read a PDF file from bytes and convert it to base64
def read_pdf(file_bytes):
    return base64.b64encode(file_bytes).decode('utf-8')

# Load config file
config_path = os.getenv(CONFIG_PATH_KEY, 'config.yaml')
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
    # Logout button in the sidebar
    authenticator.logout("Logout", "sidebar")
    st.sidebar.title("Welcome, {}".format(st.session_state["name"]))

    candidatura_options = fetch_data()

    if candidatura_options is not None:
        st.title('Matrice dei controlli formali')

        st.write("""
        Questa app consente di selezionare una candidatura e visualizzare i dettagli dei controlli formali sui documenti associati. 
        """)

        st.sidebar.title("Ricerca Candidature")
        selected_candidatura = st.sidebar.text_input('Cerca il nome della candidatura')

        if selected_candidatura:
            if selected_candidatura in candidatura_options:
                st.subheader(f"Dettagli per la candidatura '{selected_candidatura}':")
                st.write("""
                Ogni cella contiene un colore che indica se i controlli sul documento sono OK (verde chiaro), se manca il documento (rosso), 
                se il documento contiene errori (arancione), o se il documento non è ancora supportato.
                """)
                query_data = fetch_data2(selected_candidatura)

                ### preprocessing 
                df_documents, df_checklist = prepro(query_data)
                st.write("### Stato dei Documenti")
                st.dataframe(df_documents[['esitoCheckReason']].style.applymap(color_cells))
                document_options = df_documents.index.tolist()
                selected_document = st.sidebar.selectbox('Seleziona il documento', [''] + document_options)

                if selected_document:
                    if selected_document == 'Stato_Checklist_Asseverazione':
                        st.write(f"### Dettagli dei Controlli per il Documento '{selected_document}':")
                        st.dataframe(df_checklist.style.applymap(color_cells))

                        if st.button('Mostra documento'):
                            # Read the file from S3 into memory
                            paths3 = df_documents.loc['Stato_Checklist_Asseverazione','documentPathS3']
                            visualize_document(paths3)

                    else:
                        st.write(f"### Documento non ancora supportato")
            else:
                st.warning("Candidatura non trovata")

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')

# Saving config file
with open(config_path, 'w', encoding='utf-8') as file:
    yaml.dump(config, file, default_flow_style=False)
