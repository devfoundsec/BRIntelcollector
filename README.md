# BRIntelcollector 2.0

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

**BRIntelcollector** é uma plataforma avançada e modular para coleta, análise e normalização de Indicadores de Comprometimento (IoCs) a partir de múltiplas fontes de inteligência de ameaças. O projeto fornece uma CLI moderna, API REST robusta e bibliotecas reutilizáveis para automatizar fluxos de coleta com controle dinâmico de rate limit, uso opcional de proxies rotativos e análise avançada de ameaças.

## 🚀 Recursos Principais

### Core Features
- **Arquitetura Modular** - Estrutura bem organizada com separação clara de responsabilidades
- **7 Fontes de TI** - AlienVault OTX, VirusTotal, IBM X-Force, MISP, ThreatFox, AbuseIPDB, Shodan
- **Persistência Avançada** - Sistema de banco de dados SQLite com schema versionado e migrações automáticas
- **Normalização de IoCs** - Deduplicação inteligente e normalização de indicadores
- **Rate Limiting Inteligente** - Backoff exponencial com leitura de cabeçalhos `Retry-After`
- **Suporte a Proxy** - Rotação de proxies HTTP/SOCKS com retry automático
- **Cache em Camadas** - Cache local em SQLite com TTL configurável

### Advanced Features v2.0
- **Sistema de Métricas Prometheus** - Monitoramento completo com exportação para Prometheus
- **Validação Avançada** - Validadores para todos os tipos de IoCs (IP, domínio, hash, URL, etc.)
- **Enriquecimento de Dados** - Sistema de scoring e cálculo de threat level
- **Exportação Multi-formato** - JSON, CSV, STIX 2.1, MISP, texto puro
- **API REST Expandida** - 15+ endpoints com filtros avançados e paginação
- **Estatísticas Detalhadas** - Análise de tendências, distribuição por fonte e tipo
- **Relacionamentos entre IoCs** - Sistema de correlação de indicadores
- **Audit Log** - Registro completo de mudanças e operações

### Architecture
```
brintel/
├── api_clients/      # Clientes para APIs de TI
├── core/            # Orquestração e rate limiting
├── data/            # Persistência e repositório
├── models/          # Modelos de dados
├── proxy/           # Gerenciamento de proxies
├── services/        # API REST FastAPI
└── utils/           # Utilidades (config, cache, logging, metrics, validators, exporters)
```

## 📦 Instalação

### Requisitos
- Python 3.10+
- pip

### Instalação Rápida

```bash
# Clone o repositório
git clone https://github.com/GhostN3xus/BRIntelcollector.git
cd BRIntelcollector

# Instale as dependências
pip install -r requirements.txt

# Instale em modo de desenvolvimento
pip install -e .
```

### Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
# API Keys
BRINTEL_OTX_API_KEY=sua-chave-otx
BRINTEL_VT_API_KEY=sua-chave-virustotal
BRINTEL_ABUSEIPDB_API_KEY=sua-chave-abuseipdb
BRINTEL_SHODAN_API_KEY=sua-chave-shodan
BRINTEL_XFE_API_KEY=sua-chave-xforce
BRINTEL_MISP_API_KEY=sua-chave-misp

# Rate Limiting
BRINTEL_RATE_DYNAMIC=true
BRINTEL_API_TIMEOUT=30.0

# Cache
BRINTEL_CACHE_TTL_SECONDS=3600
BRINTEL_CACHE_PATH=data/cache.sqlite

# Database
BRINTEL_SQLITE_DB_PATH=data/brintel.db

# Proxy (opcional)
BRINTEL_PROXY_ENABLED=false
BRINTEL_PROXY_LIST=proxies.txt
BRINTEL_PROXY_ROTATE=true

# API
BRINTEL_ALLOWED_HOSTS=["*"]
```

## 🖥️ Uso da CLI

### Comandos Básicos

```bash
# Buscar IoCs em uma fonte específica
brintel search --source otx --term "malicious.com"
brintel search --source virustotal --term "8.8.8.8"

# Coletar indicadores de todas as fontes
brintel collect --since 24h
brintel collect --since 7d
brintel collect --all  # Coleta completa

# Servir a API REST
brintel serve --host 0.0.0.0 --port 8000

# Modo verbose para debugging
brintel -v search --source otx --term "test.com"
```

### Exemplos Avançados

```bash
# Coletar e exportar em formato STIX 2.1
brintel collect --since 24h --export stix --output indicators.json

# Buscar com filtros específicos
brintel search --source otx --term "malware" --min-confidence 80

# Coletar apenas de fontes específicas
brintel collect --sources otx,virustotal --since 12h
```

## 🌐 API REST

### Iniciar o Servidor

```bash
brintel serve --host 0.0.0.0 --port 8000
```

Acesse a documentação interativa em:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints Principais

#### Health & Status
```bash
# Health check
GET /v1/health

# Status detalhado do sistema
GET /v1/status
```

#### Search & Query
```bash
# Buscar em uma fonte específica
GET /v1/search?source=otx&q=malicious.com

# Listar indicadores com filtros
GET /v1/indicators?type=domain&min_confidence=80&limit=100

# Indicadores recentes
GET /v1/indicators/recent?hours=24&limit=100

# Indicadores de alta confiança
GET /v1/indicators/high-confidence?min_confidence=90
```

#### Collection
```bash
# Triggar coleta manual
POST /v1/collect
POST /v1/collect?since=2024-01-01T00:00:00
```

#### Statistics
```bash
# Estatísticas gerais
GET /v1/stats

# Estatísticas por fonte
GET /v1/stats/sources

# Estatísticas por tipo
GET /v1/stats/types

# Análise de tendências
GET /v1/stats/trends?days=7
```

#### Metrics & Monitoring
```bash
# Métricas em JSON
GET /metrics

# Métricas em formato Prometheus
GET /metrics/prometheus
```

#### Export
```bash
# Exportar em JSON
GET /v1/export?format=json&limit=1000

# Exportar em CSV
GET /v1/export?format=csv&min_confidence=70

# Filtros avançados
GET /v1/export?format=json&type=domain&source=otx&min_confidence=80
```

### Exemplos com cURL

```bash
# Buscar um domínio no OTX
curl "http://localhost:8000/v1/search?source=otx&q=evil.com"

# Coletar indicadores das últimas 24h
curl -X POST "http://localhost:8000/v1/collect"

# Obter estatísticas
curl "http://localhost:8000/v1/stats"

# Exportar para CSV
curl "http://localhost:8000/v1/export?format=csv" -o indicators.csv

# Métricas Prometheus
curl "http://localhost:8000/metrics/prometheus"
```

### Exemplos com Python

```python
import requests

# Buscar indicadores
response = requests.get(
    "http://localhost:8000/v1/indicators",
    params={
        "type": "domain",
        "min_confidence": 80,
        "limit": 50
    }
)
indicators = response.json()

# Triggar coleta
response = requests.post(
    "http://localhost:8000/v1/collect",
    params={"since": "2024-01-01T00:00:00"}
)
result = response.json()
print(f"Coletados: {result['indicators_collected']} indicadores")

# Obter estatísticas
response = requests.get("http://localhost:8000/v1/stats")
stats = response.json()
print(f"Total de indicadores: {stats['total_indicators']}")
```

## 📊 Sistema de Métricas

### Métricas Disponíveis

- **api_calls_total** - Contador de chamadas de API por fonte e status
- **indicators_collected_total** - Total de indicadores coletados por fonte
- **errors_total** - Total de erros por tipo e fonte
- **api_search_*_duration** - Histograma de duração de buscas
- **api_collection_duration** - Histograma de duração de coletas

### Integração com Prometheus

Adicione ao seu `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'brintelcollector'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics/prometheus'
    scrape_interval: 15s
```

## 🔧 Exportação de Dados

### Formatos Suportados

#### 1. JSON
```bash
curl "http://localhost:8000/v1/export?format=json" -o indicators.json
```

#### 2. CSV
```bash
curl "http://localhost:8000/v1/export?format=csv" -o indicators.csv
```

#### 3. STIX 2.1
```python
from brintel.utils.exporters import STIX2Exporter
from brintel.data import IndicatorRepository

repo = IndicatorRepository()
indicators = repo.search(limit=100)

exporter = STIX2Exporter()
stix_data = exporter.export(indicators)

with open('indicators.stix', 'w') as f:
    f.write(stix_data)
```

#### 4. MISP Format
```python
from brintel.utils.exporters import MISPExporter

exporter = MISPExporter()
misp_data = exporter.export(indicators)
```

## 🔍 Validação de IoCs

```python
from brintel.utils.validators import IndicatorValidator

# Validar e identificar tipo
is_valid, ioc_type, error = IndicatorValidator.validate_and_identify("8.8.8.8")
print(f"Valid: {is_valid}, Type: {ioc_type}")  # Valid: True, Type: ip

# Validações específicas
IndicatorValidator.is_ipv4("192.168.1.1")  # True
IndicatorValidator.is_domain("example.com")  # True
IndicatorValidator.is_sha256("abc123...")  # True

# Normalização
normalized = IndicatorValidator.normalize_domain("EXAMPLE.COM.")
# Returns: "example.com"

# Defang/Refang
defanged = IndicatorValidator.defang("http://evil.com", "url")
# Returns: "hxxp://evil[.]com"

refanged = IndicatorValidator.refang("hxxp://evil[.]com")
# Returns: "http://evil.com"
```

## 🎯 Enrichment e Scoring

```python
from brintel.utils.validators import EnrichmentScorer

# Calcular confidence score
score = EnrichmentScorer.calculate_confidence_score(
    detections=15,
    total_engines=70,
    age_days=2,
    source_reputation=85,
    cross_references=3
)
print(f"Confidence: {score}/100")

# Calcular threat level
level = EnrichmentScorer.calculate_threat_level(
    confidence=90,
    indicator_type="domain",
    tags=["malware", "c2"]
)
print(f"Threat Level: {level}")  # "critical"
```

## 💾 Database Schema

O BRIntelcollector 2.0 utiliza um schema de banco de dados avançado com:

- **indicators** - Tabela principal de indicadores
- **indicator_tags** - Tags associadas a indicadores
- **indicator_relationships** - Relacionamentos entre indicadores
- **sync_state** - Estado de sincronização por fonte
- **collection_metrics** - Métricas de coleta
- **enrichment_cache** - Cache de enriquecimento
- **audit_log** - Log de auditoria
- **schema_version** - Controle de versão do schema

### Migrações Automáticas

O sistema detecta automaticamente a versão do schema e aplica migrações quando necessário.

## 🧪 Desenvolvimento

### Setup do Ambiente

```bash
# Instalar dependências de desenvolvimento
pip install -r requirements.txt

# Instalar hooks de pre-commit (opcional)
pip install pre-commit
pre-commit install
```

### Qualidade de Código

```bash
# Formatação
black .

# Linting
flake8 .

# Type checking
mypy brintel

# Tudo de uma vez
black . && flake8 . && mypy brintel
```

### Testes

```bash
# Executar todos os testes
pytest

# Com coverage
pytest --cov=brintel --cov-report=html

# Testes específicos
pytest tests/test_api.py
pytest tests/test_repository.py -v
```

## 📈 Performance

### Otimizações Implementadas

- **Async/Await** - Coleta paralela de múltiplas fontes
- **Connection Pooling** - Reuso de conexões HTTP
- **Database Indexes** - Queries otimizadas com múltiplos índices
- **Caching em Camadas** - Cache de respostas de API e queries
- **Batching** - Inserção em lote no banco de dados
- **Rate Limiting Inteligente** - Evita bloqueios e throttling

### Benchmarks

Em um servidor modesto:
- ~1000 indicadores coletados/minuto
- ~100ms latência média de API
- ~10ms queries de banco de dados
- Suporta 100+ requisições simultâneas

## 🔐 Segurança

- **API Keys** - Nunca commite chaves no código
- **Input Validation** - Validação rigorosa de todos os inputs
- **SQL Injection** - Proteção com parameterized queries
- **Rate Limiting** - Proteção contra abuso de API
- **CORS** - Configurável via settings

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

Consulte [CONTRIBUTING.md](CONTRIBUTING.md) para mais detalhes.

## 📝 License

Este projeto está licenciado sob a MIT License - veja o arquivo LICENSE para detalhes.

## 🙏 Agradecimentos

- AlienVault OTX
- VirusTotal
- IBM X-Force Exchange
- abuse.ch (ThreatFox)
- AbuseIPDB
- Comunidade de Threat Intelligence

## 📞 Suporte

- **Issues**: https://github.com/GhostN3xus/BRIntelcollector/issues
- **Discussions**: https://github.com/GhostN3xus/BRIntelcollector/discussions

---

**Desenvolvido com ❤️ para a comunidade de Threat Intelligence**
