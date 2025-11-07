# BRIntelcollector

## Visão Geral

O **BRIntelcollector** é uma ferramenta de Cyber Threat Intelligence (CTI) focada em indicadores de ameaças nacionais do Brasil. A ferramenta permite pesquisar e consolidar informações sobre ameaças cibernéticas através de múltiplas fontes de inteligência, facilitando a criação de um banco de dados centralizado para análise de segurança.

## Objetivos

- Coletar indicadores de ameaças nacionais brasileiras
- Integrar múltiplas fontes de CTI em uma única interface
- Facilitar pesquisas e identificação de ameaças
- Auxiliar organizações na busca por possíveis ameaças relevantes

## Fontes de Dados

Atualmente, a ferramenta integra duas principais fontes de inteligência:

1. **OTX (Open Threat Exchange)** - AlienVault
2. **XFE (X-Force Exchange)** - IBM

## Pré-requisitos

### Software
- Python 3+
- pip (correspondente à versão do Python)

### Credenciais de API
É necessário obter chaves de API das seguintes plataformas:

- **Open Threat Exchange (OTX)**: [https://otx.alienvault.com](https://otx.alienvault.com)
- **IBM X-Force Exchange**: [https://exchange.xforce.ibmcloud.com](https://exchange.xforce.ibmcloud.com)

**Importante**: A chave da IBM deve estar no formato `chave:senha` codificado em Base64.

## Instalação

### 1. Instalar o pacote

```bash
pip3 install BRIntel1
```

### 2. Configurar as variáveis de ambiente

Crie um arquivo `.env` com suas credenciais:

```bash
echo "OTX_KEY = '<sua chave>'" > .env
echo "IBM_KEY = '<sua chave + senha em base64>'" >> .env
```

**Exemplo de codificação da chave IBM**:
```bash
echo -n "sua_chave:sua_senha" | base64
```

## Uso

### Busca em Todas as Fontes

#### Busca Completa (Dados Absolutos)

```python
from BRIntel import allSources

# Retorna uma lista com dicionários contendo todos os dados das fontes
resultados = allSources("Termo de busca")
```

#### Busca Padrão (Dados Simplificados)

```python
from BRIntel import default

# Retorna uma lista com dicionários em formato padronizado
resultados = default("Termo de busca")
```

### Estrutura de Retorno Padrão

A função `default()` retorna os dados no seguinte formato:

| Campo | Descrição |
|-------|-----------|
| `title` | Título do pulse/relatório |
| `description` | Descrição detalhada do pulse/relatório |
| `author` | Nome do autor |
| `created` | Data de criação |
| `Modified` | Data da última modificação |
| `tlp` | Traffic Light Protocol (classificação de compartilhamento) |
| `url` | URL do pulse/relatório |

### Busca em Fontes Específicas

#### IBM X-Force Exchange (XFE)

```python
from BRIntel import xfe

# Busca no XFE (retorna formato STIX 2.1)
resultados_xfe = xfe.search("Termo de busca")

# Exibir em formato padrão
xfe.show(resultados_xfe[0])

# Obter detalhes completos de um relatório específico
detalhes = xfe.details(resultados_xfe[0]["id"])
```

#### Open Threat Exchange (OTX)

```python
from BRIntel import otx

# Busca no OTX (retorna formato aberto de pulse OTX)
resultados_otx = otx.search("Termo de busca")

# Exibir em formato padrão
otx.show(resultados_otx[0])

# Obter detalhes completos de um pulse específico
detalhes = otx.details(resultados_otx[0]["id"])
```

## Exemplos de Uso

### Exemplo 1: Busca Simples

```python
from BRIntel import default

# Buscar por um domínio suspeito
resultados = default("exemplo.com.br")

for resultado in resultados:
    print(f"Título: {resultado['title']}")
    print(f"Autor: {resultado['author']}")
    print(f"TLP: {resultado['tlp']}")
    print(f"URL: {resultado['url']}")
    print("-" * 50)
```

### Exemplo 2: Busca com Detalhes

```python
from BRIntel import otx, xfe

# Buscar em ambas as fontes
resultados_otx = otx.search("malware Brasil")
resultados_xfe = xfe.search("malware Brasil")

# Obter detalhes do primeiro resultado de cada fonte
if resultados_otx:
    detalhes_otx = otx.details(resultados_otx[0]["id"])
    print("Detalhes OTX:", detalhes_otx)

if resultados_xfe:
    detalhes_xfe = xfe.details(resultados_xfe[0]["id"])
    print("Detalhes XFE:", detalhes_xfe)
```

### Exemplo 3: Comparação entre Fontes

```python
from BRIntel import allSources

# Buscar em todas as fontes com dados completos
todas_fontes = allSources("phishing")

print(f"Total de resultados encontrados: {len(todas_fontes)}")

for item in todas_fontes:
    print(f"Fonte: {item.get('fonte', 'N/A')}")
    print(f"Título: {item.get('title', 'N/A')}")
```

## Traffic Light Protocol (TLP)

A ferramenta utiliza o padrão TLP para classificação de compartilhamento de informações:

- **TLP:RED** - Informação restrita, não compartilhar
- **TLP:AMBER** - Compartilhamento limitado
- **TLP:GREEN** - Compartilhamento dentro da comunidade
- **TLP:WHITE** - Compartilhamento público ilimitado

Mais informações: [https://www.gov.br/cisc/pt-br/tlp](https://www.gov.br/cisc/pt-br/tlp)

## Formatos de Dados

- **OTX**: Retorna dados no formato aberto de pulse do OTX
- **XFE**: Retorna dados no formato STIX 2.1

## Casos de Uso

1. **Análise de Ameaças**: Identificar campanhas maliciosas direcionadas ao Brasil
2. **Investigação de Incidentes**: Correlacionar indicadores com ameaças conhecidas
3. **Threat Hunting**: Buscar proativamente por indicadores de comprometimento
4. **Enriquecimento de IOCs**: Adicionar contexto a indicadores coletados
5. **Relatórios de Inteligência**: Consolidar informações para relatórios executivos

## Boas Práticas

1. **Gestão de Credenciais**: Nunca compartilhe ou commite suas chaves de API
2. **Rate Limiting**: Respeite os limites de requisições das APIs
3. **Validação de Dados**: Sempre valide e contextualize os resultados obtidos
4. **Atualização Regular**: Mantenha a biblioteca atualizada para novos recursos
5. **Documentação TLP**: Respeite as classificações TLP dos relatórios

## Limitações

- Dependência de APIs externas (requer conectividade e credenciais válidas)
- Limitado às fontes OTX e XFE atualmente
- Sujeito aos limites de taxa das APIs utilizadas

## Contribuindo

Para contribuir com o projeto, visite o repositório no GitHub:
[https://github.com/devfoundsec/BRIntelcollector](https://github.com/devfoundsec/BRIntelcollector)

## Suporte

Para reportar bugs ou solicitar recursos, abra uma issue no GitHub do projeto.

## Referências

- [AlienVault OTX](https://otx.alienvault.com)
- [IBM X-Force Exchange](https://exchange.xforce.ibmcloud.com)
- [STIX 2.1 Documentation](https://oasis-open.github.io/cti-documentation/)
- [Traffic Light Protocol - Gov.br](https://www.gov.br/cisc/pt-br/tlp)

---

**Desenvolvido por**: devfoundsec  
**Repositório**: https://github.com/devfoundsec/BRIntelcollector