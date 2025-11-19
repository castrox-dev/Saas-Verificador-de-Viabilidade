# 🎯 Otimizações Implementadas - Marcação no Mapa

Este documento descreve as otimizações implementadas para melhorar a performance ao marcar pontos no mapa.

---

## 🐌 Problema Identificado

Ao clicar no mapa para marcar um ponto, havia demora porque:

1. **Geocodificação reversa bloqueante**: Esperava resposta da API antes de mostrar o marcador
2. **Processamento de muitos CTOs**: Calculava distância para TODOS os CTOs da empresa
3. **Roteamento lento**: Chamadas à API OSRM podiam demorar até 15 segundos
4. **Sem cache de CTOs**: `get_all_ctos` recalculava tudo a cada requisição
5. **Múltiplos cliques**: Não havia proteção contra cliques rápidos

---

## ✅ Otimizações Implementadas

### 1. Feedback Visual Imediato

**Arquivo:** `static/ftth_viewer/js/app.js` (função `onMapClick`)

- ✅ Marcador aparece **IMEDIATAMENTE** ao clicar
- ✅ Popup de confirmação aparece **sem esperar** geocodificação
- ✅ Geocodificação acontece em **background** e atualiza o popup depois

**Resultado:** Usuário vê feedback visual instantâneo (< 100ms)

---

### 2. Geocodificação Não-Bloqueante

**Arquivo:** `static/ftth_viewer/js/app.js`

- ✅ Geocodificação com timeout de 2 segundos
- ✅ Se demorar, usa coordenadas como fallback
- ✅ Não bloqueia a exibição do marcador

**Resultado:** Popup aparece imediatamente, endereço atualiza depois se disponível

---

### 3. Debounce de Cliques

**Arquivo:** `static/ftth_viewer/js/app.js`

- ✅ Ignora cliques muito rápidos (< 500ms entre cliques)
- ✅ Previne múltiplas requisições simultâneas

**Resultado:** Evita requisições duplicadas e melhora performance

---

### 4. Cache de CTOs

**Arquivo:** `ftth_viewer/utils.py` (função `get_all_ctos`)

- ✅ Cache de 1 hora para lista de CTOs por empresa
- ✅ Query otimizada com `.only()` e `.select_related()`
- ✅ Cache invalidado automaticamente ao fazer upload de novo mapa

**Resultado:** Primeira busca pode demorar, mas próximas são instantâneas

---

### 5. Filtro de Raio Inicial

**Arquivo:** `ftth_viewer/views.py` (função `api_verificar_viabilidade`)

- ✅ Busca inicial limitada a CTOs dentro de 5km
- ✅ Se não encontrar, expande busca para todos
- ✅ Reduz processamento desnecessário de CTOs distantes

**Resultado:** Processa menos CTOs, resposta mais rápida

---

### 6. Timeout Reduzido no Roteamento

**Arquivo:** `ftth_viewer/utils.py` (função `calcular_rota_ruas`)

- ✅ Timeout reduzido de 15s para 5s máximo
- ✅ Se API demorar, usa distância euclidiana como fallback
- ✅ Cache de rotas por 30 minutos

**Resultado:** Respostas mais rápidas, menos espera

---

### 7. Workers Paralelos Otimizados

**Arquivo:** `ftth_viewer/views.py`

- ✅ Ajusta número de workers baseado na quantidade de tarefas
- ✅ Máximo de 5 workers para não sobrecarregar

**Resultado:** Melhor uso de recursos, processamento mais eficiente

---

### 8. Loading Visual Melhorado

**Arquivo:** `static/ftth_viewer/js/app.js` (função `verificarViabilidade`)

- ✅ Mostra loading no popup imediatamente
- ✅ Feedback visual claro durante verificação

**Resultado:** Usuário sabe que o sistema está processando

---

## 📊 Impacto Esperado

### Antes:
- ⏱️ Tempo até ver marcador: **1-3 segundos** (esperando geocodificação)
- ⏱️ Tempo de verificação: **5-15 segundos** (processando todos os CTOs)
- 🔄 Processamento: Todos os CTOs sempre recalculados

### Depois:
- ⚡ Tempo até ver marcador: **< 100ms** (instantâneo)
- ⚡ Tempo de verificação: **2-5 segundos** (com cache e filtros)
- ⚡ Com cache: **< 1 segundo** (se já foi calculado antes)

---

## 🔧 Configurações Ajustáveis

### Timeout de Geocodificação:
```javascript
// Em onMapClick, linha ~3694
const geoTimeout = setTimeout(() => geoController.abort(), 2000); // 2 segundos
```

### Raio Inicial de Busca:
```python
# Em api_verificar_viabilidade, linha ~653
MAX_INITIAL_RADIUS = 5000  # 5km em metros
```

### Timeout de Roteamento:
```python
# Em calcular_rota_ruas, linha ~279
timeout = min(getattr(settings, 'FTTH_ROUTING_TIMEOUT', 15), 5)  # Máximo 5s
```

### Cache de CTOs:
```python
# Em get_all_ctos, linha ~549
cache.set(cache_key, coords, 3600)  # 1 hora
```

---

## 🚀 Próximas Otimizações Possíveis

1. **Cache de resultados de verificação** (já existe, mas pode melhorar)
2. **Pré-carregar CTOs** quando mapa carrega
3. **Web Workers** para cálculos pesados em background
4. **Service Worker** para cache offline
5. **Índice espacial** no banco para buscas por proximidade

---

**Última atualização:** 2025-11-19

