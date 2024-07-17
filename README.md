# BRIntelcollector

Pesquisa por indicadores de ameaças nacionais, através de diferentes fontes. Através da ferramenta é possível criar um banco de dados com ameaças nacionais e assim facilitar as pesquisas, identificação de organizações buscar por possíveis ameaças.

Atualmente estamos trabalhando duas fontes de dados: OTX da Alienvault e XFE da IBM

## Instalação e uso

> **Pré requisitos:** para instalar é necessário ter o python na versão 3+ e o pip correspondente. E possuir as chaves de API do [Open Threat Exchange](https://support.rocketcyber.com/hc/en-us/articles/360017914637-Setup-Alienvault-OTX-Threat-Intel-API-Key) e do [IBM X-Force Exchange](https://api.xforce.ibmcloud.com/doc/#/)(Lembre-se da especificidade da chave que [deve ser](https://github.com/Jul10l1r4/X-force#use): `$chave:$senha` em base64)

```pypi
pip3 install BRIntel1
```
Configure dessa forma seu `.env`. Claro: Substitua `<sua chave e senha>` pelo seu código da API e senha respectivamente.

```bash
echo "OTX_KEY = '<sua chave>'" > .env
echo "IBM_KEY = '<sua chave + senha em base64>'" >> .env
```
Para usar, basta importar os módulos que serão exemplificados:
```python
from BRIntel import allSources, default

# Retornará uma list contendo a busca padrão 
# das duas fontes, todos os valores em dict
allSources("Termo de busca")

# Da mesma forma da outra função também retornará
# lista de valores em dict, mas na estrutura padrão:
default("Termo de busca")
```
A primeira função retorna de forma absoluta os valores das buscas, já a segunda reduz alguns dados para o trabalho na manipulação.
Retorno da busca padrão (`BRIntel.defaul`):
- ["title"]: Título do pulse/relatório
- ["description"]: Descrição mais detalhada explicando o pulse/relatório
- ["author"]: Nome do autor do pulse/relatório
- ["created"]: Data de criação do pulse/relatório
- ["Modified"]: Data de modificação do pulse/relatório
- ["tlp"]: Traffic Light Protocol ([TLP](https://www.gov.br/cisc/pt-br/tlp)) de pulse/relatório
- ["url"]: Url de pulse/relatório

É possível fazer a busca em fontes específicas, exemplo:
```python
from BRIntel import xfe, otx

# O RETORNO SERÁ UMA LIST
# stix 2.1
xfe.search("Termo de busca")
# Formato aberto de pulse OTX
otx.search("Termo de busca")
```
Além de busca em fonte específica, também é possível fazer isso de forma que siga o padrão citado à cima
```python
from BRIntel import xfe, otx

# Ambas as funções recebem o dict que corresponde a um valor
# de pulse/relatorio
xfe.show(xfe_search[x])
otx.show(otx_search[x])
```
Além da busca com o retorno em padrão de exibição, é possível buscar os detalhes de um pulse/relatório específico. Dessa forma:
```python
from BRIntel import xfe, otx

# Ambas as funções recebem o ID, uma como string e outra como int, respectivamente
xfe.details(xfe_search[x]["id"])
otx.details(otx_search[x]["id"])
```
