from XForce import all as grabAll, details
from os import environ
from dotenv import load_dotenv

load_dotenv()
IBM_KEY = environ['IBM_KEY']

# extrai informacoes mais importantes pegando do padrao STIX
def extract_pattern(blob, volume_information):
    if volume_information == "basic":
        result = {}
        try:
            result['title'] = blob['objects'][0]['name']
            result['description'] = blob['objects'][0]['x_com_ibm_short_description']
            if len(blob['objects'][0]['x_com_ibm_tags']) >= 1:
                result["author"] = blob['objects'][0]['x_com_ibm_tags'][0]["user"]
            result['created'] = blob['objects'][0]['created']
            result['modified'] = blob['objects'][0]['modified']
            result['url'] = blob['url']
            result['tlp'] = None

            return result
        except:
            result = blob
            result['status'] = "Error in data formatation"
            return result
    else:
        return blob

def search(term):
    return grabAll(f"{term} (brasil or brazil)", IBM_KEY)

# resume_data: dict de resumida de pesquisa
# volume_information: full | basic = quantidade de dados entregue
def show(resume_data, volume_information='basic'):
    try:
        if resume_data["type"] == "threatactivity-report":
            data = details.activity(resume_data["id"], IBM_KEY)
            return extract_pattern(data, volume_information)

        elif resume_data["type"] == "malware-report":
            data = details.malware(resume_data["id"], IBM_KEY)
            return extract_pattern(data, volume_information)

        elif resume_data["type"] == "threatgroup-report":
            data = details.group(resume_data["id"], IBM_KEY)
            return extract_pattern(data, volume_information)

        elif resume_data["type"] == "industry-report":
            data = details.industry(resume_data["id"], IBM_KEY)
            return extract_pattern(data, volume_information)
    except:
        result = {}
        data = details.collector(resume_data["caseFileID"], IBM_KEY)
        if volume_information == 'basic':
            result["title"] = data["title"]
            result["description"] = data["contents"]["plainText"]
            result["author"] = data["owner"]["name"]
            result["created"] = data["created"]
            result["modified"] = None
            result["url"] = data["url"]
            result["tlp"] = data["tlpColor"]["tlpColorCode"]

            return result
        else:
            return data
