# 🔴 Problemas Identificados - Ordenados por Urgência

## ⚠️ URGÊNCIA CRÍTICA - Resolver IMEDIATAMENTE

> **Nota:** Problemas relacionados a DEBUG foram marcados como não críticos para ambiente de desenvolvimento.

### 1. 🔴 SECRET_KEY com valor padrão inseguro
**Arquivo:** `saas_viabilidade/settings.py:10`
**Problema:** Valor padrão de desenvolvimento pode ser usado em produção
```python
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
```
**Impacto:**
- Se SECRET_KEY não for definida, usa chave conhecida
- Permite falsificação de tokens/sessões
- Risco de acesso não autorizado

**Solução:** Exigir SECRET_KEY em produção ou gerar erro

---

### 2. 🔴 Rate Limiting Desabilitado em DEBUG (Para Produção)
**Arquivo:** `core/rate_limiting.py:93`
**Problema:** Rate limiting é totalmente desativado em modo DEBUG
```python
if settings.DEBUG:
    return view_func(request, *args, **kwargs)
```
**Impacto:**
- Pode ser esquecido em produção (crítico para prod)
- Em dev: aceitável para facilitar testes

**Solução:** Validar que rate limiting está ativo em produção (deploy check)

> **Nota Dev:** Aceitável em desenvolvimento, mas verificar antes de deploy para produção

---

### 3. 🔴 DEBUG=True Forçado (Para Produção)
**Arquivo:** `saas_viabilidade/settings.py:132`
**Problema:** DEBUG está sendo forçado como True mesmo após carregar do .env
```python
DEBUG = True  # Linha 132 - Sobrescreve valor do .env
```
**Nota:** Aceitável em dev, mas CRÍTICO remover antes de produção.

**Solução:** Adicionar verificação em deploy para garantir DEBUG=False em produção

---

## 🟠 URGÊNCIA ALTA - Resolver em até 1 semana

### 4. 🟠 Logging de Informações Sensíveis
**Arquivo:** `core/views.py:241-249`
**Problema:** Informações de login sendo logadas em nível INFO
```python
logger.info(f"Login attempt for company: {company_slug}, input: {input_id}, resolved username: {username}")
logger.info(f"User found: {user.username}, company: {user.company}, is_active: {user.is_active}")
```
**Impacto:**
- Logs podem expor informações de usuários
- Credenciais parciais podem ser registradas
- Violação de LGPD/GDPR

**Solução:** Usar logger.debug() ou remover informações sensíveis

---

### 5. 🟠 Falta de Validação em Exclusão de Empresas
**Arquivo:** `core/views.py:877-883`
**Problema:** Exclusão de empresa sem verificar dependências
```python
@require_http_methods(["POST"])
def rm_company_delete(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    try:
        company.delete()  # Pode causar cascata indesejada
```
**Impacto:**
- Pode deletar todos os usuários/mapas sem aviso
- Perda de dados sem confirmação adequada
- Sem rollback em caso de erro

**Solução:** Adicionar confirmação e verificação de dependências

---

### 6. 🟠 Arquivos Temporários Não Limpos
**Arquivo:** `core/verificador_service.py:218-240`
**Problema:** Arquivos temporários podem não ser limpos em caso de erro
```python
temp_path = cls._save_temp_file(uploaded_file)
# Se ocorrer erro aqui, arquivo não é limpo
result = DjangoVerificadorService.verificar_arquivo(temp_path, file_type)
cls._cleanup_temp_file(temp_path)
```
**Impacto:**
- Acúmulo de arquivos temporários
- Disco pode encher
- Possível vazamento de dados

**Solução:** Usar context manager ou try/finally garantindo limpeza

---

### 7. 🟠 Validação de Magic Number Muito Permissiva
**Arquivo:** `core/security_validators.py:354-365`
**Problema:** Magic number validation permite qualquer conteúdo se não validar
```python
if not is_valid:
    # Para CSV, verificar se é texto válido
    if file.name.lower().endswith('.csv'):
        # Aceita quase qualquer conteúdo como CSV válido
```
**Impacto:**
- Arquivos maliciosos podem passar como CSV válido
- Validação insuficiente de conteúdo real

**Solução:** Tornar validação mais rigorosa

---

## 🟡 URGÊNCIA MÉDIA - Resolver em até 1 mês

### 8. 🟡 Duplicação de Middleware
**Arquivo:** `core/middleware.py` e `core/middleware_security.py`
**Problema:** Dois middlewares fazendo coisas similares
- `CompanyMiddleware` (antigo)
- `SecureCompanyMiddleware` (novo)
**Impacto:**
- Código duplicado
- Manutenção confusa
- Possível conflito

**Solução:** Consolidar em um único middleware

---

### 9. 🟡 Falta de Testes Unitários
**Arquivo:** `verificador/tests.py:4`
**Problema:** TODO para adicionar testes
```python
# TODO: Adicionar testes unitários e de integração
```
**Impacto:**
- Mudanças podem quebrar funcionalidades
- Dificulta refatoração
- Sem garantia de qualidade

**Solução:** Implementar testes para componentes críticos

---

### 10. 🟡 Cache de Rate Limiting Pode Crescer Indefinidamente
**Arquivo:** `core/rate_limiting.py:40-63`
**Problema:** Lista de timestamps pode crescer sem limite teórico
```python
requests_data = cache.get(cache_key, [])
# Remove requisições antigas, mas lista pode ser grande
requests_data = [req_time for req_time in requests_data if req_time > cutoff_time]
```
**Impacto:**
- Uso excessivo de memória
- Performance degradada com muitos usuários

**Solução:** Usar estrutura de dados mais eficiente (contador circular)

---

### 11. 🟡 Tratamento de Erro Genérico em Upload
**Arquivo:** `core/views.py:426`
**Problema:** Exceções genéricas escondem erros reais
```python
except Exception as e:
    logger.error(f"Erro no upload: {str(e)}")
    return JsonResponse({'success': False, 'message': 'Erro interno do servidor'}, status=500)
```
**Impacto:**
- Dificulta debugging
- Usuário recebe mensagem genérica

**Solução:** Tratar exceções específicas e fornecer mensagens claras

---

### 12. 🟡 Geocoding sem Rate Limiting
**Arquivo:** `verificador/geocoding.py:54`
**Problema:** Chamadas a Nominatim sem controle de taxa
```python
response = requests.get(cls.BASE_URL, params=params, headers=headers, timeout=cls.TIMEOUT)
```
**Impacto:**
- Pode violar termos de uso do Nominatim
- IP pode ser bloqueado
- Sem retry logic

**Solução:** Adicionar rate limiting específico para geocoding

---

### 13. 🟡 Falta de Indexação em Consultas Frequentes
**Arquivo:** `core/models.py:200-204`
**Problema:** Índices existem, mas podem não ser suficientes
```python
indexes = [
    models.Index(fields=['company', 'processing_status']),
    models.Index(fields=['uploaded_by', 'uploaded_at']),
    models.Index(fields=['file_type', 'is_processed']),
]
```
**Impacto:**
- Queries lentas com crescimento do banco
- Performance degradada

**Solução:** Analisar queries e adicionar índices compostos conforme necessário

---

## 🔵 URGÊNCIA BAIXA - Melhorias e Otimizações

### 14. 🔵 Código Antigo do Flask Mantido
**Arquivo:** `verificador_flask/` e `core/verificador/`
**Problema:** Diretórios antigos ainda presentes (conforme README_VERIFICADOR.md)
**Impacto:**
- Confusão sobre qual código usar
- Espaço desperdiçado

**Solução:** Remover código antigo após verificar migração completa

---

### 15. 🔵 Hardcoded URLs em Templates
**Problema:** Algumas URLs podem estar hardcoded
**Impacto:**
- Dificulta mudanças de rota
- Não funciona com diferentes domínios

**Solução:** Usar `{% url %}` tag em todos os templates

---

### 16. 🔵 Falta de Documentação de API
**Problema:** Endpoints do verificador sem documentação
**Impacto:**
- Dificulta integração
- Desenvolvedores não sabem como usar APIs

**Solução:** Adicionar documentação com OpenAPI/Swagger

---

### 17. 🔵 Validação de Assinatura XLS Muito Específica
**Arquivo:** `core/security_validators.py:484`
**Problema:** Validação exata de 8 bytes pode falhar para XLS legítimos
```python
if not header.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
    raise ValidationError("Assinatura XLS inválida")
```
**Impacto:**
- Pode rejeitar arquivos XLS válidos
- Muito restritivo

**Solução:** Usar validação mais flexível (primeiros 4 bytes)

---

### 18. 🔵 Cache de Rotas com TTL Fixo
**Arquivo:** `verificador/routing.py:96`
**Problema:** Cache de rotas por 30 minutos pode estar desatualizado
```python
cache.set(cache_key, result, 1800)  # 30 minutos
```
**Impacto:**
- Rotas podem mudar (novas ruas)
- Dados desatualizados

**Solução:** Considerar TTL mais curto ou invalidar cache inteligentemente

---

### 19. 🔵 Sem Controle de Versão de APIs
**Problema:** APIs do verificador sem versionamento
**Impacto:**
- Mudanças quebram clientes existentes
- Sem histórico de versões

**Solução:** Implementar versionamento de API (v1, v2, etc)

---

### 20. 🔵 Logging Inconsistente
**Problema:** Alguns lugares usam logger, outros print
**Impacto:**
- Logs difíceis de filtrar
- Inconsistência

**Solução:** Padronizar uso de logger em todo o código

---

## 📊 Resumo

- **Críticos (Dev):** 1 problema (SECRET_KEY em produção)
- **Críticos (Produção):** 2 problemas (DEBUG e rate limiting)
- **Altos:** 4 problemas (semana)
- **Médios:** 7 problemas (mês)
- **Baixos:** 6 problemas (melhorias)

**Total:** 20 problemas identificados

---

## 🎯 Próximos Passos Recomendados

### Para Desenvolvimento (Agora)
1. **Hoje:** Corrigir SECRET_KEY (#1)
2. **Esta semana:** Resolver problemas de alta urgência (#4, #5, #6, #7)
3. **Este mês:** Implementar melhorias médias (#8-#13)

### Para Produção (Antes do Deploy)
1. Verificar DEBUG=False
2. Verificar rate limiting ativo
3. Validar SECRET_KEY segura
4. **Futuro:** Melhorias de baixa urgência (#14-#20)

---

*Documento gerado automaticamente - Revisar e atualizar conforme necessário*

