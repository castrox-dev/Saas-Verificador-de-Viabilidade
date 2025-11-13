# Troubleshooting - Erro de Push no GitHub

## Erro: "Internal Server Error" ao fazer push

Este erro geralmente indica um problema no lado do GitHub, mas pode ter várias causas.

## Soluções a tentar:

### 1. Verificar status do GitHub
Acesse: https://www.githubstatus.com/
Se houver problemas reportados, aguarde a resolução.

### 2. Tentar push novamente após alguns minutos
O erro pode ser temporário. Aguarde 5-10 minutos e tente novamente.

### 3. Verificar autenticação
Se estiver usando HTTPS, pode ser necessário atualizar as credenciais:
```bash
git config --global credential.helper manager-core
```

### 4. Tentar usar SSH ao invés de HTTPS
```bash
# Verificar se já tem SSH configurado
ssh -T git@github.com

# Se funcionar, alterar o remote:
git remote set-url origin git@github.com:castrox-dev/Saas-Verificador-de-Viabilidade.git
git push origin main
```

### 5. Fazer push de commits menores
Se houver muitos commits, tente fazer push de um por vez:
```bash
# Ver commits pendentes
git log origin/main..HEAD --oneline

# Fazer push de commits individuais (se necessário)
git push origin <commit-hash>:main
```

### 6. Verificar se há problemas com o repositório
- Acesse o repositório no GitHub
- Verifique se há problemas reportados
- Verifique se o repositório não está bloqueado ou com problemas

### 7. Limpar e tentar novamente
```bash
# Atualizar referências
git fetch origin

# Tentar push novamente
git push origin main
```

### 8. Verificar limites do GitHub
- Verifique se não excedeu limites de rate
- Verifique se o repositório não está muito grande

### 9. Tentar push para uma branch diferente
```bash
# Criar branch temporária
git checkout -b temp-fix
git push origin temp-fix

# Se funcionar, fazer merge via interface do GitHub
```

### 10. Contatar suporte do GitHub
Se nenhuma solução funcionar, pode ser necessário contatar o suporte do GitHub.

## Comandos úteis:

```bash
# Ver status
git status

# Ver commits pendentes
git log origin/main..HEAD

# Verificar remote
git remote -v

# Verificar tamanho do repositório
git count-objects -vH
```

