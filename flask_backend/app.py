import os
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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

def load_data():
    try:
        parquet_path = os.getenv('PARQUET_PATH')
        excel_path = os.getenv('EXCEL_PATH')
        candidature_checklist = pd.read_parquet(parquet_path)
        file_status_report = pd.read_excel(excel_path)
        return candidature_checklist, file_status_report
    except Exception as e:
        app.logger.error(f"Error loading data: {e}")
        return None, None

def generate_data():
    candidature_checklist, file_status_report = load_data()
    if candidature_checklist is None or file_status_report is None:
        return None, None

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

    columns_documenti = list(possible_values_documenti.keys())

    possible_values_checklist = {
        "Stato_CUP":                    ['Codice corretto',                     'Codice errato', 'Codice assente',      'Verifica manuale', 'Controllo non supportato', 'Errore nel controllo', 'Documento non presente'],
        "Stato_Firma_Asseveratore":     ['Firma presente', 'Documento p7m',     'Firma assente',                        'Verifica manuale', 'Controllo non supportato', 'Errore nel controllo', 'Documento non presente'],
        "Stato_Anagrafica_SA":          ['Dati corretti',                       'Dati non corrispondenti',              'Verifica manuale', 'Controllo non supportato', 'Errore nel controllo', 'Documento non presente'],
        "Stato_Compilazione_Checklist": ['Compilazione corretta',               'Compilazione errata',                  'Verifica manuale', 'Controllo non supportato', 'Errore nel controllo', 'Documento non presente'],
        "Esito_Conformità_Tecnica":     ['Positivo',                            'Negativo', 'Campo nullo',              'Verifica manuale', 'Controllo non supportato', 'Errore nel controllo', 'Documento non presente']
    }

    columns_checklist = list(possible_values_checklist.keys())

    df_checklist = pd.DataFrame(index=file_status_report.index, columns=columns_checklist)
    df = pd.DataFrame(index=file_status_report.index, columns=columns_documenti)

    df_checklist['Stato_CUP'] = 'Controllo non supportato'
    df_checklist['Stato_Firma_Asseveratore'] = file_status_report['Status']
    df_checklist.loc[df_checklist['Stato_Firma_Asseveratore'] == 'EOF marker not found', 'Stato_Firma_Asseveratore'] = 'Errore nel controllo'
    df_checklist['Stato_Anagrafica_SA'] = 'Controllo non supportato'
    df_checklist['Stato_Compilazione_Checklist'] = 'Controllo non supportato'
    df_checklist['Esito_Conformità_Tecnica'] = file_status_report['Esito']
    df_checklist.loc[df_checklist['Esito_Conformità_Tecnica'] == 'EOF marker not found', 'Esito_Conformità_Tecnica'] = 'Errore nel controllo'

    df['Stato_Checklist_Asseverazione'] = df_checklist.apply(determine_stato_checklist, axis=1)

    for column in columns_documenti:
        if column != "Stato_Checklist_Asseverazione":
            df[column] = "Documento non supportato"

    is_valid, message = validate_df_columns_and_values(df_checklist, possible_values_checklist)
    app.logger.info(message)

    is_valid, message = validate_df_columns_and_values(df, possible_values_documenti)
    app.logger.info(message)

    return df, df_checklist

@app.route('/api/data', methods=['GET'])
def get_data():
    df, df_checklist = generate_data()
    if df is None or df_checklist is None:
        return jsonify({'error': 'Data generation failed'}), 500
    return jsonify({'df': df.to_dict(), 'df_checklist': df_checklist.to_dict()})

if __name__ == '__main__':
    app.run(debug=True)
