import os
import base64
import requests
import pandas as pd
from dotenv import load_dotenv
import streamlit as st
import streamlit_authenticator as stauth
from config_manager import ConfigManager  # Import the ConfigManager class


# Load environment variables from .env file
load_dotenv()

# Load config file
config_manager = ConfigManager()
config = config_manager.config

API_URL_KEY = 'API_URL'
CONFIG_PATH_KEY = 'CONFIG_PATH'

COLOR_MAPPING = {
    'Documento non supportato': 'blue',
    'Controllo non supportato': 'blue',
    'Documento valido': 'lightgreen',
    'Codice corretto': 'lightgreen',
    'Firma presente': 'lightgreen',
    'Documento p7m': 'lightgreen',
    'Dati corretti': 'lightgreen',
    'Compilazione corretta': 'lightgreen',
    'Positivo': 'lightgreen',
    'Documento errato': 'orange',
    'Codice errato': 'orange',
    'Verifica manuale': 'orange',
    'Dati non corrispondenti': 'orange',
    'Compilazione errata': 'orange',
    'Negativo': 'orange',
    'Errore nel controllo': 'yellow',
    'Errori nei controlli': 'yellow',
    'EOF marker not found': 'yellow',
    'Codice assente': 'red',
    'Firma assente': 'red',
    'Campo nullo': 'red',
    'Documento non presente': 'red',
}

def color_cells(val):
    """
    Apply background color to dataframe cells based on their value.

    Args:
        val (str): The value in the dataframe cell.

    Returns:
        str: The CSS style for the background color.
    """    
    return f'background-color: {COLOR_MAPPING.get(val, "white")}'

def get_api_url(endpoint):
    """
    Construct the full API URL based on the endpoint provided.

    Args:
        endpoint (str): The API endpoint.

    Returns:
        str: The full API URL.
    """    
    base_url = os.getenv(API_URL_KEY)
    return f"{base_url}{endpoint}"

def fetch_from_api(endpoint):
    """
    Fetch data from the API for the given endpoint.

    Args:
        endpoint (str): The API endpoint to fetch data from.

    Returns:
        dict or None: The JSON response from the API, or None if an error occurs.
    """
    api_url = get_api_url(endpoint)
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError:
        st.error(f'Failed to fetch data from {endpoint}')
        return None

@st.cache_data(ttl=3600)
def fetch_documents(path):
    """
    Fetch the base64 encoded content of a document from the backend.

    Args:
        path (str): The document path to fetch.

    Returns:
        str: The base64 encoded content of the document or None if an error occurs.
    """    
    data = fetch_from_api(f'document/{path}')
    if data:
        return data.get("file_content_base64")
    return None

@st.cache_data(ttl=3600)
def fetch_data():
    """
    Fetch candidature data from the backend.

    Returns:
        list: A list of unique candidature IDs or None if an error occurs.
    """    
    data = fetch_from_api('data')
    if data:
        df = pd.DataFrame(data)
        return df['candidature_ids'].unique()
    return None

@st.cache_data(ttl=3600)
def fetch_data2(id_candidatura):
    """
    Fetch detailed data for a specific candidature from the backend.

    Args:
        id_candidatura (str): The ID of the candidature to fetch.

    Returns:
        dict: The detailed data for the candidature or None if an error occurs.
    """    
    data = fetch_from_api(f'detail/{id_candidatura}')
    if data:
        return data.get('query')
    return None

# Function to visualize the document
def visualize_document(paths3):
    """
    Visualize a PDF document retrieved from the backend.

    Args:
        paths3 (str): The S3 path of the document to visualize.

    Returns:
        None
    """    
    base64_pdf = fetch_documents(paths3)
    if base64_pdf:
        st.success("File read successfully!")
        st.write("## Selected PDF")
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="900" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.error("Failed to fetch document from API")

def extract_documents(query_data):
    """
    Extract documents information from the query data.

    Args:
        query_data (list): The raw data returned from the backend query.

    Returns:
        pd.DataFrame: DataFrame containing documents information.
    """
    return pd.DataFrame([
        {
            'documentClass': entry['documentClass'],
            'candidatureId': entry['candidatureId'],
            'esitoCheckReason': entry['esitoCheckReason'],
            'documentName': entry['documentName'],
            'documentPathS3': entry['documentPathS3']
        }
        for entry in query_data
    ]).set_index('documentClass')[['esitoCheckReason', 'documentName', 'documentPathS3']]

def extract_checklist(query_data):
    """
    Extract checklist information from the query data.

    Args:
        query_data (list): The raw data returned from the backend query.

    Returns:
        pd.DataFrame: DataFrame containing checklist information, or an empty DataFrame if not found.
    """
    checklist_document = next(
        (doc for doc in query_data if doc['documentClass'] == "Stato_Checklist_Asseverazione"), None
    )

    if not checklist_document:
        st.warning("Checklist document not found.")
        return pd.DataFrame()

    return pd.DataFrame([
        {
            'nomeCheck': check['nomeCheck'],
            'Descrizione': check['Descrizione']
        }
        for check in checklist_document['dettaglioCheck']
    ]).set_index('nomeCheck')[['Descrizione']]

def prepro(query_data):
    """
    Preprocess the query data to extract documents and checklist information.

    Args:
        query_data (list): The raw data returned from the backend query.

    Returns:
        tuple: Two DataFrames, one for the documents and one for the checklist.
    """
    df_documents = extract_documents(query_data)
    df_checklist = extract_checklist(query_data)
    return df_documents, df_checklist


# Function to read and decrypt p7m file
def read_p7m(file_path):
    """
    Read and extract the content of a p7m file.

    Args:
        file_path (str): The file path of the p7m file to read.

    Returns:
        bytes: The extracted content of the p7m file.
    """    
    with open(file_path, "rb") as f:
        data = f.read()
    
    # Parse the PKCS#7 signature
    pkcs7_data = pkcs7.load_pem_pkcs7_signed_data(data)
    
    # Extract the payload content
    content = pkcs7_data.get_payload()
    
    return content

# Function to read a PDF file from bytes and convert it to base64
def read_pdf(file_bytes):
    """
    Convert a PDF file from bytes to a base64 encoded string.

    Args:
        file_bytes (bytes): The bytes of the PDF file.

    Returns:
        str: The base64 encoded string of the PDF file.
    """    
    return base64.b64encode(file_bytes).decode('utf-8')

# Load config file
config_manager = ConfigManager()
config = config_manager.config

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

if st.session_state.get("authentication_status") is None:
    st.warning('Please enter your username and password')
elif not st.session_state["authentication_status"]:
    st.error('Username/password is incorrect')
else:
    # User is authenticated

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

# Save the updated configuration back to the file
config_manager.save_config()