import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database


# TODO IMPLEMENT DATABASE URL
#SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:12345@localhost:5432/fyyurdb'
uri = 'SQLALCHEMYDATABASEURI'
SQLALCHEMY_DATABASE_URI = os.getenv(uri, "No DB URI is specified")
#NOTE: You need to restart a new console window if you changed the environment variables

