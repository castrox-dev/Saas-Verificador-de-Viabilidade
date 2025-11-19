/**
 * Sistema Global de Loading Screen
 * Intercepta requisições HTTP e mostra loading automaticamente
 * para requisições que demoram mais de 500ms
 */

class GlobalLoadingScreen {
    constructor() {
        this.loadingOverlay = null;
        this.activeRequests = new Set();
        this.minLoadingTime = 500; // Mostrar loading apenas se demorar mais de 500ms
        this.loadingTimeout = null;
        this.init();
    }

    init() {
        this.createLoadingOverlay();
        this.interceptFetch();
        this.interceptXMLHttpRequest();
        this.handlePageNavigation();
    }

    /**
     * Cria o overlay de loading global
     */
    createLoadingOverlay() {
        // Verificar se já existe
        if (document.getElementById('global-loading-overlay')) {
            this.loadingOverlay = document.getElementById('global-loading-overlay');
            return;
        }

        const overlay = document.createElement('div');
        overlay.id = 'global-loading-overlay';
        overlay.className = 'global-loading-overlay';
        overlay.innerHTML = `
            <div class="global-loading-content">
                <div class="global-loading-spinner">
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                </div>
                <div class="global-loading-text">Carregando...</div>
                <div class="global-loading-progress">
                    <div class="global-loading-progress-bar"></div>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        this.loadingOverlay = overlay;

        // Adicionar estilos
        this.injectStyles();
    }

    /**
     * Injeta estilos CSS
     */
    injectStyles() {
        if (document.getElementById('global-loading-styles')) return;

        const style = document.createElement('style');
        style.id = 'global-loading-styles';
        style.textContent = `
            .global-loading-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.75);
                backdrop-filter: blur(4px);
                z-index: 999999;
                display: none;
                align-items: center;
                justify-content: center;
                opacity: 0;
                transition: opacity 0.3s ease;
            }

            .global-loading-overlay.show {
                display: flex;
                opacity: 1;
            }

            .global-loading-content {
                text-align: center;
                color: white;
            }

            .global-loading-spinner {
                display: inline-block;
                position: relative;
                width: 80px;
                height: 80px;
                margin-bottom: 20px;
            }

            .spinner-ring {
                box-sizing: border-box;
                display: block;
                position: absolute;
                width: 64px;
                height: 64px;
                margin: 8px;
                border: 6px solid rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                animation: spinner-ring 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
                border-color: rgba(255, 255, 255, 0.3) transparent transparent transparent;
            }

            .spinner-ring:nth-child(1) {
                animation-delay: -0.45s;
            }

            .spinner-ring:nth-child(2) {
                animation-delay: -0.3s;
            }

            .spinner-ring:nth-child(3) {
                animation-delay: -0.15s;
            }

            @keyframes spinner-ring {
                0% {
                    transform: rotate(0deg);
                }
                100% {
                    transform: rotate(360deg);
                }
            }

            .global-loading-text {
                font-size: 18px;
                font-weight: 500;
                margin-bottom: 20px;
                color: white;
            }

            .global-loading-progress {
                width: 200px;
                height: 4px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 2px;
                overflow: hidden;
                margin: 0 auto;
            }

            .global-loading-progress-bar {
                height: 100%;
                background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
                width: 0%;
                animation: progress-bar 2s ease-in-out infinite;
                border-radius: 2px;
            }

            @keyframes progress-bar {
                0% {
                    width: 0%;
                    transform: translateX(0);
                }
                50% {
                    width: 70%;
                    transform: translateX(0);
                }
                100% {
                    width: 100%;
                    transform: translateX(0);
                }
            }

            /* Dark mode support */
            [data-theme="dark"] .global-loading-overlay {
                background: rgba(0, 0, 0, 0.85);
            }

            /* Mobile optimization */
            @media (max-width: 768px) {
                .global-loading-spinner {
                    width: 60px;
                    height: 60px;
                }

                .spinner-ring {
                    width: 48px;
                    height: 48px;
                    margin: 6px;
                    border-width: 4px;
                }

                .global-loading-text {
                    font-size: 16px;
                }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Mostra o loading screen
     */
    show() {
        if (!this.loadingOverlay) return;

        // Limpar timeout anterior se existir
        if (this.loadingTimeout) {
            clearTimeout(this.loadingTimeout);
        }

        // Mostrar após delay mínimo
        this.loadingTimeout = setTimeout(() => {
            if (this.activeRequests.size > 0) {
                this.loadingOverlay.classList.add('show');
            }
        }, this.minLoadingTime);
    }

    /**
     * Esconde o loading screen
     */
    hide() {
        if (!this.loadingOverlay) return;

        // Limpar timeout
        if (this.loadingTimeout) {
            clearTimeout(this.loadingTimeout);
            this.loadingTimeout = null;
        }

        // Esconder apenas se não houver requisições ativas
        if (this.activeRequests.size === 0) {
            this.loadingOverlay.classList.remove('show');
        }
    }

    /**
     * Adiciona uma requisição ativa
     */
    addRequest(requestId) {
        this.activeRequests.add(requestId);
        this.show();
    }

    /**
     * Remove uma requisição ativa
     */
    removeRequest(requestId) {
        this.activeRequests.delete(requestId);
        if (this.activeRequests.size === 0) {
            this.hide();
        }
    }

    /**
     * Intercepta fetch API
     */
    interceptFetch() {
        const originalFetch = window.fetch;
        const self = this;

        window.fetch = async function(...args) {
            const url = args[0];
            const options = args[1] || {};

            // Ignorar requisições de recursos estáticos e algumas APIs
            const ignorePatterns = [
                /\.(css|js|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$/i,
                /\/static\//,
                /\/media\//,
                /\/api\/health/,
                /\/api\/status/
            ];

            const shouldIgnore = ignorePatterns.some(pattern => {
                if (typeof url === 'string') {
                    return pattern.test(url);
                }
                if (url instanceof Request) {
                    return pattern.test(url.url);
                }
                return false;
            });

            if (shouldIgnore) {
                return originalFetch.apply(this, args);
            }

            const requestId = `fetch_${Date.now()}_${Math.random()}`;
            self.addRequest(requestId);

            try {
                const response = await originalFetch.apply(this, args);
                self.removeRequest(requestId);
                return response;
            } catch (error) {
                self.removeRequest(requestId);
                throw error;
            }
        };
    }

    /**
     * Intercepta XMLHttpRequest
     */
    interceptXMLHttpRequest() {
        const self = this;
        const originalOpen = XMLHttpRequest.prototype.open;
        const originalSend = XMLHttpRequest.prototype.send;

        XMLHttpRequest.prototype.open = function(method, url, ...rest) {
            this._url = url;
            this._method = method;
            return originalOpen.apply(this, [method, url, ...rest]);
        };

        XMLHttpRequest.prototype.send = function(...args) {
            const url = this._url;
            const method = this._method;

            // Ignorar requisições de recursos estáticos
            const ignorePatterns = [
                /\.(css|js|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$/i,
                /\/static\//,
                /\/media\//
            ];

            const shouldIgnore = ignorePatterns.some(pattern => pattern.test(url));

            if (shouldIgnore) {
                return originalSend.apply(this, args);
            }

            const requestId = `xhr_${Date.now()}_${Math.random()}`;
            self.addRequest(requestId);

            const originalOnReadyStateChange = this.onreadystatechange;
            this.onreadystatechange = function() {
                if (originalOnReadyStateChange) {
                    originalOnReadyStateChange.apply(this, arguments);
                }
                if (this.readyState === 4) {
                    self.removeRequest(requestId);
                }
            };

            this.addEventListener('loadend', () => {
                self.removeRequest(requestId);
            });

            this.addEventListener('error', () => {
                self.removeRequest(requestId);
            });

            return originalSend.apply(this, args);
        };
    }

    /**
     * Lida com navegação de página
     */
    handlePageNavigation() {
        // Mostrar loading em links que não são hash/anchor
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (!link) return;

            const href = link.getAttribute('href');
            if (!href) return;

            // Ignorar links especiais
            if (
                href.startsWith('#') ||
                href.startsWith('javascript:') ||
                link.hasAttribute('download') ||
                link.target === '_blank' ||
                link.hasAttribute('data-no-loading')
            ) {
                return;
            }

            // Mostrar loading para navegação
            this.show();
        });

        // Esconder loading quando página carregar
        window.addEventListener('load', () => {
            this.hide();
        });
    }

    /**
     * Força mostrar loading (útil para operações manuais)
     */
    forceShow(message = 'Carregando...') {
        if (this.loadingOverlay) {
            const textElement = this.loadingOverlay.querySelector('.global-loading-text');
            if (textElement) {
                textElement.textContent = message;
            }
        }
        this.show();
    }

    /**
     * Força esconder loading
     */
    forceHide() {
        this.activeRequests.clear();
        this.hide();
    }
}

// Inicializar quando DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.globalLoadingScreen = new GlobalLoadingScreen();
    });
} else {
    window.globalLoadingScreen = new GlobalLoadingScreen();
}

// Exportar para uso global
window.GlobalLoadingScreen = GlobalLoadingScreen;

