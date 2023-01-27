import BRIntel.xfe 
import BRIntel.otx

# Get all blob and make a list
def allSources(term):
    data = []
    data = BRIntel.xfe.search(term)
    data += BRIntel.otx.search(term)
    return data

def reduced(term):
    # Fazer uns loop com todos os valores para entregar
    # os dados reduzidos com url em cada
    # id, name, description, author, date: created and modified ...
    # url, TLP
    return False
 
