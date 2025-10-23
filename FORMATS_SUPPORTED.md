# 📁 Formatos de Arquivo Suportados - SaaS Verificador de Viabilidade

## **FORMATOS ACEITOS**

### **📊 Planilhas (Excel/CSV)**
- **.xlsx** - Excel 2007+
- **.xls** - Excel 97-2003
- **.csv** - Comma Separated Values

### **🗺️ Mapas CTO (KML/KMZ)**
- **.kml** - Keyhole Markup Language
- **.kmz** - Compressed KML (ZIP)

## **VALIDAÇÕES DE SEGURANÇA**

### **Para Arquivos Excel/CSV:**
✅ Verificação de MIME type real  
✅ Validação de estrutura interna  
✅ Detecção de macros maliciosas  
✅ Verificação de integridade  
✅ Limite de tamanho: 10MB  

### **Para Arquivos KML:**
✅ Verificação de estrutura XML válida  
✅ Detecção de elementos suspeitos (scripts, iframes)  
✅ Validação de elementos geográficos  
✅ Verificação de encoding UTF-8  
✅ Limite de tamanho: 10MB  

### **Para Arquivos KMZ:**
✅ Verificação de estrutura ZIP válida  
✅ Validação do KML interno  
✅ Detecção de arquivos suspeitos no ZIP  
✅ Verificação de tamanho descompactado  
✅ Limite de tamanho: 10MB (20MB descompactado)  

## **EXEMPLOS DE USO**

### **Upload de Mapa CTO KML:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Mapa CTO - Região Sul</name>
    <Placemark>
      <name>CTO-001</name>
      <description>Centro de Telecomunicações Ópticas</description>
      <Point>
        <coordinates>-46.6333,-23.5505,0</coordinates>
      </Point>
    </Placemark>
  </Document>
</kml>
```

### **Upload de Mapa CTO KMZ:**
- Arquivo ZIP contendo:
  - `doc.kml` (arquivo principal)
  - `images/` (pasta com imagens)
  - `styles/` (pasta com estilos)

## **RESTRIÇÕES DE SEGURANÇA**

### **❌ NÃO PERMITIDO:**
- Arquivos executáveis (.exe, .bat, .cmd, .scr)
- Scripts (.js, .vbs, .ps1)
- Arquivos de sistema (.dll, .sys)
- Documentos com macros (.docm, .xlsm)
- Arquivos comprimidos suspeitos

### **⚠️ VALIDAÇÕES ESPECIAIS:**
- **KML:** Não pode conter tags `<script>`, `<iframe>`, `<object>`
- **KMZ:** Não pode conter arquivos executáveis no ZIP
- **Excel:** Macros são detectadas e rejeitadas
- **CSV:** Código suspeito é detectado e rejeitado

## **LIMITES TÉCNICOS**

| Formato | Tamanho Máximo | Validações |
|---------|----------------|------------|
| .xlsx   | 10MB          | Estrutura, macros, integridade |
| .xls    | 10MB          | Estrutura, macros, integridade |
| .csv    | 10MB          | Encoding, conteúdo suspeito |
| .kml    | 10MB          | XML válido, elementos geográficos |
| .kmz    | 10MB          | ZIP válido, KML interno, arquivos |

## **PROCESSO DE VALIDAÇÃO**

### **1. Validação Básica:**
- Verificação de extensão
- Verificação de tamanho
- Verificação de nome do arquivo

### **2. Validação de Conteúdo:**
- Detecção de MIME type real
- Análise de estrutura interna
- Verificação de padrões suspeitos

### **3. Validação de Segurança:**
- Detecção de malware básica
- Verificação de integridade
- Análise de conteúdo malicioso

### **4. Validação Específica:**
- **Excel:** Verificação de macros, estrutura de planilha
- **CSV:** Verificação de encoding, conteúdo suspeito
- **KML:** Verificação de XML, elementos geográficos
- **KMZ:** Verificação de ZIP, KML interno, arquivos

## **LOGS DE SEGURANÇA**

Todos os uploads são registrados com:
- ✅ Usuário que fez upload
- ✅ Empresa associada
- ✅ Tipo de arquivo
- ✅ Tamanho do arquivo
- ✅ Hash SHA256
- ✅ Resultado da validação
- ✅ Timestamp

## **TROUBLESHOOTING**

### **Erro: "Tipo de arquivo não suportado"**
- Verificar se a extensão está correta
- Verificar se o MIME type é reconhecido
- Tentar renomear o arquivo

### **Erro: "Arquivo muito grande"**
- Reduzir tamanho do arquivo
- Comprimir arquivos KMZ
- Dividir planilhas grandes

### **Erro: "Conteúdo suspeito detectado"**
- Verificar se não há scripts no arquivo
- Limpar macros do Excel
- Verificar conteúdo do KML

## **SUPORTE TÉCNICO**

Para problemas com uploads:
- 📧 Email: suporte@rmsys.com.br
- 📞 Telefone: +55 11 99999-9999
- 💬 Chat: Disponível no sistema

---

**🎯 SISTEMA OTIMIZADO PARA MAPAS CTO!**
