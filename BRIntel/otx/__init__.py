#!/usr/bin/python3 
from dotenv import load_dotenv
from os import environ
from OTXv2 import OTXv2

load_dotenv()
otx = OTXv2(environ["OTX_KEY"])

def details(pulse_id):
    return otx.get_pulses_details(pulse_id)

# consulta personalizada por dominio
def search(term):
    data = []
    clearData = []
    for origin in ['Brasil', 'Brazil', 'BR', 'country:"Brazil"']:
        blob = otx.search_pulses(f"{term} {origin}")
        data += blob["results"]

    return data
