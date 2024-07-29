import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import os 

# Sample DataFrame generation
def generate_sample_data():
    # Define the columns and rows
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
        'CND_141SCU0422X_015254',
        'CND_141SCU1222X_079364',
        'CND_144COM0422X_014068',
        'CND_131COM1022X_082020',
        'CND_141SCU1222X_079707',
        'CND_141SCU1222X_079604',
        'CND_131COM1022X_068828',
        'CND_141SCU0622X_059144',
        'CND_131COM1022X_081830',
        'CND_141SCU0622X_032775'
    ]

    # Create a fixed DataFrame
    data = [
        ['Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Documento valido',  'Controllo non eseguito', 'Controllo non eseguito'  ],
        ['Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Documento errato',  'Controllo non eseguito', 'Controllo non eseguito'  ],
        ['Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Documento assente', 'Controllo non eseguito', 'Controllo non eseguito'  ],
        ['Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Documento valido',  'Controllo non eseguito', 'Controllo non eseguito'  ],
        ['Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Documento errato',  'Controllo non eseguito', 'Controllo non eseguito'  ],
        ['Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Documento assente', 'Controllo non eseguito', 'Controllo non eseguito'  ],
        ['Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Documento valido',  'Controllo non eseguito', 'Controllo non eseguito'  ],
        ['Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Documento assente', 'Controllo non eseguito', 'Controllo non eseguito'  ],
        ['Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Documento valido',  'Controllo non eseguito', 'Controllo non eseguito'  ],
        ['Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Controllo non eseguito', 'Documento errato',  'Controllo non eseguito', 'Controllo non eseguito'   ]
    ]
    df = pd.DataFrame(data, index=indices[0:len(data)], columns=columns)

    return df

def generate_specific_data_checklist():
    # Define the columns and rows
    columns = [
        "Stato_CUP",
        "Stato_Firma_Asseveratore",
        "Stato_Anagrafica_SA",
        "Stato_Compilazione_Checklist",
        "Esito_Conformità_Tecnica"
    ]

    indices = [
        'CND_141SCU0422X_015254',
        'CND_141SCU1222X_079364',
        'CND_144COM0422X_014068',
        'CND_131COM1022X_082020',
        'CND_141SCU1222X_079707',
        'CND_141SCU1222X_079604',
        'CND_131COM1022X_068828',
        'CND_141SCU0622X_059144',
        'CND_131COM1022X_081830',
        'CND_141SCU0622X_032775'
    ]
    
    data = [
        ['Codice corretto',     'Firma presente',       'Dati corretti',           'Compilazione corretta',    'Positivo',],
        ['Codice errato',       'Firma assente',        'Dati non corrispondenti',  'Compilazione corretta',    'Positivo',],
        ['Documento assente',   'Documento assente',    'Documento assente',        'Documento assente',        'Documento assente',],
        ['Codice corretto',     'Firma presente',       'Dati corretti',           'Compilazione corretta',    'Positivo',],
        ['Codice corretto',     'Verifica manuale',     'Dati corretti',           'Compilazione corretta',    'Positivo',],
        ['Documento assente',   'Documento assente',    'Documento assente',        'Documento assente',        'Documento assente',],
        ['Verifica manuale',    'Documento p7m',        'Dati corretti',           'Compilazione corretta',    'Positivo',],
        ['Documento assente',   'Documento assente',    'Documento assente',        'Documento assente',        'Documento assente',],
        ['Codice corretto',     'Firma presente',       'Dati corretti',           'Compilazione corretta',    'Positivo',],
        ['Codice corretto',     'Controllare',          'Dati corretti',           'Compilazione errata',      'Positivo',],
    ]

    df = pd.DataFrame(data, index=indices[0:len(data)], columns=columns)
    return df

# Function to color the cells
def color_cells(val):
    color = 'white'
    if val in ['Controllo non eseguito']:
        color = 'blue'    
    if val in ['Documento valido', 'Codice corretto', 'Firma presente', 'Documento p7m', 'Dati corretti', 'Compilazione corretta', 'Positivo']:
        color = 'lightgreen'
    elif val in ['Documento errato', 'Codice errato', 'Verifica manuale', 'Dati non corrispondenti', 'Compilazione errata', 'Negativo']:
        color = 'orange'
    elif val in ['Errore nel controllo']:
        color = 'yellow'
    elif val in ['Documento assente', 'Codice assente', 'Firma assente', 'Campo nullo']:
        color = 'red'
    return f'background-color: {color}'

# Path for the Excel file
excel_file_path = 'candidature_lavorate.xlsx'

# Load or generate the data
df = generate_sample_data()
df_checklist = generate_specific_data_checklist()

# Streamlit App
st.title('Matrice dei controlli formali')

st.write("""
Questa app visualizza una tabella in cui ogni riga è una candidatura in asseverazione formale,
ogni colonna è un documento da controllare, e ogni cella contiene un colore che indica se i controlli sul documento sono OK,
se manca il documento (rosso), o se il documento contiene errori (arancione)
""")

# Sidebar for search inputs and rerun button
st.sidebar.title("Ricerca Candidature")
candidatura_search = st.sidebar.text_input('Cerca il nome della candidatura')
column_search = st.sidebar.selectbox('Seleziona il nome del documento', df.columns)
if st.sidebar.button('Rerun'):
    st.experimental_rerun()

# Check if the Excel file exists and remove rows from df that are in existing_data
if os.path.exists(excel_file_path):
    existing_data = pd.read_excel(excel_file_path, header=None)
    existing_indices = existing_data[0].tolist()
    df = df.drop(existing_indices, errors='ignore')

if candidatura_search and column_search:
    if column_search in df.columns:
        filtered_df = df[df.index.str.contains(candidatura_search, case=False)]
        if not filtered_df.empty:
            # st.write(f"Risultati per '{candidatura_search}' e '{column_search}':")
            # st.dataframe(filtered_df[[column_search]].style.applymap(color_cells))
            
            # Check if a specific cell is clicked and display df_checklist
            if candidatura_search in df.index and column_search in df.columns:
                selected_value = df.loc[candidatura_search, column_search]
                if selected_value in ['Documento assente', 'Documento errato', 'Documento valido']:
                    st.write(f"Dettagli per la candidatura '{candidatura_search}' e documento '{column_search}':")              
                    st.dataframe(df_checklist.loc[[candidatura_search]].style.applymap(color_cells))
                    # Button to append the index to the Excel file
                    if st.button('Salva come candidatura lavorata'):
                        try:
                            # Load existing data from Excel file or create a new DataFrame
                            if os.path.exists(excel_file_path):
                                existing_data = pd.read_excel(excel_file_path, header=None)
                                new_data = pd.DataFrame([candidatura_search])
                                all_data = pd.concat([existing_data, new_data], ignore_index=True)
                            else:
                                all_data = pd.DataFrame([candidatura_search])
                            
                            # Write the data to Excel
                            all_data.to_excel(excel_file_path, index=False, header=False)
                            st.success(f"La candidatura '{candidatura_search}' è stata salvata su {excel_file_path} e non verrà più presentata!")
                        except Exception as e:
                            st.error(f"Error writing to Excel: {e}")
        else:
            st.write(f"Nessun risultato trovato per '{candidatura_search}'")
    else:
        st.write(f"Nessun documento trovato con il nome '{column_search}'")
else:
    st.write("Inserisci il nome della candidatura e del documento per visualizzare la riga corrispondente.")

# Display the full dataframe
st.write("Tabella completa:")
st.dataframe(df.style.applymap(color_cells))
