#!/usr/bin/python3 
import requests
from dotenv import load_dotenv
from os import environ
from OTXv2 import OTXv2

load_dotenv()
otx = OTXv2(environ["OTX_KEY"])

# CONSULTAS PARA PULSES RELACIONADOS AO BRASIL
brazil = otx.search_pulses("Brazil")
br = otx.search_pulses("BR")
brasil = otx.search_pulses("Brasil")

# consulta personalizada por dominio
def otxBr(term):
    data = []
    clearData = []
    for origin in ['Brasil', 'Brazil', 'BR', 'country:"Brazil"']:
        blob = otx.search_pulses(f"{term} {origin}")

        for i in range(len(blob["results"])):
            pulse_id = blob["results"][i]["id"]
            pulse_details = otx.get_pulse_details(pulse_id)
            data.append(pulse_details)

    for i in data:
        if i not in clearData:
            clearData.append(i) 

    return clearData

print(otxBr("com.br"))
