# BRIntelcollector

BRIntelcollector é uma plataforma modular para coleta e normalização de Indicadores de Comprometimento (IoCs) a partir de múltiplas fontes de inteligência de ameaças. O projeto fornece uma CLI moderna, API REST local e bibliotecas reutilizáveis para automatizar fluxos de coleta com controle dinâmico de *rate limit* e uso opcional de proxies rotativos.

## Recursos principais

- Estrutura modular (`brintel/core`, `brintel/api_clients`, `brintel/proxy`, `brintel/utils`).
- Clientes padronizados para AlienVault OTX, IBM X-Force Exchange, VirusTotal, MISP/ThreatFox/AbuseIPDB/Shodan.
- Normalização de IoCs com deduplicação e armazenamento em SQLite.
- Rate manager com *backoff* exponencial, leitura de cabeçalhos `Retry-After` e integração com proxy.
- CLI baseada em Typer com comandos `search`, `collect` e `serve`.
- API REST em FastAPI (`/v1/search`, `/v1/iocs`, `/v1/health`, `/metrics`).
- Cache local em SQLite, logging estruturado e suporte a proxies HTTP/SOCKS.
- Pipeline CI com lint (`black`, `flake8`, `mypy`) e testes (`pytest`).

## Instalação

```bash
pip install -r requirements.txt
pip install -e .
```

Configure as variáveis de ambiente no arquivo `.env` (exemplo):

```env
BRINTEL_OTX_API_KEY="sua-chave"
BRINTEL_PROXY_ENABLED=true
BRINTEL_RATE_DYNAMIC=true
```

## Uso da CLI

```bash
# Buscar IoCs em uma fonte específica
brintel search --source otx --term "example.com"

# Coletar indicadores de todas as fontes desde as últimas 24h
brintel collect --since 24h

# Servir a API REST local
brintel serve --host 0.0.0.0 --port 8000
```

## API REST

Após executar `brintel serve`, os principais endpoints ficam disponíveis:

- `GET /v1/health` — status do serviço.
- `GET /v1/search?source=otx&q=dominio` — consulta de IoCs em uma fonte.
- `GET /v1/iocs?since=2024-01-01T00:00:00` — coleta incremental e retorno em formato JSON.
- `GET /metrics` — métricas básicas para monitoramento.

## Desenvolvimento

```bash
# Formatação e lint
black .
flake8 .
mypy brintel

# Testes
pytest
```

Consulte o [CONTRIBUTING.md](CONTRIBUTING.md) para detalhes adicionais e abra *issues* seguindo os templates definidos.
