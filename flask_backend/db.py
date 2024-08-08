from pymongo import MongoClient
from flask import current_app, g

def get_db():
    if 'mongo_db' not in g:
        g.mongo_db = MongoClient(current_app.config['MONGO_URI']).get_database()
    return g.mongo_db

def close_db(e=None):
    db = g.pop('mongo_db', None)
    if db is not None:
        db.client.close()
