class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
    SECRET_KEY = 'dev' # !!! DO NOT COMMIT WITH THIS ANYTHING ELSE BUT DEV
    #   https://www.geeksforgeeks.org/python/how-to-use-flask-session-in-python-flask/
    SESSION_PERMANENT = False     # Sessions expire when the browser is closed
    SESSION_TYPE = 'filesystem'     # Store session data in files
