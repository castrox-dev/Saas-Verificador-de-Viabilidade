/**
 * Sistema de Dark Mode para RM Systems SaaS
 * Gerencia a alternância entre modo claro e escuro
 */

class DarkModeManager {
    constructor() {
        this.themeKey = 'rm-theme';
        this.currentTheme = this.getStoredTheme();
        
        this.init();
    }
    
    init() {
        // Verificar se o tema já foi aplicado no <head>
        const html = document.documentElement;
        const currentDataTheme = html.getAttribute('data-theme');
        if (currentDataTheme && currentDataTheme !== this.currentTheme) {
            // Sincronizar com o tema já aplicado
            this.currentTheme = currentDataTheme;
            this.setStoredTheme(currentDataTheme);
        } else {
            this.applyTheme(this.currentTheme);
        }
        this.createThemeToggle();
        this.setupSystemThemeListener();
    }
    
    getStoredTheme() {
        try {
            const savedTheme = localStorage.getItem(this.themeKey);
            if (savedTheme) {
                return savedTheme;
            }
            // Se não houver tema salvo, detectar preferência do sistema
            return this.getSystemTheme();
        } catch (e) {
            return this.getSystemTheme();
        }
    }
    
    getSystemTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }
    
    setStoredTheme(theme) {
        try {
            localStorage.setItem(this.themeKey, theme);
        } catch (e) {
            console.warn('Não foi possível salvar o tema:', e);
        }
    }
    
    applyTheme(theme) {
        const html = document.documentElement;
        
        // Remove classes anteriores
        html.classList.remove('light-theme', 'dark-theme');
        
        // Aplica o tema atual
        if (theme === 'dark') {
            html.setAttribute('data-theme', 'dark');
            html.classList.add('dark-theme');
        } else {
            html.setAttribute('data-theme', 'light');
            html.classList.add('light-theme');
        }
        
        this.currentTheme = theme;
        this.setStoredTheme(theme);
        
        // Atualiza meta theme-color
        this.updateMetaThemeColor(theme);
        
        // Dispara evento customizado
        this.dispatchThemeChangeEvent(theme);
    }
    
    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
        return newTheme;
    }
    
    updateMetaThemeColor(theme) {
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            metaThemeColor.content = theme === 'dark' ? '#0F172A' : '#1D4ED8';
        }
    }
    
    dispatchThemeChangeEvent(theme) {
        const event = new CustomEvent('themeChanged', {
            detail: { theme: theme }
        });
        document.dispatchEvent(event);
    }
    
    createThemeToggle() {
        // Verifica se já existe o toggle
        if (document.getElementById('theme-toggle')) {
            return;
        }
        
        // Cria o botão de toggle
        const toggle = document.createElement('button');
        toggle.id = 'theme-toggle';
        toggle.className = 'theme-toggle theme-toggle-bottom-left';
        toggle.setAttribute('aria-label', 'Alternar tema');
        toggle.setAttribute('title', 'Alternar entre modo claro e escuro');
        
        // Ícone do toggle
        const icon = document.createElement('i');
        icon.className = this.currentTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        toggle.appendChild(icon);
        
        // Adiciona evento de clique
        toggle.addEventListener('click', () => {
            const newTheme = this.toggleTheme();
            const icon = toggle.querySelector('i');
            icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
            
            // Animação do ícone
            icon.style.transform = 'rotate(360deg)';
            setTimeout(() => {
                icon.style.transform = 'rotate(0deg)';
            }, 300);
        });
        
        // Adiciona estilos do toggle
        this.addToggleStyles();
        
        // Insere o toggle no DOM
        this.insertToggleInDOM(toggle);
    }
    
    addToggleStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .theme-toggle {
                position: fixed;
                z-index: 9999;
                width: 50px;
                height: 50px;
                border-radius: 50%;
                border: none;
                background: var(--rm-card-bg, #ffffff);
                color: var(--rm-text-primary, #333333);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
                border: 1px solid var(--rm-border-primary, #e2e8f0);
            }
            
            .theme-toggle i {
                color: var(--rm-text-primary);
                font-size: 18px;
                transition: all 0.3s ease;
            }
            
            .theme-toggle-bottom-left {
                bottom: 20px;
                left: 20px;
                position: fixed;
            }
            
            .theme-toggle:hover {
                transform: translateY(-2px) scale(1.05);
                box-shadow: var(--rm-shadow-xl);
                background: var(--rm-primary) !important;
                color: var(--rm-white) !important;
            }
            
            .theme-toggle:hover i {
                color: var(--rm-white) !important;
            }
            
            .theme-toggle:active {
                transform: translateY(0) scale(0.95);
                background: var(--rm-primary-dark) !important;
                color: var(--rm-white) !important;
            }
            
            .theme-toggle:active i {
                color: var(--rm-white) !important;
            }
            
            
            /* Responsividade */
            @media (max-width: 768px) {
                .theme-toggle {
                    bottom: 15px;
                    left: 15px;
                    width: 45px;
                    height: 45px;
                    font-size: 16px;
                }
            }
            
            @media (max-width: 480px) {
                .theme-toggle {
                    bottom: 10px;
                    left: 10px;
                    width: 40px;
                    height: 40px;
                    font-size: 14px;
                }
            }
            
            /* Animação de entrada */
            .theme-toggle {
                animation: slideInLeft 0.5s ease-out;
            }
            
            @keyframes slideInLeft {
                from {
                    transform: translateX(-100px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    insertToggleInDOM(toggle) {
        // Tenta inserir em diferentes locais
        const possibleContainers = [
            document.querySelector('.topbar'),
            document.querySelector('.nav-container'),
            document.querySelector('header'),
            document.querySelector('body')
        ];
        
        for (const container of possibleContainers) {
            if (container) {
                container.appendChild(toggle);
                return;
            }
        }
        
        // Fallback: adiciona ao body
        document.body.appendChild(toggle);
    }
    
    setupSystemThemeListener() {
        // Escuta mudanças no tema do sistema
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            
            const handleSystemThemeChange = (e) => {
                // Só aplica se o usuário não tiver escolhido um tema manualmente
                // Verifica se o tema atual é diferente do tema do sistema
                const savedTheme = localStorage.getItem(this.themeKey);
                const systemTheme = e.matches ? 'dark' : 'light';
                
                // Se não houver preferência salva OU se o tema salvo for 'auto' (futuro)
                // então seguir o tema do sistema
                if (!savedTheme || savedTheme === 'auto') {
                    this.applyTheme(systemTheme);
                    // Se estava vazio, salvar a preferência do sistema
                    if (!savedTheme) {
                        this.setStoredTheme(systemTheme);
                    }
                }
            };
            
            mediaQuery.addEventListener('change', handleSystemThemeChange);
        }
    }
    
    // Métodos públicos
    getCurrentTheme() {
        return this.currentTheme;
    }
    
    setTheme(theme) {
        if (['light', 'dark'].includes(theme)) {
            this.applyTheme(theme);
            const toggle = document.getElementById('theme-toggle');
            if (toggle) {
                const icon = toggle.querySelector('i');
                icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
            }
        }
    }
    
    isDarkMode() {
        return this.currentTheme === 'dark';
    }
    
    isLightMode() {
        return this.currentTheme === 'light';
    }
}

// Inicializa o gerenciador de tema quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.darkModeManager = new DarkModeManager();
});

// Exporta para uso global
window.DarkModeManager = DarkModeManager;
