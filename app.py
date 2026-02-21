from app import create_app
from dotenv import load_dotenv

app = create_app()

if __name__ == '__main__':
    # This function will load the environment variables from .env file
    # access them by using os.getenv('VARIABLE_NAME'), obviously you need "import os" before that
    load_dotenv() 

    app.run(debug=True)
