from XForce import all as grabAll, details
from os import environ
from dotenv import load_dotenv

load_dotenv()
IBM_KEY = environ['IBM_KEY']

def search(term):
    return grabAll(f"{term} (brasil or brazil)", IBM_KEY)
