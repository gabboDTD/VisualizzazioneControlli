import os
import base64
import requests
import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
from config_manager import ConfigManager  # Import the ConfigManager class
from cryptography.hazmat.primitives.serialization import pkcs7

# Custom CSS for styling
st.markdown(
    """
    <style>
    /* Set the background color of the sidebar */
    .css-18e3th9 {
        background-color: #0056b3;  /* Blue background */
        display: flex;
        flex-direction: column;
        justify-content: flex-start;  /* Align content to the top */
        padding-top: 20px; /* Adjust padding to align with the main content */
    }
    
    /* Center logo vertically within the sidebar */
    .logo-container {
        padding-top: 0px;
        padding-bottom: 20px;
        margin-top: 0;
    }
    
    /* Set the font color and style for the sidebar */
    .css-18e3th9, .css-1d391kg, .css-1v3fvcr, .css-1l02zno {
        color: white;  /* White text */
        font-family: 'Helvetica', sans-serif;
    }
    
    /* Set the main content background and font style */
    .css-1outpf7 {
        background-color: #f7f9fc;  /* Light gray background */
        color: #0056b3;  /* Blue text */
        font-family: 'Helvetica', sans-serif;
        padding-top: 20px;  /* Align with the logo */
    }
    
    /* Style the header */
    .css-145kmo2 {
        font-size: 24px;
        font-weight: bold;
        color: #003366;  /* Darker blue */
        margin-top: 0; /* Remove top margin for alignment */
        padding-top: 0px; /* Ensure it aligns with the sidebar */
    }

    /* Style the subheaders */
    .css-1cpxqw2 {
        color: #003366;  /* Darker blue */
        font-size: 20px;
        font-weight: bold;
    }

    /* Button styling */
    .stButton button {
        background-color: #0056b3;  /* Blue button */
        color: white;  /* White text */
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
    }
    
    .stButton button:hover {
        background-color: #003366;  /* Darker blue on hover */
    }
    
    </style>
    """, unsafe_allow_html=True
)

# Load config file
config_manager = ConfigManager()
config = config_manager.config

# Ensure all necessary config fields are present
try:
    base_url = config['api_url']
    credentials = config['credentials']
    cookie_config = config['cookie']
except KeyError as e:
    st.error(f"Missing configuration key: {e}")
    st.stop()

COLOR_MAPPING = {
    'Documento non supportato': '#1E90FF',
    'Controllo non supportato': '#1E90FF',
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
    base_url = config['api_url']
    if not base_url:
        st.error("API URL is not configured.")
        return None
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
    if not api_url:
        return None
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch data from {endpoint}: {e}")
        return None

@st.cache_data(ttl=3600)
def fetch_documents(path: str):
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
def fetch_candidature_ids():
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
def fetch_candidature_details(id_candidatura: str):
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
def visualize_document(paths3: str):
    """
    Visualize a PDF document retrieved from the backend.

    Args:
        paths3 (str): The S3 path of the document to visualize.

    Returns:
        None
    """    
    if not paths3:
        st.error("No valid document path provided.")
        return

    base64_pdf = fetch_documents(paths3)
    if base64_pdf:
        st.success("File read successfully!")
        st.write("## Documento selezionato")
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="900" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.error("Failed to fetch document from API")

def extract_documents(query_data: list):
    """
    Extract documents information from the query data.

    Args:
        query_data (list): The raw data returned from the backend query.

    Returns:
        pd.DataFrame: DataFrame containing documents information.
    """
    return pd.DataFrame([
        {
            'Documento': entry['documentClass'],
            'candidatureId': entry['candidatureId'],
            'Esito controlli': entry['esitoCheckReason'],
            'documentName': entry['documentName'],
            'documentPathS3': entry['documentPathS3']
        }
        for entry in query_data
    ]).set_index('Documento')[['Esito controlli', 'documentName', 'documentPathS3']]

def extract_checklist(query_data: list):
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
            'Controllo': check['nomeCheck'],
            'Esito': check['Descrizione']
        }
        for check in checklist_document['dettaglioCheck']
    ]).set_index('Controllo')[['Esito']]

import pandas as pd

def rename_dataframe_index(df):
    """
    Rename the index of a DataFrame according to a specified mapping.
    
    This function takes a DataFrame with specific index labels and renames those labels 
    based on a predefined mapping. It modifies the DataFrame in place.

    Parameters:
    df (pd.DataFrame): The DataFrame whose index is to be renamed.

    Returns:
    pd.DataFrame: The DataFrame with the renamed index.    
    """
    index_mapping = {
        "Stato_Checklist_Asseverazione": "Checklist di asseverazione",
        "Stato_Contratto_SA_SR": "Contratto soggetto attuatore soggetto realizzatore",
        "Stato_Determina_Affidamento_Aggiudicazione_Servizio": "Determina affidamento, aggiudicazione servizio",
        "Stato_Proposta_Commerciale": "Proposta commerciale",
        "Stato_Documento_Stipula_MEPA": "Documento stipula MEPA",
        "Stato_Convenzione_Accordo": "Convenzione accordo",
        "Stato_Certificato_Regolare_Esec": "Certificato regolare esecuzione",
        "Stato_Allegato_5": "Allegato 5"
    }
    
    df.rename(index=index_mapping, inplace=True)
    return df

def rename_controlli_checklist_index(df):
    """
    Rename the index of a DataFrame according to a specified mapping.
    
    This function takes a DataFrame with specific index labels and renames those labels 
    based on a predefined mapping. It modifies the DataFrame in place.

    Parameters:
    df (pd.DataFrame): The DataFrame whose index is to be renamed.

    Returns:
    pd.DataFrame: The DataFrame with the renamed index.    
    """
    index_mapping = {
        "Stato_CUP": "CUP",
        "Stato_Firma_Asseveratore": "Firma asseveratore",
        "Stato_Anagrafica_SA": "Anagrafica soggetto attuatore",
        "Stato_Compilazione_Checklist": "Compilazione checklist",
        "Esito_Conformità_Tecnica": "Esito conformità tecnica",
    }
    
    df.rename(index=index_mapping, inplace=True)
    return df

def prepro(query_data: list):
    """
    Preprocess the query data to extract documents and checklist information.

    Args:
        query_data (list): The raw data returned from the backend query.

    Returns:
        tuple: Two DataFrames, one for the documents and one for the checklist.
    """
    df_documents = extract_documents(query_data)
    df_documents = rename_dataframe_index(df_documents)

    df_checklist = extract_checklist(query_data)
    df_checklist = rename_controlli_checklist_index(df_checklist)
    return df_documents, df_checklist

# Function to read and decrypt p7m file
def read_p7m(file_path: str):
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
def read_pdf(file_bytes: bytes):
    """
    Convert a PDF file from bytes to a base64 encoded string.

    Args:
        file_bytes (bytes): The bytes of the PDF file.

    Returns:
        str: The base64 encoded string of the PDF file.
    """    
    return base64.b64encode(file_bytes).decode('utf-8')

# Create the authenticator object
authenticator = stauth.Authenticate(
    credentials,
    cookie_config['name'],
    cookie_config['key'],
    cookie_config['expiry_days'],
    config['pre-authorized']
)

# Create a login widget
try:
    authenticator.login()
except stauth.LoginError as e:
    st.error(e)
    st.stop()

# Check authentication status
if st.session_state.get("authentication_status") is None:
    st.warning('Please enter your username and password')
    st.stop()
elif not st.session_state["authentication_status"]:
    st.error('Username/password is incorrect')
    st.stop()
else:
    # User is authenticated

    # Add SVG logo in the sidebar
    st.sidebar.markdown(
        """
        <div class="logo-container">
            <img src="data:image/svg+xml;base64,{encoded_svg}" />
        </div>
        """.format(encoded_svg=base64.b64encode(open("blue-nofill-text-bottom.svg", "rb").read()).decode("utf-8")),
        unsafe_allow_html=True
    )

    # Sidebar title and logout button
    st.sidebar.title(f"Benvenuto, {st.session_state['name']}")
    authenticator.logout("Logout", "sidebar")

    candidatura_options = fetch_candidature_ids()

    if candidatura_options is not None:
        st.title('Matrice dei controlli formali')

        st.write("""
        Questa applicazione ti permette di selezionare una candidatura e visualizzare i dettagli dei controlli formali sui documenti ad essa associati. 
        """)

        st.sidebar.title("Cerca la candidatura")
        selected_candidatura = st.sidebar.text_input('Inserisci il nome della candidatura', key='selected_candidatura', autocomplete='on')
        # selected_candidatura = st.sidebar.selectbox(
        #     label='Nome candidatura', 
        #     options=[''] + candidatura_options,
        #     key='selected_candidatura'
        # )
        # Reset selected_document when selected_candidatura changes
        if st.session_state.get('selected_document') and st.session_state['selected_candidatura'] != st.session_state.get('previous_candidatura'):
            st.session_state['selected_document'] = ''
        
        st.session_state['previous_candidatura'] = st.session_state['selected_candidatura']

        if selected_candidatura:
            if selected_candidatura in candidatura_options:
                # st.subheader(f"Dettagli della candidatura {selected_candidatura}:")
                # st.write("""
                # Il colore di ogni cella indica lo stato del controllo del documento: verde chiaro se il controllo è positivo, rosso se il documento manca, 
                # arancione se ci sono errori, e blu se il documento non è supportato.
                # """)
                query_data = fetch_candidature_details(selected_candidatura)

                if query_data:
                    ### preprocessing 
                    df_documents, df_checklist = prepro(query_data)
                    st.write(f"### Stato dei controlli per i documenti della candidatura {selected_candidatura}")
                    if not df_documents.empty:
                        # st.dataframe(df_documents[['Esito controlli']].style.map(color_cells).set_properties(**{'text-align': 'center'}))  # Improved text alignment
                        st.dataframe(df_documents[['Esito controlli']].style.set_properties(**{'text-align': 'center'}))  # Improved text alignment
                        document_options = df_documents.index.tolist()
                        selected_document = st.sidebar.selectbox(
                            label='Scegli il documento su cui effettuare i controlli', 
                            options=[''] + document_options,
                            key='selected_document'
                        )
                        if selected_document:
                            if selected_document == 'Checklist di asseverazione':
                                st.write(f"### Dettagli dei controlli per il documento:<br>{selected_document}", unsafe_allow_html=True)
                                if not df_checklist.empty:
                                    # st.dataframe(df_checklist.style.map(color_cells).set_properties(**{'text-align': 'center'}))  # Improved text alignment
                                    st.dataframe(df_checklist.style.set_properties(**{'text-align': 'center'}))  # Improved text alignment

                                if st.button('Mostra documento'):
                                    paths3 = df_documents.loc[selected_document, 'documentPathS3']
                                    visualize_document(paths3)
                            else:
                                st.write(f"### Documento non ancora supportato")
                    else:
                        st.warning("Nessun documento disponibile.")
                else:
                    st.warning("Nessun dato trovato per la candidatura selezionata.")
            else:
                st.warning("Candidatura non trovata")

# Save the updated configuration back to the file
# config_manager.save_config()
