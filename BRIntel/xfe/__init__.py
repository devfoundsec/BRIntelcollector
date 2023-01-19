from XForce import all as grabAll, details
from os import environ
from dotenv import load_dotenv

load_dotenv()
IBM_KEY = environ['IBM_KEY']

def bigDetails(term):

def search(term):
    return grabAll(f"{term} (brasil or brazil)", IBM_KEY)

def reduced(term):
    # Fazer uns loop com todos os valores para entregar
    # os dados reduzidos com url em cada
    # id, name, description, author, date: created and modified ...
    # url, TLP
    
