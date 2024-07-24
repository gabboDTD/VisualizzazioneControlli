import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import os 

# Sample DataFrame generation
def generate_sample_data():

    # Define the columns and rows
    columns = [
        # "Contratto tra SA e SR", 
        # "Determina di affidamento / di aggiudicazione / ordine di servizio", 
        # "Proposta commerciale SR accettata da SA", 
        # "Documento di stipula MEPA", 
        # "Convenzione / Accordo", 
        "Checklist asseverazione tecnica", 
        # "Certificato Regolare Esecuzione", 
        # "Allegato 5"        
    ]
    indices = ['CND_141SCU0422X_015254',
                'CND_141SCU1222X_079364',
                'CND_144COM0422X_014068',
                'CND_131COM1022X_082020',
                'CND_141SCU1222X_079707',
                'CND_141SCU1222X_079604',
                'CND_131COM1022X_068828',
                'CND_141SCU0622X_059144',
                'CND_131COM1022X_081830',
                'CND_141SCU0622X_032775']

    # Create a fixed DataFrame
    data = [
        ['Documento OK',            ],
        ['Errori nel documento',    ],
        ['Documento mancante',      ],
        ['Documento OK',            ],
        ['Errori nel documento',    ],
        ['Documento mancante',      ],
        ['Documento OK',            ],
        ['Documento mancante',      ],
        ['Documento OK',            ],
        ['Errori nel documento',    ]
    ]
    # Populate the DataFrame with random values 0, 1, 2
    df = pd.DataFrame(data, index=indices[0:len(data)], columns=columns)

    return df

def generate_specific_data_checklist():
    # Define the columns and rows
    columns = [
        "CUP",
        "Presenza della firma dell'asseveratore",
        "Corrispondenza dell’Anagrafica del SA con quanto scritto nell’Allegato 5 / in piattaforma",
        "Compilazione di tutti i campi della checklist (con la “x” su “positivo” o “n/a”)",
        "Esito positivo della verifica di conformità tecnica del progetto"
    ]

    indices = ['CND_141SCU0422X_015254',
                'CND_141SCU1222X_079364',
                'CND_144COM0422X_014068',
                'CND_131COM1022X_082020',
                'CND_141SCU1222X_079707',
                'CND_141SCU1222X_079604',
                'CND_131COM1022X_068828',
                'CND_141SCU0622X_059144',
                'CND_131COM1022X_081830',
                'CND_141SCU0622X_032775']
    
    data = [
        ['OK',          'OK',           'OK',           'OK',           'OK',],
        ['Assente',     'Assente',      'Assente',      'OK',           'OK',],
        ['No documento','No documento', 'No documento', 'No documento', 'No documento',],
        ['OK',          'OK',           'OK',           'OK',           'OK',],
        ['OK',          'Controllare',  'OK',           'OK',           'OK',],
        ['No documento','No documento', 'No documento', 'No documento', 'No documento',],
        ['OK',          'p7m',          'OK',           'OK',           'OK',],
        ['No documento','No documento', 'No documento', 'No documento', 'No documento',],
        ['OK',          'OK',           'OK',           'OK',           'OK',],
        ['OK',          'Controllare',  'OK',           'Errore',       'OK',],
    ]

    # Populate the DataFrame with random values 0, 1, 2
    df = pd.DataFrame(data, index=indices[0:len(data)], columns=columns)
    return df

# Function to color the cells
def color_cells(val):
    color = 'white'
    if val in ['No documento']:
        color = 'blue'    
    if val in ['Documento OK', 'OK', 'p7m']:
        color = 'lightgreen'
    elif val in ['Errori nel documento','Controllare','Errore']:
        color = 'orange'
    elif val in ['Documento mancante','Assente']:
        color = 'red'
    return f'background-color: {color}'

# Path for the Excel file
excel_file_path = 'sample_index.xlsx'

# Load or generate the data
df = generate_sample_data()

df_checklist = generate_specific_data_checklist()

# Streamlit App
st.title('Matrice dei controlli formali')

st.write("""
Questa app visualizza una tabella in cui ogni riga e' una candidatura in asseverazione formale,
ogni colonna e' un documento da controllare, e ogni cella contiene un colore che indica se i controlli sul documento sono OK,
se manca il documento (rosso), o se il documento continene errori (arancione)
""")

# Add search boxes to find the specific candidatura and column
candidatura_search = st.text_input('Cerca il nome della candidatura')
column_search = st.selectbox('Seleziona il nome del documento', df.columns)

if candidatura_search and column_search:
    if column_search in df.columns:
        filtered_df = df[df.index.str.contains(candidatura_search, case=False)]
        if not filtered_df.empty:
            # st.write(f"Risultati per '{candidatura_search}' e '{column_search}':")
            # st.dataframe(filtered_df[[column_search]].style.applymap(color_cells))
            
            # Check if a specific cell is clicked and display df_checklist
            if candidatura_search in df.index and column_search in df.columns:
                selected_value = df.loc[candidatura_search, column_search]
                if selected_value in ['Documento mancante', 'Errori nel documento', 'Documento OK']:
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
                            st.success(f"La candidatura '{candidatura_search}' e' stata salvata su {excel_file_path} e non verra' piu' presentata!")
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

