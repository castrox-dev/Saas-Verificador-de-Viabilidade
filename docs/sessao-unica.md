# Controle Opcional de Sessão Única

> Esta funcionalidade ainda está desativada no código. Todas as instruções abaixo estão comentadas para evitar efeitos colaterais até que você decida habilitá-la em produção.

## Objetivo
Garantir que cada usuário mantenha apenas **uma sessão ativa**. Se alguém fizer login com a mesma conta em outro dispositivo/navegador, a sessão anterior é automaticamente encerrada.

## Recursos adicionados (comentados)

1. **Modelo opcional `UserSession`** – adicionado ao final de `core/models.py`.
2. **Sinal `ensure_single_session`** – localizado em `core/signals_single_session.py`.
3. **Hook no `CoreConfig`** – em `core/apps.py`, pronto para importar o sinal.

Todos os blocos estão envoltos em comentários e acompanhados de instruções inline.

## Como habilitar

1. **Modelo**
   - No final de `core/models.py`, remova os comentários do bloco `UserSession`.
   - Execute `python manage.py makemigrations` e `python manage.py migrate` para criar a tabela.

2. **Sinal**
   - Em `core/signals_single_session.py`, remova os comentários de todas as linhas para ativar o listener `user_logged_in`.

3. **Registrar o sinal**
   - Em `core/apps.py`, descomente o método `ready` e a importação de `core.signals_single_session`.
   - Verifique se `CoreConfig` está listado em `INSTALLED_APPS` (já está por padrão).

4. **Deploy**
   - Faça deploy com o novo código.
   - Ao primeiro login, a tabela `UserSession` será alimentada e qualquer login subsequente desligará a sessão anterior do mesmo usuário.

## Considerações

- Usuários derrubados podem receber mensagem de “sessão expirada” e precisarão logar novamente.
- O comportamento vale para **todos** os usuários; ajuste o sinal se quiser exceções (ex.: superusuários).
- Para reverter, basta comentar os blocos novamente (operação reversível).

> Dica: teste em ambiente de staging antes de ativar em produção para garantir que tudo se comporta como esperado.

