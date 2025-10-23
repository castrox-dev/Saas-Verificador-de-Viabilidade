# 🎨 Sistema de Design RM Systems

## **📋 VISÃO GERAL**

Sistema de design completo baseado na identidade visual da RM Systems, incluindo sistema de cores, dark mode e componentes reutilizáveis.

## **🎨 PALETA DE CORES**

### **Cores Principais (Baseadas na Logo)**
```css
/* Azul principal da marca */
--rm-primary: #1D4ED8;        /* Azul principal */
--rm-primary-dark: #1E40AF;   /* Azul escuro */
--rm-primary-light: #3B82F6;  /* Azul claro */
--rm-primary-50: #EFF6FF;     /* Azul muito claro */
--rm-primary-100: #DBEAFE;    /* Azul claro de fundo */
```

### **Escala de Cinzas**
```css
--rm-gray-900: #0F172A;       /* Cinza escuro (texto principal) */
--rm-gray-800: #1E293B;       /* Cinza escuro secundário */
--rm-gray-700: #334155;       /* Cinza médio escuro */
--rm-gray-600: #475569;       /* Cinza médio */
--rm-gray-500: #64748B;       /* Cinza médio claro */
--rm-gray-400: #94A3B8;       /* Cinza claro */
--rm-gray-300: #CBD5E1;       /* Cinza muito claro */
--rm-gray-200: #E2E8F0;       /* Cinza de borda */
--rm-gray-100: #F1F5F9;       /* Cinza de fundo */
--rm-gray-50: #F8FAFC;        /* Cinza muito claro de fundo */
```

### **Cores Funcionais**
```css
--rm-success: #10B981;        /* Verde sucesso */
--rm-warning: #F59E0B;        /* Amarelo aviso */
--rm-error: #EF4444;          /* Vermelho erro */
--rm-info: #3B82F6;           /* Azul informação */
```

## **🌙 SISTEMA DE DARK MODE**

### **Ativação Automática**
- ✅ **Detecção do sistema:** Respeita `prefers-color-scheme`
- ✅ **Persistência:** Salva preferência no localStorage
- ✅ **Toggle manual:** Botão flutuante para alternar
- ✅ **Transições suaves:** Animações de 0.3s

### **Variáveis de Tema**
```css
/* Modo Claro */
:root {
  --rm-bg-primary: var(--rm-white);
  --rm-text-primary: var(--rm-gray-900);
  --rm-card-bg: var(--rm-white);
}

/* Modo Escuro */
[data-theme="dark"] {
  --rm-bg-primary: var(--rm-gray-900);
  --rm-text-primary: var(--rm-white);
  --rm-card-bg: var(--rm-gray-800);
}
```

## **🎯 COMPONENTES**

### **Botões**
```css
.btn.primary {
  background: var(--rm-button-primary);
  color: var(--rm-white);
  transition: all 0.3s ease;
}

.btn.primary:hover {
  background: var(--rm-button-primary-hover);
  transform: translateY(-2px);
}
```

### **Cards**
```css
.card {
  background: var(--rm-card-bg);
  border: 1px solid var(--rm-card-border);
  box-shadow: var(--rm-card-shadow);
  transition: all 0.3s ease;
}
```

### **Formulários**
```css
.input-inner {
  background: var(--rm-input-bg);
  border: 1px solid var(--rm-input-border);
  color: var(--rm-text-primary);
}
```

## **📱 RESPONSIVIDADE**

### **Breakpoints**
- **Mobile:** < 768px
- **Tablet:** 768px - 1024px
- **Desktop:** > 1024px

### **Adaptações Mobile**
```css
@media (max-width: 768px) {
  .theme-toggle {
    width: 45px;
    height: 45px;
    font-size: 16px;
  }
}
```

## **🎨 GRADIENTES**

### **Gradientes Principais**
```css
--rm-gradient-primary: linear-gradient(135deg, #1D4ED8 0%, #3B82F6 100%);
--rm-gradient-secondary: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%);
--rm-gradient-dark: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
```

## **📏 SOMBRAS**

### **Sistema de Sombras**
```css
--rm-shadow-sm: 0 1px 2px 0 rgba(15, 23, 42, 0.05);
--rm-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.1);
--rm-shadow-md: 0 10px 15px -3px rgba(15, 23, 42, 0.1);
--rm-shadow-lg: 0 20px 25px -5px rgba(15, 23, 42, 0.1);
--rm-shadow-xl: 0 25px 50px -12px rgba(15, 23, 42, 0.25);
```

## **⚡ ANIMAÇÕES**

### **Transições Padrão**
```css
* {
  transition: background-color 0.3s ease,
              border-color 0.3s ease,
              color 0.3s ease,
              box-shadow 0.3s ease;
}
```

### **Animações Especiais**
```css
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
```

## **🔧 IMPLEMENTAÇÃO**

### **Arquivos CSS**
1. `theme_colors.css` - Sistema de cores base
2. `dark-mode.css` - Estilos específicos do dark mode
3. `styles.css` - Estilos principais atualizados

### **JavaScript**
```javascript
// Inicialização automática
window.darkModeManager = new DarkModeManager();

// Controle manual
darkModeManager.toggleTheme();
darkModeManager.setTheme('dark');
```

### **HTML**
```html
<!-- Incluir no template base -->
<link rel="stylesheet" href="{% static 'css/theme_colors.css' %}" />
<link rel="stylesheet" href="{% static 'css/dark-mode.css' %}" />
<script src="{% static 'js/dark-mode.js' %}"></script>
```

## **🎯 BOAS PRÁTICAS**

### **Uso de Variáveis**
```css
/* ✅ Correto */
color: var(--rm-text-primary);

/* ❌ Evitar */
color: #0F172A;
```

### **Estados de Hover**
```css
.btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--rm-shadow-lg);
}
```

### **Acessibilidade**
```css
*:focus {
  outline: 2px solid var(--rm-primary);
  outline-offset: 2px;
}
```

## **📊 COMPATIBILIDADE**

### **Navegadores Suportados**
- ✅ Chrome 88+
- ✅ Firefox 85+
- ✅ Safari 14+
- ✅ Edge 88+

### **Recursos CSS**
- ✅ CSS Custom Properties
- ✅ CSS Grid
- ✅ Flexbox
- ✅ CSS Transitions
- ✅ Media Queries

## **🚀 PRÓXIMOS PASSOS**

1. **Testes de Acessibilidade**
   - Contraste de cores
   - Navegação por teclado
   - Leitores de tela

2. **Otimizações**
   - Lazy loading de estilos
   - Minificação CSS
   - Cache de recursos

3. **Componentes Adicionais**
   - Modais
   - Tooltips
   - Dropdowns
   - Accordions

---

**🎨 Sistema de Design RM Systems - Versão 1.0**
