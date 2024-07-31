import yaml
import streamlit as st
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities import (CredentialsError, ForgotError, Hasher, LoginError, RegisterError, ResetError, UpdateError)
import pandas as pd
import numpy as np
import os

# Function to generate sample data
def generate_sample_data():
    columns = [
        "Stato_Contratto_SA_SR", 
        "Stato_Determina_Affidamento_Aggiudicazione_Servizio", 
        "Stato_Proposta_Commerciale", 
        "Stato_Documento_Stipula_MEPA", 
        "Stato_Convenzione_Accordo", 
        "Stato_Checklist_Asseverazione", 
        "Stato_Certificato_Regolare_Esec", 
        "Stato_Allegato_5"        
    ]
    indices = [
        'CND_141SCU0422X_015254', 'CND_141SCU1222X_079364', 'CND_144COM0422X_014068',
        'CND_131COM1022X_082020', 'CND_141SCU1222X_079707', 'CND_141SCU1222X_079604',
        'CND_131COM1022X_068828', 'CND_141SCU0622X_059144', 'CND_131COM1022X_081830',
        'CND_141SCU0622X_032775'
    ]
    data = [
        ['Documento non supportato'] * 5 + ['Documento valido'] + ['Documento non supportato'] * 2,
        ['Documento non supportato'] * 5 + ['Documento errato'] + ['Documento non supportato'] * 2,
        ['Documento non supportato'] * 5 + ['Documento assente'] + ['Documento non supportato'] * 2,
        ['Documento non supportato'] * 5 + ['Documento valido'] + ['Documento non supportato'] * 2,
        ['Documento non supportato'] * 5 + ['Documento errato'] + ['Documento non supportato'] * 2,
        ['Documento non supportato'] * 5 + ['Documento assente'] + ['Documento non supportato'] * 2,
        ['Documento non supportato'] * 5 + ['Documento valido'] + ['Documento non supportato'] * 2,
        ['Documento non supportato'] * 5 + ['Documento assente'] + ['Documento non supportato'] * 2,
        ['Documento non supportato'] * 5 + ['Documento valido'] + ['Documento non supportato'] * 2,
        ['Documento non supportato'] * 5 + ['Documento errato'] + ['Documento non supportato'] * 2
    ]
    df = pd.DataFrame(data, index=indices, columns=columns)
    return df

def generate_specific_data_checklist():
    columns = [
        "Stato_CUP", "Stato_Firma_Asseveratore", "Stato_Anagrafica_SA",
        "Stato_Compilazione_Checklist", "Esito_Conformità_Tecnica"
    ]
    indices = [
        'CND_141SCU0422X_015254', 'CND_141SCU1222X_079364', 'CND_144COM0422X_014068',
        'CND_131COM1022X_082020', 'CND_141SCU1222X_079707', 'CND_141SCU1222X_079604',
        'CND_131COM1022X_068828', 'CND_141SCU0622X_059144', 'CND_131COM1022X_081830',
        'CND_141SCU0622X_032775'
    ]
    data = [
        ['Codice corretto', 'Firma presente', 'Dati corretti', 'Compilazione corretta', 'Positivo'],
        ['Codice errato', 'Firma assente', 'Dati non corrispondenti', 'Compilazione corretta', 'Positivo'],
        ['Documento assente'] * 5,
        ['Codice corretto', 'Firma presente', 'Dati corretti', 'Compilazione corretta', 'Positivo'],
        ['Codice corretto', 'Verifica manuale', 'Dati corretti', 'Compilazione corretta', 'Positivo'],
        ['Documento assente'] * 5,
        ['Verifica manuale', 'Documento p7m', 'Dati corretti', 'Compilazione corretta', 'Positivo'],
        ['Documento assente'] * 5,
        ['Codice corretto', 'Firma presente', 'Dati corretti', 'Compilazione corretta', 'Positivo'],
        ['Codice corretto', 'Verifica manuale', 'Dati corretti', 'Compilazione errata', 'Positivo']
    ]
    df = pd.DataFrame(data, index=indices, columns=columns)
    return df

def generate_data():
    # Set the random seed for reproducibility
    np.random.seed(42)
    candidature_checklist = pd.read_parquet('/Users/gabbo/Code/Work/GitHub/pdnd-dtd-pad26-pdf/data/candidature_checklist.parquet')
    file_status_report = pd.read_excel('/Users/gabbo/Code/Work/GitHub/pdnd-dtd-pad26-pdf/code/log/file_status_report.xlsx')
    columns = [
        "Stato_Contratto_SA_SR", "Stato_Determina_Affidamento_Aggiudicazione_Servizio",
        "Stato_Proposta_Commerciale", "Stato_Documento_Stipula_MEPA",
        "Stato_Convenzione_Accordo", "Stato_Checklist_Asseverazione",
        "Stato_Certificato_Regolare_Esec", "Stato_Allegato_5"
    ]
    # Initialize the DataFrame with the given columns and index
    df = pd.DataFrame(index=candidature_checklist['nome_candidatura'], columns=columns)

    # Populate "Stato_Checklist_Asseverazione" based on the condition
    df["Stato_Checklist_Asseverazione"] = candidature_checklist['Checklist asseverazione tecnica'].apply(
        lambda x: "Documento assente" if x is None else "Presente"
    ).values

    # Optionally, you can fill other columns with default values or leave them as NaN
    # Here we fill other columns with empty strings for demonstration
    for column in columns:
        if column != "Stato_Checklist_Asseverazione":
            df[column] = "Documento non supportato"

    # Filter the DataFrame
    df_presente = df[df['Stato_Checklist_Asseverazione'] == 'Presente']
    df_assente = df[df['Stato_Checklist_Asseverazione'] == 'Documento assente']

    # Sample 50 rows from each filtered DataFrame
    df_presente_sample = df_presente.sample(n=50, random_state=1)
    df_assente_sample = df_assente.sample(n=50, random_state=1)

    # Assign random values to df_presente_sample['Stato_Checklist_Asseverazione']
    df_presente_sample['Stato_Checklist_Asseverazione'] = np.random.choice(
        ['Documento valido', 'Documento errato'], size=len(df_presente_sample)
    )

    # Concatenate the sampled rows
    df = pd.concat([df_presente_sample, df_assente_sample])

    columns_checklist = [
        "Stato_CUP", "Stato_Firma_Asseveratore", "Stato_Anagrafica_SA",
        "Stato_Compilazione_Checklist", "Esito_Conformità_Tecnica"
    ]

    possible_values = {
        "Stato_CUP": ['Codice corretto', 'Codice assente', 'Codice errato', 'Verifica manuale', 'Controllo non supportato', 'Errore nel controllo', 'Documento assente'],
        "Stato_Firma_Asseveratore": ['Firma presente', 'Documento p7m', 'Firma assente', 'Verifica manuale', 'Controllo non supportato', 'Errore nel controllo', 'Documento assente'],
        "Stato_Anagrafica_SA": ['Dati corretti', 'Dati non corrispondenti', 'Verifica manuale', 'Controllo non supportato', 'Errore nel controllo', 'Documento assente'],
        "Stato_Compilazione_Checklist": ['Compilazione corretta', 'Compilazione errata', 'Verifica manuale', 'Controllo non supportato', 'Errore nel controllo', 'Documento assente'],
        "Esito_Conformità_Tecnica": ['Positivo', 'Negativo', 'Campo nullo', 'Controllo non supportato', 'Errore nel controllo', 'Documento assente']
    }

    # Initialize the DataFrame with the given columns and same index as df
    df_checklist = pd.DataFrame(index=df.index, columns=columns_checklist)

    # Populate the DataFrame based on the conditions
    for idx, row in df.iterrows():
        stato = row['Stato_Checklist_Asseverazione']
        if stato == 'Documento assente':
            df_checklist.loc[idx] = 'Documento assente'
        elif stato == 'Documento valido':
            for column in columns_checklist:
                df_checklist.loc[idx, column] = possible_values[column][0]
        elif stato == 'Documento errato':
            for column in columns_checklist:
                choices = possible_values[column][1:-1]  # Exclude the first value
                df_checklist.loc[idx, column] = np.random.choice(choices)

    return df, df_checklist

def color_cells(val):
    color = 'white'
    if val in ['Documento non supportato', 'Controllo non supportato']:
        color = 'blue'
    elif val in ['Documento valido', 'Codice corretto', 'Firma presente', 'Documento p7m', 'Dati corretti', 'Compilazione corretta', 'Positivo']:
        color = 'lightgreen'
    elif val in ['Documento errato', 'Codice errato', 'Verifica manuale', 'Dati non corrispondenti', 'Compilazione errata', 'Negativo']:
        color = 'orange'
    elif val in ['Errore nel controllo']:
        color = 'yellow'
    elif val in ['Documento assente', 'Codice assente', 'Firma assente', 'Campo nullo']:
        color = 'red'
    return f'background-color: {color}'

# Loading config file
with open('config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Hashing all plain text passwords once
# Hasher.hash_passwords(config['credentials'])

# Creating the authenticator object
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized']
)

# Creating a login widget
try:
    authenticator.login()
except LoginError as e:
    st.error(e)

if st.session_state["authentication_status"]:
    authenticator.logout()
    st.write(f'Welcome *{st.session_state["name"]}*')

    # Path for the Excel file
    excel_file_path = 'candidature_lavorate.xlsx'

    # Load or generate the data
    # df = generate_sample_data()
    # df_checklist = generate_specific_data_checklist()
    df, df_checklist = generate_data()

    # Streamlit App
    st.title('Matrice dei controlli formali')

    st.write("""
    Questa app consente di selezionare una candidatura e visualizzare i dettagli dei controlli formali sui documenti associati. 
    Ogni cella contiene un colore che indica se i controlli sul documento sono OK (verde chiaro), se manca il documento (rosso), 
    se il documento contiene errori (arancione), o se il controllo non è supportato.
    """)

    # Sidebar for search inputs
    st.sidebar.title("Ricerca Candidature")
    candidatura_options = df.index.unique().tolist()
    # Check if the Excel file exists and remove rows from df that are in existing_data
    if os.path.exists(excel_file_path):
        existing_data = pd.read_excel(excel_file_path, header=None)
        if not existing_data.empty:
            existing_indices = existing_data[0].tolist()
            # Remove elements from candidatura_options that are in existing_indices
            candidatura_options = [item for item in candidatura_options if item not in existing_indices]
            # df = df.drop(existing_indices, errors='ignore')

    # selected_candidatura = st.sidebar.selectbox('Seleziona la candidatura', [''] + candidatura_options)
    selected_candidatura = st.sidebar.text_input('Cerca il nome della candidatura')

    if selected_candidatura:
        st.write(f"Dettagli per la candidatura '{selected_candidatura}':")
        st.dataframe(df.loc[[selected_candidatura]].T.style.applymap(color_cells))
        
        # Document selection and Save button in the sidebar
        document_options = df.columns.tolist()
        selected_document = st.sidebar.selectbox('Seleziona il documento', [''] + document_options)

        if st.sidebar.button('Salva come candidatura lavorata'):
            try:
                # Load existing data from Excel file or create a new DataFrame
                if os.path.exists(excel_file_path):
                    existing_data = pd.read_excel(excel_file_path, header=None)
                    new_data = pd.DataFrame([[selected_candidatura, st.session_state["username"]]])
                    all_data = pd.concat([existing_data, new_data], ignore_index=True)
                else:
                    all_data = pd.DataFrame([[selected_candidatura, st.session_state["username"]]])

                # Write the data to Excel
                all_data.to_excel(excel_file_path, index=False, header=False)
                st.success(f"La candidatura '{selected_candidatura}' è stata salvata su {excel_file_path} e non verrà più presentata!")
                st.experimental_rerun()

            except Exception as e:
                st.error(f"Error writing to Excel: {e}")

        if selected_document:
            if selected_document == 'Stato_Checklist_Asseverazione':
                st.write(f"Dettagli dei controlli per il documento '{selected_document}':")
                st.dataframe(df_checklist.loc[selected_candidatura, :].to_frame().style.applymap(color_cells))
            else:
                st.write(f"Documento non ancora supportato")

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')

# # Creating a password reset widget
# if st.session_state["authentication_status"]:
#     try:
#         if authenticator.reset_password(st.session_state["username"]):
#             st.success('Password modified successfully')
#     except ResetError as e:
#         st.error(e)
#     except CredentialsError as e:
#         st.error(e)

# # Creating a new user registration widget
# try:
#     (email_of_registered_user,
#      username_of_registered_user,
#      name_of_registered_user) = authenticator.register_user(pre_authorization=False)
#     if email_of_registered_user:
#         st.success('User registered successfully')
# except RegisterError as e:
#     st.error(e)

# # Creating a forgot password widget
# try:
#     (username_of_forgotten_password,
#      email_of_forgotten_password,
#      new_random_password) = authenticator.forgot_password()
#     if username_of_forgotten_password:
#         st.success('New password sent securely')
#         # Random password to be transferred to the user securely
#     elif not username_of_forgotten_password:
#         st.error('Username not found')
# except ForgotError as e:
#     st.error(e)

# # Creating a forgot username widget
# try:
#     (username_of_forgotten_username,
#      email_of_forgotten_username) = authenticator.forgot_username()
#     if username_of_forgotten_username:
#         st.success('Username sent securely')
#         # Username to be transferred to the user securely
#     elif not username_of_forgotten_username:
#         st.error('Email not found')
# except ForgotError as e:
#     st.error(e)

# # Creating an update user details widget
# if st.session_state["authentication_status"]:
#     try:
#         if authenticator.update_user_details(st.session_state["username"]):
#             st.success('Entries updated successfully')
#     except UpdateError as e:
#         st.error(e)

# Saving config file
with open('config.yaml', 'w', encoding='utf-8') as file:
    yaml.dump(config, file, default_flow_style=False)
