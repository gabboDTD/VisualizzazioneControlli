import json
import pandas as pd
from dotenv import load_dotenv

def determine_stato_checklist(row):
    if row['Status'] == 'Documento non presente':
        return False, 'Documento non presente'
    elif row['Status'] in ['Firma presente', 'Documento p7m'] and row['Esito'] == 'Positivo':
        return True, 'Documento valido'
    elif row['Status'] in ['Firma assente', 'Verifica manuale'] or row['Esito'] in ['Negativo', 'Campo nullo']:
        return False, 'Documento errato'
    elif row['Status'] in ['Errore nel controllo', 'EOF marker not found'] or row['Esito'] in ['Errore nel controllo', 'EOF marker not found']:
        return False, 'Errori nei controlli'
    else:
        return ''


# Load environment variables from .env file
load_dotenv()

# parquet_path = os.getenv('PARQUET_PATH')
# candidature_checklist = pd.read_parquet(parquet_path)


excel_path = os.getenv('EXCEL_PATH')
candidature_checklist = pd.read_excel(excel_path)

# Create the query result from the list of candidature IDs
query_result = [{"candidatureId": candidature_id} for candidature_id in candidature_checklist['Candidatura'].to_list()]

# Path to the JSON file
json_file_path = '../data/candidature.json'

# Write the JSON data to a file
with open(json_file_path, 'w') as json_file:
    json.dump(query_result, json_file, indent=4)

print(f"JSON file written to {json_file_path}")

# Convert the DataFrame to JSON format
json_output = []

for idx, row in candidature_checklist.iterrows():
    
    stato, reason = determine_stato_checklist(row)

    json_output.append({
        "candidatureId": row["Candidatura"],
        "documentClass": "Stato_Checklist_Asseverazione",
        "documentID": "",
        "modifyTimestamp": "",
        "documentType": "CandidaturaDocumento",
        "esitoChecks": stato,
        "esitoCheckReason": reason,
        "dettaglioCheck": [
            {
                "nomeCheck": "Stato_CUP",
                "esitoCheck": False,
                "Descrizione": "Controllo non supportato"
            },
            {
                "nomeCheck": "Stato_Firma_Asseveratore",
                "esitoCheck": False,
                "Descrizione": row['Status']
            },
            {
                "nomeCheck": "Stato_Anagrafica_SA",
                "esitoCheck": False,
                "Descrizione": "Controllo non supportato"
            },
            {
                "nomeCheck": "Stato_Compilazione_Checklist",
                "esitoCheck": False,
                "Descrizione": "Controllo non supportato"
            },
            {
                "nomeCheck": "Esito_Conformità_Tecnica",
                "esitoCheck": False,
                "Descrizione": row["Esito"]
            }
        ],
        "documentName": "",
        "userFeedback": "",
        "lastmodifyUsers": ""
    })

    json_output.append({
        "candidatureId": row["Candidatura"],
        "documentClass": "Stato_Contratto_SA_SR",
        "documentID": "",
        "modifyTimestamp": "",
        "documentType": "CandidaturaDocumento",
        "esitoChecks": False,
        "esitoCheckReason": "Documento non supportato",
        "dettaglioCheck": [],
        "documentName": "",
        "userFeedback": "",
        "lastmodifyUsers": ""
    })
    
    json_output.append({
        "candidatureId": row["Candidatura"],
        "documentClass": "Stato_Determina_Affidamento_Aggiudicazione_Servizio",
        "documentID": "",
        "modifyTimestamp": "",
        "documentType": "CandidaturaDocumento",
        "esitoChecks": False,
        "esitoCheckReason": "Documento non supportato",
        "dettaglioCheck": [],
        "documentName": "",
        "userFeedback": "",
        "lastmodifyUsers": ""
    })

    json_output.append({
        "candidatureId": row["Candidatura"],
        "documentClass": "Stato_Proposta_Commerciale",
        "documentID": "",
        "modifyTimestamp": "",
        "documentType": "CandidaturaDocumento",
        "esitoChecks": False,
        "esitoCheckReason": "Documento non supportato",
        "dettaglioCheck": [],
        "documentName": "",
        "userFeedback": "",
        "lastmodifyUsers": ""
    })

    json_output.append({
        "candidatureId": row["Candidatura"],
        "documentClass": "Stato_Documento_Stipula_MEPA",
        "documentID": "",
        "modifyTimestamp": "",
        "documentType": "CandidaturaDocumento",
        "esitoChecks": False,
        "esitoCheckReason": "Documento non supportato",
        "dettaglioCheck": [],
        "documentName": "",
        "userFeedback": "",
        "lastmodifyUsers": ""
    })

    json_output.append({
        "candidatureId": row["Candidatura"],
        "documentClass": "Stato_Convenzione_Accordo",
        "documentID": "",
        "modifyTimestamp": "",
        "documentType": "CandidaturaDocumento",
        "esitoChecks": False,
        "esitoCheckReason": "Documento non supportato",
        "dettaglioCheck": [],
        "documentName": "",
        "userFeedback": "",
        "lastmodifyUsers": ""
    })

    json_output.append({
        "candidatureId": row["Candidatura"],
        "documentClass": "Stato_Certificato_Regolare_Esec",
        "documentID": "",
        "modifyTimestamp": "",
        "documentType": "CandidaturaDocumento",
        "esitoChecks": False,
        "esitoCheckReason": "Documento non supportato",
        "dettaglioCheck": [],
        "documentName": "",
        "userFeedback": "",
        "lastmodifyUsers": ""
    })

    json_output.append({
        "candidatureId": row["Candidatura"],
        "documentClass": "Stato_Allegato_5",
        "documentID": "",
        "modifyTimestamp": "",
        "documentType": "CandidaturaDocumento",
        "esitoChecks": False,
        "esitoCheckReason": "Documento non supportato",
        "dettaglioCheck": [],
        "documentName": "",
        "userFeedback": "",
        "lastmodifyUsers": ""
    })



# Convert the list of JSON objects to a JSON string
json_result = json.dumps(json_output, indent=4)

# Print the JSON output
print(json_output)

# Path to the JSON file
json_file_path = '../data/candidatura.json'

# Write the JSON data to a file
with open(json_file_path, 'w') as json_file:
    json.dump(json_output, json_file, indent=4)

print(f"JSON file written to {json_file_path}")
