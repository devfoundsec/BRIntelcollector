#!/usr/bin/python3
from dotenv import load_dotenv
from os import environ
from OTXv2 import OTXv2
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import logging

load_dotenv()
otx = OTXv2(environ["OTX_KEY"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_indicators_for_pulse(pulse_id):
    """
    Busca indicadores de um único pulse.
    Retorna tupla (pulse_id, indicators) para mapeamento.
    """
    try:
        indicators = otx.get_pulse_indicators(pulse_id)
        return pulse_id, indicators
    except Exception as e:
        logger.error(f"Erro ao buscar indicadores do pulse {pulse_id}: {e}")
        return pulse_id, []


def get_all_indicators_parallel(pulse_ids, max_workers=10):
    """
    Busca indicadores de múltiplos pulses em paralelo.
    Retorna dicionário {pulse_id: [indicators]}
    """
    indicators_map = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_id = {
            executor.submit(get_indicators_for_pulse, pid): pid 
            for pid in pulse_ids
        }
        
        for future in as_completed(future_to_id):
            pulse_id, indicators = future.result()
            indicators_map[pulse_id] = indicators
    
    return indicators_map


def enrich_pulses_with_indicators(pulses, max_workers=10):
    """
    Enriquece lista de pulses com seus indicadores.
    Estrutura final: cada pulse contém chave 'indicators' com lista de indicadores.
    
    Args:
        pulses: Lista de dicionários de pulses
        max_workers: Número de threads paralelas
    
    Returns:
        Lista de pulses enriquecidos com indicators
    """
    if not pulses:
        return []
    
    # Extrai IDs dos pulses
    pulse_ids = [pulse.get('id') for pulse in pulses if pulse.get('id')]
    
    if not pulse_ids:
        logger.warning("Nenhum pulse com ID válido encontrado")
        return pulses
    
    logger.info(f"Buscando indicadores para {len(pulse_ids)} pulses...")
    
    # Busca indicadores em paralelo
    indicators_map = get_all_indicators_parallel(pulse_ids, max_workers)
    
    # Enriquece pulses com indicadores
    enriched_pulses = []
    for pulse in pulses:
        pulse_id = pulse.get('id')
        
        # Cria cópia para não modificar original
        enriched_pulse = pulse.copy()
        
        # Adiciona indicadores se existirem
        if pulse_id in indicators_map:
            enriched_pulse['indicators'] = indicators_map[pulse_id]
        else:
            enriched_pulse['indicators'] = []
        
        enriched_pulses.append(enriched_pulse)
    
    logger.info(f"Enriquecimento concluído: {len(enriched_pulses)} pulses processados")
    return enriched_pulses


@lru_cache(maxsize=128)
def search_cached(term, origin):
    """
    Cache de buscas para evitar queries repetidas.
    """
    try:
        return otx.search_pulses(f"{term} {origin}")
    except Exception as e:
        logger.error(f"Erro ao buscar '{term} {origin}': {e}")
        return {"results": []}


def search(term, parallel=True, deduplicate=True):
    """
    Busca otimizada com opções de paralelização e deduplicação.
    
    Args:
        term: Termo de busca
        parallel: Se True, executa buscas em paralelo
        deduplicate: Se True, remove resultados duplicados
    
    Returns:
        Lista de pulses (sem indicators ainda)
    """
    origins = ['Brasil', 'Brazil', 'BR', 'country:"Brazil"']
    
    if parallel:
        # Busca paralela - muito mais rápido
        results = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(search_cached, term, origin) for origin in origins]
            
            for future in as_completed(futures):
                blob = future.result()
                if blob and "results" in blob:
                    results.extend(blob["results"])
    else:
        # Busca sequencial (fallback)
        results = []
        for origin in origins:
            blob = search_cached(term, origin)
            if blob and "results" in blob:
                results.extend(blob["results"])
    
    # Remove duplicatas por ID se solicitado
    if deduplicate and results:
        seen_ids = set()
        unique_results = []
        
        for item in results:
            item_id = item.get("id")
            if item_id and item_id not in seen_ids:
                seen_ids.add(item_id)
                unique_results.append(item)
            elif not item_id:
                unique_results.append(item)
        
        return unique_results
    
    return results


def search_with_indicators(term, parallel=True, deduplicate=True, max_workers=10):
    """
    Pipeline completo: busca pulses e enriquece com indicators.
    
    Args:
        term: Termo de busca
        parallel: Se True, executa buscas em paralelo
        deduplicate: Se True, remove pulses duplicados
        max_workers: Threads para buscar indicators
    
    Returns:
        Lista de pulses com indicators aninhados
    """
    logger.info(f"Iniciando busca por: {term}")
    
    # 1. Busca pulses
    pulses = search(term, parallel=parallel, deduplicate=deduplicate)
    logger.info(f"Encontrados {len(pulses)} pulses")
    
    if not pulses:
        return []
    
    # 2. Enriquece com indicators
    enriched_pulses = enrich_pulses_with_indicators(pulses, max_workers=max_workers)
    
    # 3. Log de estatísticas
    total_indicators = sum(len(p.get('indicators', [])) for p in enriched_pulses)
    logger.info(f"Total de indicators coletados: {total_indicators}")
    
    return enriched_pulses


def batch_search_with_indicators(terms, parallel=True, max_workers=10):
    """
    Busca múltiplos termos e enriquece com indicators.
    Útil para processar várias queries de uma vez.
    
    Args:
        terms: Lista de termos de busca
        parallel: Se True, busca termos em paralelo
        max_workers: Threads para buscar indicators
    
    Returns:
        Dicionário {term: [pulses_with_indicators]}
    """
    results = {}
    
    if parallel:
        with ThreadPoolExecutor(max_workers=len(terms)) as executor:
            future_to_term = {
                executor.submit(search_with_indicators, term, True, True, max_workers): term 
                for term in terms
            }
            
            for future in as_completed(future_to_term):
                term = future_to_term[future]
                results[term] = future.result()
    else:
        for term in terms:
            results[term] = search_with_indicators(term, False, True, max_workers)
    
    return results