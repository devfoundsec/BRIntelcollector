#!/usr/bin/ python3 


import pandas as pd
from bs4 import BeautifulSoup
#import nltk 
import urllib3
#from urllib3.error import URLError, HTTPError
#import numpy as np



def le_phishstream(http):
    url= 'https://raw.githubusercontent.com/openctibr/threatFeeds/main/PhishingTodayFeed.txt'
    r= http.request ('GET', url)
    dados = BeautifulSoup(r.data)
    phishtable= pd.DataFrame()
    phishtable = phishtable.to_csv(str(dados), sep=",")
    #phishtable.head()
    phishtable = pd.read_csv('./log.csv')
    
    # Nova Data com Split das coluna "esquisita" separado por espaços
    new = phishtable['<html><body><p>"_Oil_Company.html","filename"'].str.split(",", n = 1, expand = True)
    new.head() 
    # Criando a Nova Coluna "Endereços" com o new[0]
    phishtable["Endereços"]= new[0] 
    # Criando a Nova Coluna "Identificador" com o new[1]
    phishtable["Identificador"]= new[1] 
    # Retirando a antiga coluna "esquisita" e unnamed 
    phishtable.drop(columns =['<html><body><p>"_Oil_Company.html","filename"'], inplace = True)
    phishtable.drop(columns =['Unnamed: 0'], inplace = True)
    phishtable.to_csv('./TabelaPhishing.csv')


le_phishstream(http)










