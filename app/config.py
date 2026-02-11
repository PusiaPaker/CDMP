class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
    SECRET_KEY = 'dev' # !!! DO NOT COMMIT WITH THIS ANYTHING ELSE BUT DEV
    #   https://www.geeksforgeeks.org/python/how-to-use-flask-session-in-python-flask/
    SESSION_PERMANENT = True # Sessions do not expire when the browser is closed
    SESSION_TYPE = 'filesystem'     # Store session data in files

    SESSION_COOKIE_SECURE = False  # Set True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_NAME = 'session'

    REMEMBER_COOKIE_DURATION = 30 * 24 * 60 * 60
    REMEMBER_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = True
