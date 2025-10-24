# Verificador de Viabilidade (SaaS)

Sistema SaaS multi-tenant para verificação de viabilidade de mapas CTO com isolamento completo entre empresas.

## 🚀 Funcionalidades

- **Multi-tenant**: Isolamento completo entre empresas
- **Verificador de Mapas**: Upload e análise de mapas CTO (.xlsx, .xls, .csv, .kml, .kmz)
- **Gestão de Usuários**: Controle de acesso por empresa
- **Dashboard Administrativo**: Visão completa para RM e empresas
- **Interface Responsiva**: Design moderno com dark mode
- **Segurança Avançada**: Validação de arquivos e rate limiting

## 🛠️ Tecnologias

- **Backend**: Django 5.2.7
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: SQLite (desenvolvimento) / PostgreSQL (produção)
- **Segurança**: Middleware customizado, validação de arquivos

## 📦 Instalação

### 1. Clone o repositório
```bash
git clone <repository-url>
cd Saas-Verificador-de-Viabilidade
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente
```bash
cp env.example .env
# Edite o arquivo .env com suas configurações
```

### 4. Execute as migrações
```bash
python manage.py migrate
```

### 5. Crie um superusuário
```bash
python manage.py createsuperuser
```

### 6. Execute o servidor
```bash
python manage.py runserver
```

## 🔧 Configuração

### Variáveis de Ambiente (.env)
```env
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

### Empresas e Usuários
- **RM Admin**: Acesso total ao sistema
- **Company Admin**: Gestão da empresa
- **Company User**: Acesso ao verificador

## 🔒 Segurança

- **Isolamento Multi-tenant**: Dados completamente separados
- **Validação de Arquivos**: Verificação de tipo e conteúdo
- **Rate Limiting**: Proteção contra spam
- **Headers de Segurança**: CSP, HSTS, X-Frame-Options
- **Validação de Senhas**: Políticas de segurança

## 📁 Estrutura do Projeto

```
├── core/                    # Aplicação principal
│   ├── models.py           # Modelos de dados
│   ├── views.py            # Views e lógica de negócio
│   ├── forms.py            # Formulários
│   ├── urls_*.py           # URLs por módulo
│   └── middleware_*.py     # Middlewares de segurança
├── templates/              # Templates HTML
├── static/                 # Arquivos estáticos
├── requirements.txt        # Dependências
└── manage.py              # Script de gerenciamento
```

## 🚀 Deploy

### Desenvolvimento
```bash
python manage.py runserver
```

### Produção
```bash
python manage.py collectstatic
python manage.py migrate
# Configure seu servidor web (nginx + gunicorn)
```

## 📊 Monitoramento

- **Logs**: Sistema de logging integrado
- **Métricas**: Performance e uso
- **Alertas**: Notificações de segurança

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

## 📞 Suporte

Para suporte, entre em contato através dos issues do GitHub ou email.

---

**Desenvolvido com ❤️ para otimização de processos de viabilidade**
