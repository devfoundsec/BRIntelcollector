#!/usr/bin/python3 
from dotenv import load_dotenv
from os import environ
from OTXv2 import OTXv2

load_dotenv()
otx = OTXv2(environ["OTX_KEY"])

def show(data):
    
    data["title"] 
    data["description"] 
    data["author"] 
    data["created"] 
    data["modified"] 
    data["tlp"] 
    data["url"] 
    data["pulse_key"] 
    data["indicator"] 
    data["type"] 
    data["report_date"] 
    data["content"] 
    return data

def indicators(pulse_id):
    indicators = []
    for id in pulse_id:
        indicators.append(otx.get_pulse_indicators("pulse_id"))
    merge_result(indicators)
    return indicators
    

def merge_result(indicators,data):
    # Dicionário para armazenar os dados da lista 2
    dic_indicators = {item["pulse_key"]: item for item in indicators[0]}

    # Nova lista com o resultado do left join
    result_unido = []

    for item_lista_1 in data:
        id_item_lista_1 = item_lista_1["id"]
    
        # Verifica se a chave 'id' da lista 1 existe na lista 2
        if id_item_lista_1 in dic_indicators:
            item_lista_2 = dic_indicators[id_item_lista_1]
         
        else:
            # Se a chave 'id' não existe na lista 2, mantém o item da lista 1
            novo_item = item_lista_1.copy()
    
            # Adiciona o novo item na lista unida
            result_unido.append(novo_item)

        # Copia o item da lista 1 e adiciona as informações da lista 2
        novo_item = item_lista_1.copy()
        novo_item.update(item_lista_2)


    data = result_unido
    return data

def details(pulse_id):
    return otx.get_pulse_details(pulse_id)

# consulta personalizada por dominio
def search(term):
    data = []
    clearData = []
    for origin in ['Brasil', 'Brazil', 'BR', 'country:"Brazil"']:
        blob = otx.search_pulses(f"{term} {origin}")
        data += blob["results"]

    return data
