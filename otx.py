#!/usr/bin/python3 
import requests
import json
from dotenv import load_dotenv
from os import environ
from OTXv2 import OTXv2, IndicatorTypes
import pandas

load_dotenv()
otx = OTXv2(environ["OTX_KEY"])

#CONSULTAS PARA PULSES RELACIONADOS AO BRASIL
brazil = otx.search_pulses("Brazil")
br = otx.search_pulses("BR")
brasil = otx.search_pulses("Brasil")

#criação de dataframes
pdtable=pandas.DataFrame()
pd2 = pandas.DataFrame()
pd3 = pandas.DataFrame()

#criação de vetores temporários que auxiliam no manuseio dos dados
dta=[]
dta2=[]
dta3=[]

#ler resultados das querys e puchar os detalhes para obter mais dados das ocorrencias
for i in range(len(brazil["results"])):
        brazil_id=brazil["results"][i]["id"]
        brazil_details = otx.get_pulse_details(brazil_id) 
        dta.append(brazil_details)

for i in range(len(dta)): #montagem dataframe pdtable
        pdtable = pdtable.append(dta[i] , ignore_index=True)
for i in range(len(br['results'])):
        br_id=br["results"][i]["id"]
        br_details = otx.get_pulse_details(br_id)
        dta2.append(br_details)

for i in range(len(brasil['results'])):
        brasil_id=brasil["results"][i]["id"]
        brasil_details = otx.get_pulse_details(brasil_id)
        dta3.append(brasil_details)

#manuseio de resultados para montagem de dataframes pd2 e pd3
for i in range(len(dta2)):
  pd2 = pd2.append(dta2[i] , ignore_index=True)

for i in range(len(dta3)):
  pd3 = pd3.append(dta3[i] , ignore_index=True)

#montagem de dataframe final com os três dataframes concatenados
f=[pdtable,pd2,pd3] #variavel que armazena o conteúdo dos três dataframes
finalbr=pd.concat(f,ignore_index=True) #concatenação dos três dataframes

finalbr.to_csv('./otbrfinal.csv', index=False) #exportando o dataframe em um arquivo csv

#consulta personalizada por dominio
def consulta_dominio(otx):
    data=[]
    dominio=str(input('digite o dominio que deseja buscar'))
    dc=otx.search_pulses(dominio)
    domain_table=pd.DataFrame()
    for i in range(len(dc["results"])):
        brazil_id=dc["results"][i]["id"]
        brazil_details = otx.get_pulse_details(brazil_id)
        data.append(brazil_details)
    for i in range(len(data)):
        domain_table = domain_table.append(data[i] , ignore_index=True)
    domaintable.to_csv('./otxconsultadominio.csv',index=False)
