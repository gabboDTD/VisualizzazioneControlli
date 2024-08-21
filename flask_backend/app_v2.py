import os
import json
import base64

import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

from config import Config
from db import get_db, close_db
import numpy as np
from bson import ObjectId

def create_app():
    """
    Create and configure the Flask application.

    This function initializes the Flask application, loads the configuration from the Config object,
    and ensures that the database connection is closed after each request.

    Returns:
        Flask: The initialized Flask application.
    """    
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.teardown_appcontext
    def teardown_db(exception):
        """
        Close the database connection after the app context ends.

        Args:
            exception (Exception): Any exception that might have occurred during the request.
        """        
        close_db()
    return app

def determine_stato_checklist(row):
    """
    Determine the checklist status based on document signature and technical compliance.

    This function analyzes the 'Stato_Firma_Asseveratore' and 'Esito_Conformità_Tecnica' fields
    from a dataframe row and categorizes the document into one of several status types.

    Args:
        row (pd.Series): A pandas Series object representing a row of data.

    Returns:
        str: A string representing the document's status.
    """    
    stato_firma = row['Stato_Firma_Asseveratore']
    esito_conformita = row['Esito_Conformità_Tecnica']

    if stato_firma == 'Documento non presente':
        return 'Documento non presente'
    if stato_firma in ['Firma presente', 'Documento p7m'] and esito_conformita == 'Positivo':
        return 'Documento valido'
    if stato_firma in ['Firma assente', 'Verifica manuale'] or esito_conformita in ['Negativo', 'Campo nullo']:
        return 'Documento errato'
    if stato_firma in ['Errore nel controllo', 'EOF marker not found'] or esito_conformita in ['Errore nel controllo', 'EOF marker not found']:
        return 'Errori nei controlli'
    
    return ''

def validate_df_columns_and_values(df, possible_values):
    """
    Validate the columns and values of a DataFrame.

    This function checks if the columns of the DataFrame match the expected set of columns
    and validates the values against a set of possible values for each column.

    Args:
        df (pd.DataFrame): The DataFrame to validate.
        possible_values (dict): A dictionary where keys are column names and values are lists of valid values.

    Returns:
        tuple: A tuple containing a boolean indicating success, and a string with validation details or errors.
    """    
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

def convert_objectid_to_str(document):
    """
    Recursively convert MongoDB ObjectId fields to strings within a document.

    This function converts any ObjectId fields found within a dictionary or list structure
    to strings, which can be easier to work with in JSON or other data formats.

    Args:
        document (dict or list): The document (or list of documents) containing ObjectId fields.

    Returns:
        dict or list: The document with all ObjectId fields converted to strings.
    """
    if isinstance(document, list):
        return [convert_objectid_to_str(item) for item in document]
    elif isinstance(document, dict):
        for key, value in document.items():
            if isinstance(value, ObjectId):
                document[key] = str(value)
            elif isinstance(value, (dict, list)):
                document[key] = convert_objectid_to_str(value)
    return document

def load_data():
    """
    Load data from specified file paths for processing.

    This function loads data from files specified in the environment variables 'PARQUET_PATH' and 'EXCEL_PATH'.
    It returns two dataframes: one from the parquet file and another from the Excel file.

    Returns:
        tuple: Two pandas DataFrames if loading is successful, else (None, None).
    """       
    try:
        parquet_path = app.config['PARQUET_PATH']
        excel_path = app.config['EXCEL_PATH']

        if not parquet_path or not excel_path:
            raise ValueError("PARQUET_PATH or EXCEL_PATH environment variables not set.")

        candidature_checklist = pd.read_parquet(parquet_path)
        file_status_report = pd.read_excel(excel_path)

        return candidature_checklist, file_status_report
    except Exception as e:
        app.logger.error(f"Error loading data: {e}")
        return None, None

def load_json_file(file_path_env):
    """
    Load JSON data from a file specified by an environment variable.

    This function loads a JSON file from the file path given by an environment variable.

    Args:
        file_path_env (str): The environment variable containing the file path.

    Returns:
        dict: The loaded JSON data, or None if an error occurs.
    """       
    try:
        file_path = app.config[file_path_env]

        if not file_path:
            raise ValueError(f"{file_path_env} environment variable not set.")

        with open(file_path, 'r') as json_file:
            return json.load(json_file)
    except Exception as e:
        app.logger.error(f"Error loading file from {file_path_env}: {e}")
        return None

def load_candidature_from_file():
    """
    Load candidature IDs from a JSON file.

    This function loads a list of candidature IDs from a JSON file specified by the 'CANDIDATURE_PATH'
    environment variable.

    Returns:
        list: A list of candidature IDs, or None if loading fails.
    """        
    query_result = load_json_file('CANDIDATURE_PATH')
    if query_result is not None:
        # Extract candidatureIds
        candidature_ids = [doc['candidatureId'] for doc in query_result]
        return candidature_ids
    else:
        return None

def load_candidatura_from_file():
    """
    Load candidature details from a JSON file.

    This function loads detailed candidature data from a JSON file specified by the 'CANDIDATURA_PATH'
    environment variable.

    Returns:
        dict: A dictionary containing the candidature details, or None if loading fails.
    """        
    query_result = load_json_file('CANDIDATURA_PATH')
    return query_result

def load_candidature():
    """
    Load a list of candidature IDs from the MongoDB collection.

    This function connects to MongoDB and retrieves a list of candidature IDs from the specified collection.

    Returns:
        list: A list of candidature IDs, or None if an error occurs.
    """        
    try:
        # Connect to MongoDB
        client = MongoClient(app.config['MONGO_URI'])
        db = client[app.config['DATABASE_NAME']]        
        collection = db[app.config['COLLECTION_CANDIDATURA']]

        candidature = collection.find({}, {"candidatureId": 1, "_id": 0})
        candidature_ids = [doc['candidatureId'] for doc in candidature]
        return candidature_ids

    except Exception as e:
        app.logger.error(f"Error loading data: {e}")
        return None
    
def load_candidatura(id_candidatura):
    """
    Load detailed candidature data from the MongoDB collection.

    This function connects to MongoDB and retrieves detailed candidature data for the specified candidature ID.

    Args:
        id_candidatura (str): The ID of the candidature to retrieve.

    Returns:
        list: A list of documents related to the candidature, or None if an error occurs.
    """      
    try:
        # Connect to MongoDB
        client = MongoClient(app.config['MONGO_URI'])
        db = client[app.config['DATABASE_NAME']]        
        collection = db[app.config['COLLECTION_DOCUMENTO']]

        # Query the collection for all documents
        query_result = list(collection.find({"candidatureId": id_candidatura}))

        return query_result
    except Exception as e:
        app.logger.error(f"Error loading data from MongoDB: {e}")
        return None

def generate_data():
    """
    Generate data frames for document and checklist status based on loaded data.

    This function processes the loaded data to generate two dataframes: one for document statuses and one for checklist statuses.
    The data is validated before returning the dataframes.

    Returns:
        tuple: Two pandas DataFrames containing document and checklist status, or (None, None) if generation fails.
    """        
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

app = create_app()
CORS(app)  # Enable CORS for all routes

# API to read candidature lists
@app.route('/api/data', methods=['GET'])
def get_data():
    """
    API endpoint to retrieve a list of candidature IDs.

    This endpoint connects to the database, loads the candidature data, and returns a list of candidature IDs.

    Returns:
        JSON response: A JSON object containing the list of candidature IDs or an error message if the operation fails.
    """       
    candidature_ids = load_candidature()
    if candidature_ids is None:
        return jsonify({'error': 'Data generation failed'}), 500
    return jsonify({'candidature_ids': candidature_ids})

@app.route('/api/detail/<id_candidatura>', methods=['GET'])
def get_detail(id_candidatura):
    """
    API endpoint to retrieve detailed candidature data.

    This endpoint connects to the database, retrieves detailed data for a given candidature ID, and returns it as a JSON response.

    Args:
        id_candidatura (str): The ID of the candidature to retrieve.

    Returns:
        JSON response: A JSON object containing the detailed candidature data or an error message if the operation fails.
    """     
    candidatura = load_candidatura(id_candidatura)

    if candidatura is None:
        return jsonify({'error': 'Error loading data from MongoDB'}), 500
    
    # Convert ObjectId to string
    candidatura_serializable = convert_objectid_to_str(candidatura)

    # Now you can pass this data to sonify or jsonify without issues
    response = jsonify({'query': candidatura_serializable})
    return response

# @app.route('/api/detail/<id_candidatura>', methods=['GET'])
# def get_detail(id_candidatura):
#     df, df_checklist = generate_data()
#     if df is None or df_checklist is None:
#         return jsonify({'error': 'Data generation failed'}), 500
#     df_candidatura = df.loc[id_candidatura,:]
#     df_candidatura_checklist = df_checklist.loc[id_candidatura,:]
#     return jsonify({'df': df_candidatura.to_dict(), 'df_checklist': df_checklist.to_dict()})

@app.route('/api/document/<path:path>', methods=['GET'])
def get_document(path):
    """
    API endpoint to retrieve a document from S3 storage.

    This endpoint fetches a document from an S3 bucket based on the provided path and returns the content as a base64 encoded string.

    Args:
        path (str): The path of the document in the S3 bucket.

    Returns:
        JSON response: A JSON object containing the base64 encoded document content or an error message if the operation fails.
    """      
    aws_access_key_id = app.config['AWS_ACCESS_KEY_ID']
    aws_secret_access_key = app.config['AWS_SECRET_ACCESS_KEY']
    aws_region = app.config['AWS_REGION']
    bucket_name = 'pdnd-prod-dl-1'
    
    # Construct the full file key path
    file_key = f'data/mid-dtd/pad26/candidature-docs/{path}'

    app.logger.info(f"Requesting document from S3 with path: {file_key}")

    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region
    )

    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        file_bytes = response['Body'].read()
        base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
        return jsonify({"file_content_base64": base64_pdf})
    except s3_client.exceptions.NoSuchKey:
        app.logger.error(f"No such key: {file_key}")
        return jsonify({"error": f"No such key: {file_key}"}), 404
    except (NoCredentialsError, PartialCredentialsError):
        app.logger.error("Credentials not available")
        return jsonify({"error": "Credentials not available"}), 403
    except Exception as e:
        app.logger.error(f"Error fetching document: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
