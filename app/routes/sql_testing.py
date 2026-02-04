from flask import g, Blueprint
import sqlite3

DATABASE = './../database.db'

TestBP = Blueprint('test', __name__)

def getDB():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@TestBP.route('/get')
def getData():
    pass

@TestBP.route('/upload')
def uploadData():

