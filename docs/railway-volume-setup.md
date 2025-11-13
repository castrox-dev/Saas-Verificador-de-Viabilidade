# Configuração de Railway Volume para Arquivos de Mídia

## Problema

O Railway usa um filesystem **efêmero**, o que significa que todos os arquivos salvos em `MEDIA_ROOT` são **perdidos quando o container reinicia**. Isso afeta:

- Arquivos de mapas CTO (KMZ/KML)
- Outros uploads de arquivos

## Solução: Usar Railway Volume (Persistente)

### Passo 1: Criar Volume no Railway

1. Acesse seu projeto no Railway
2. Vá em **"Volumes"** no menu lateral
3. Clique em **"New Volume"**
4. Configure:
   - **Name**: `media-volume` (ou qualquer nome)
   - **Mount Path**: `/data` (padrão recomendado)
   - **Size**: Escolha o tamanho necessário (ex: 10GB para começar)

### Passo 2: Configurar Variável de Ambiente (Opcional)

Se você usar um caminho diferente de `/data`, configure a variável:

```
RAILWAY_VOLUME_PATH=/seu/caminho/personalizado
```

O padrão é `/data` se a variável não estiver definida.

### Passo 3: Conectar o Volume ao Serviço

1. Vá em **"Settings"** do seu serviço Django
2. Em **"Volumes"**, adicione o volume criado
3. Certifique-se de que o **Mount Path** seja `/data` (ou o caminho configurado)

### Passo 4: Verificar Configuração

Após configurar, o sistema detectará automaticamente o volume e usará:

```
/data/media/
```

Em vez de:

```
/media/ (efêmero)
```

## Verificação

Após o deploy, verifique os logs. Você deve ver:

```
✅ Usando Railway Volume para arquivos de mídia: /data/media
```

Se não configurado corretamente, verá:

```
⚠️ ATENÇÃO: Railway Volume não encontrado em /data
⚠️ Arquivos de mídia serão salvos em /app/media (EFÊMERO)
```

## Re-upload Necessário

Após configurar o volume, você precisará **re-enviar os arquivos de mapas** através da interface web, pois os arquivos anteriores foram perdidos no filesystem efêmero.

## Alternativa: Storage Externo (S3, etc.)

Para uma solução mais robusta e escalável, considere usar:

- **AWS S3**
- **DigitalOcean Spaces**
- **Cloudflare R2**
- **Outros serviços de storage cloud**

Para isso, seria necessário instalar `django-storages` e configurar no `settings.py`.

## Troubleshooting

### Volume não está sendo usado

1. Verifique se o volume está conectado ao serviço
2. Verifique se o Mount Path está correto (`/data`)
3. Verifique os logs do Railway após o deploy
4. Confirme que o volume existe e está ativo

### Erro de permissões

Se houver erros de permissão ao salvar arquivos:

1. O Railway geralmente configura permissões automaticamente
2. Se necessário, ajuste via comandos no Railway CLI ou via Dockerfile

### Verificar caminho atual

O sistema automaticamente verifica se `/data` existe. Se não existir, usará o diretório local (efêmero).

