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
        ['Documento non supportato'] * 5 + ['Documento non presente'] + ['Documento non supportato'] * 2,
        ['Documento non supportato'] * 5 + ['Documento valido'] + ['Documento non supportato'] * 2,
        ['Documento non supportato'] * 5 + ['Documento errato'] + ['Documento non supportato'] * 2,
        ['Documento non supportato'] * 5 + ['Documento non presente'] + ['Documento non supportato'] * 2,
        ['Documento non supportato'] * 5 + ['Documento valido'] + ['Documento non supportato'] * 2,
        ['Documento non supportato'] * 5 + ['Documento non presente'] + ['Documento non supportato'] * 2,
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
        ['Documento non presente'] * 5,
        ['Codice corretto', 'Firma presente', 'Dati corretti', 'Compilazione corretta', 'Positivo'],
        ['Codice corretto', 'Verifica manuale', 'Dati corretti', 'Compilazione corretta', 'Positivo'],
        ['Documento non presente'] * 5,
        ['Verifica manuale', 'Documento p7m', 'Dati corretti', 'Compilazione corretta', 'Positivo'],
        ['Documento non presente'] * 5,
        ['Codice corretto', 'Firma presente', 'Dati corretti', 'Compilazione corretta', 'Positivo'],
        ['Codice corretto', 'Verifica manuale', 'Dati corretti', 'Compilazione errata', 'Positivo']
    ]
    df = pd.DataFrame(data, index=indices, columns=columns)
    return df

# Populate the Stato_Checklist_Asseverazione column based on the given logic
def determine_stato_checklist(row):
    if row['Stato_Firma_Asseveratore'] == 'Documento non presente':
        return 'Documento non presente'
    elif row['Stato_Firma_Asseveratore'] in ['Firma presente', 'Documento p7m'] and row['Esito_Conformità_Tecnica'] == 'Positivo':
        return 'Documento valido'
    elif row['Stato_Firma_Asseveratore'] in ['Firma assente', 'Verifica manuale'] or row['Esito_Conformità_Tecnica'] in ['Negativo', 'Campo nullo']:
        return 'Documento errato'
    elif row['Stato_Firma_Asseveratore'] in ['Errore nel controllo'] or row['Esito_Conformità_Tecnica'] in ['Errore nel controllo']:
        return 'Errori nei controlli'
    else:
        return ''

# Validation function
def validate_df_columns_and_values(df, possible_values):
    # Check columns
    if set(df.columns) != set(possible_values.keys()):
        return False, f"Columns do not match. Expected {possible_values.keys()}, got {df.columns.tolist()}"

    # Check values
    invalid_entries = {}
    for column in possible_values.keys():
        invalid_values = df[~df[column].isin(possible_values[column])][column].unique()
        if len(invalid_values) > 0:
            invalid_entries[column] = invalid_values.tolist()

    if invalid_entries:
        return False, f"Invalid values found:\n{invalid_entries}"
    
    return True, "All columns and values are valid."


def generate_data():

    candidature_checklist = pd.read_parquet('/Users/gabbo/Code/Work/GitHub/pdnd-dtd-pad26-pdf/data/20240805_candidature_checklist.parquet')
    file_status_report = pd.read_excel('/Users/gabbo/Code/Work/GitHub/pdnd-dtd-pad26-pdf/code/log/20240805_file_status_report_all.xlsx')
    # Ensure indices are aligned properly before assigning values
    file_status_report.set_index('Candidatura', inplace=True)

    possible_values_documenti = {
        "Stato_Contratto_SA_SR":                                ["Documento valido", "Documento non presente", "Documento errato", "Documento non supportato", "Errori nei controlli"], 
        "Stato_Determina_Affidamento_Aggiudicazione_Servizio":  ["Documento valido", "Documento non presente", "Documento errato", "Documento non supportato", "Errori nei controlli"], 
        "Stato_Proposta_Commerciale":                           ["Documento valido", "Documento non presente", "Documento errato", "Documento non supportato", "Errori nei controlli"], 
        "Stato_Documento_Stipula_MEPA":                         ["Documento valido", "Documento non presente", "Documento errato", "Documento non supportato", "Errori nei controlli"], 
        "Stato_Convenzione_Accordo":                            ["Documento valido", "Documento non presente", "Documento errato", "Documento non supportato", "Errori nei controlli"], 
        "Stato_Checklist_Asseverazione":                        ["Documento valido", "Documento non presente", "Documento errato", "Documento non supportato", "Errori nei controlli"], 
        "Stato_Certificato_Regolare_Esec":                      ["Documento valido", "Documento non presente", "Documento errato", "Documento non supportato", "Errori nei controlli"], 
        "Stato_Allegato_5":                                     ["Documento valido", "Documento non presente", "Documento errato", "Documento non supportato", "Errori nei controlli"], 
        }
    
    # Derive columns_checklist from the keys of possible_values_checklist
    columns_documenti = list(possible_values_documenti.keys())

    possible_values_checklist = {
        "Stato_CUP":                    ['Codice corretto',                     'Codice errato', 'Codice assente',      'Verifica manuale', 'Controllo non supportato', 'Errore nel controllo', 'Documento non presente'],
        "Stato_Firma_Asseveratore":     ['Firma presente', 'Documento p7m',     'Firma assente',                        'Verifica manuale', 'Controllo non supportato', 'Errore nel controllo', 'Documento non presente'],
        "Stato_Anagrafica_SA":          ['Dati corretti',                       'Dati non corrispondenti',              'Verifica manuale', 'Controllo non supportato', 'Errore nel controllo', 'Documento non presente'],
        "Stato_Compilazione_Checklist": ['Compilazione corretta',               'Compilazione errata',                  'Verifica manuale', 'Controllo non supportato', 'Errore nel controllo', 'Documento non presente'],
        "Esito_Conformità_Tecnica":     ['Positivo',                            'Negativo', 'Campo nullo',              'Verifica manuale', 'Controllo non supportato', 'Errore nel controllo', 'Documento non presente']
    }

    # Derive columns_checklist from the keys of possible_values_checklist
    columns_checklist = list(possible_values_checklist.keys())

    # Initialize the DataFrame with the given columns and index
    df_checklist = pd.DataFrame(index=file_status_report.index,columns=columns_checklist)
    df = pd.DataFrame(index=file_status_report.index, columns=columns_documenti)

    df_checklist['Stato_CUP']='Controllo non supportato'
    df_checklist['Stato_Firma_Asseveratore']=file_status_report['Status']
    df_checklist.loc[df_checklist['Stato_Firma_Asseveratore']=='EOF marker not found','Stato_Firma_Asseveratore']='Errore nel controllo'
    df_checklist['Stato_Anagrafica_SA']='Controllo non supportato'
    df_checklist['Stato_Compilazione_Checklist']='Controllo non supportato'
    df_checklist['Esito_Conformità_Tecnica']=file_status_report['Esito']
    df_checklist.loc[df_checklist['Esito_Conformità_Tecnica']=='EOF marker not found','Esito_Conformità_Tecnica']='Errore nel controllo'

    # Populate the Stato_Checklist_Asseverazione column based on the given logic
    df['Stato_Checklist_Asseverazione'] = df_checklist.apply(determine_stato_checklist, axis=1)

    # Optionally, you can fill other columns with default values or leave them as NaN
    # Here we fill other columns with empty strings for demonstration
    for column in columns_documenti:
        if column != "Stato_Checklist_Asseverazione":
            df[column] = "Documento non supportato"

    # Validate the df_checklist DataFrame
    is_valid, message = validate_df_columns_and_values(df_checklist, possible_values_checklist)
    print(message)

    # Validate the df DataFrame
    is_valid, message = validate_df_columns_and_values(df, possible_values_documenti)
    print(message)


    return df, df_checklist

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
    # # Check if the Excel file exists and remove rows from df that are in existing_data
    # if os.path.exists(excel_file_path):
    #     existing_data = pd.read_excel(excel_file_path, header=None)
    #     if not existing_data.empty:
    #         existing_indices = existing_data[0].tolist()
    #         # Remove elements from candidatura_options that are in existing_indices
    #         candidatura_options = [item for item in candidatura_options if item not in existing_indices]
    #         # df = df.drop(existing_indices, errors='ignore')

    # selected_candidatura = st.sidebar.selectbox('Seleziona la candidatura', [''] + candidatura_options)
    selected_candidatura = st.sidebar.text_input('Cerca il nome della candidatura')

    if selected_candidatura:

        if selected_candidatura in df.index:
            st.write(f"Dettagli per la candidatura '{selected_candidatura}':")
            st.dataframe(df.loc[[selected_candidatura]].T.style.applymap(color_cells))
            
            # Document selection and Save button in the sidebar
            document_options = df.columns.tolist()
            selected_document = st.sidebar.selectbox('Seleziona il documento', [''] + document_options)

            # if st.sidebar.button('Salva come candidatura lavorata'):
            #     try:
            #         # Load existing data from Excel file or create a new DataFrame
            #         if os.path.exists(excel_file_path):
            #             existing_data = pd.read_excel(excel_file_path, header=None)
            #             new_data = pd.DataFrame([[selected_candidatura, st.session_state["username"]]])
            #             all_data = pd.concat([existing_data, new_data], ignore_index=True)
            #         else:
            #             all_data = pd.DataFrame([[selected_candidatura, st.session_state["username"]]])

            #         # Write the data to Excel
            #         all_data.to_excel(excel_file_path, index=False, header=False)
            #         st.success(f"La candidatura '{selected_candidatura}' è stata salvata su {excel_file_path} e non verrà più presentata!")
            #         st.experimental_rerun()

            #     except Exception as e:
            #         st.error(f"Error writing to Excel: {e}")

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
