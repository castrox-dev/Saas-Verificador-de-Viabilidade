/**
 * Sistema de Loading States para RM Systems SaaS
 * Gerencia estados de carregamento em toda a aplicação
 */

class LoadingManager {
    constructor() {
        this.activeLoaders = new Set();
        this.defaultOptions = {
            text: 'Carregando...',
            spinner: 'fas fa-spinner fa-spin',
            overlay: true,
            duration: 0 // 0 = infinito até ser removido
        };
    }

    /**
     * Mostra um loading state
     * @param {string} elementId - ID do elemento
     * @param {Object} options - Opções de configuração
     */
    show(elementId, options = {}) {
        const element = document.getElementById(elementId);
        if (!element) {
            console.warn(`Elemento ${elementId} não encontrado`);
            return;
        }

        const config = { ...this.defaultOptions, ...options };
        const loaderId = `loader_${elementId}_${Date.now()}`;
        
        // Armazenar conteúdo original
        const originalContent = element.innerHTML;
        element.setAttribute('data-original-content', originalContent);
        element.setAttribute('data-loader-id', loaderId);

        // Criar HTML do loader
        const loaderHTML = this.createLoaderHTML(config);
        element.innerHTML = loaderHTML;

        // Adicionar classe de loading
        element.classList.add('loading-state');

        // Armazenar referência
        this.activeLoaders.add(loaderId);

        // Auto-remover se duration > 0
        if (config.duration > 0) {
            setTimeout(() => {
                this.hide(elementId);
            }, config.duration);
        }

        return loaderId;
    }

    /**
     * Esconde um loading state
     * @param {string} elementId - ID do elemento
     */
    hide(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const loaderId = element.getAttribute('data-loader-id');
        const originalContent = element.getAttribute('data-original-content');

        if (originalContent) {
            element.innerHTML = originalContent;
        }

        // Remover atributos
        element.removeAttribute('data-original-content');
        element.removeAttribute('data-loader-id');
        element.classList.remove('loading-state');

        // Remover da lista de loaders ativos
        if (loaderId) {
            this.activeLoaders.delete(loaderId);
        }
    }

    /**
     * Cria HTML do loader
     * @param {Object} config - Configuração do loader
     */
    createLoaderHTML(config) {
        const overlay = config.overlay ? 'loading-overlay' : '';
        
        return `
            <div class="loading-container ${overlay}">
                <div class="loading-content">
                    <i class="${config.spinner}"></i>
                    <span class="loading-text">${config.text}</span>
                </div>
            </div>
        `;
    }

    /**
     * Loading para botões
     * @param {string} buttonId - ID do botão
     * @param {string} text - Texto do loading
     */
    showButton(buttonId, text = 'Carregando...') {
        const button = document.getElementById(buttonId);
        if (!button) return;

        // Armazenar estado original
        button.setAttribute('data-original-text', button.innerHTML);
        button.setAttribute('data-original-disabled', button.disabled);

        // Aplicar loading
        button.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${text}`;
        button.disabled = true;
        button.classList.add('loading-button');
    }

    /**
     * Remove loading de botões
     * @param {string} buttonId - ID do botão
     */
    hideButton(buttonId) {
        const button = document.getElementById(buttonId);
        if (!button) return;

        const originalText = button.getAttribute('data-original-text');
        const originalDisabled = button.getAttribute('data-original-disabled');

        if (originalText) {
            button.innerHTML = originalText;
        }
        
        button.disabled = originalDisabled === 'true';
        button.classList.remove('loading-button');
    }

    /**
     * Loading para formulários
     * @param {string} formId - ID do formulário
     */
    showForm(formId) {
        const form = document.getElementById(formId);
        if (!form) return;

        // Desabilitar todos os inputs
        const inputs = form.querySelectorAll('input, select, textarea, button');
        inputs.forEach(input => {
            input.disabled = true;
            input.classList.add('loading-input');
        });

        // Adicionar overlay
        const overlay = document.createElement('div');
        overlay.className = 'form-loading-overlay';
        overlay.innerHTML = `
            <div class="form-loading-content">
                <i class="fas fa-spinner fa-spin"></i>
                <span>Processando...</span>
            </div>
        `;
        form.appendChild(overlay);
    }

    /**
     * Remove loading de formulários
     * @param {string} formId - ID do formulário
     */
    hideForm(formId) {
        const form = document.getElementById(formId);
        if (!form) return;

        // Reabilitar todos os inputs
        const inputs = form.querySelectorAll('input, select, textarea, button');
        inputs.forEach(input => {
            input.disabled = false;
            input.classList.remove('loading-input');
        });

        // Remover overlay
        const overlay = form.querySelector('.form-loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    }

    /**
     * Loading para tabelas
     * @param {string} tableId - ID da tabela
     */
    showTable(tableId) {
        const table = document.getElementById(tableId);
        if (!table) return;

        const tbody = table.querySelector('tbody');
        if (!tbody) return;

        // Armazenar conteúdo original
        tbody.setAttribute('data-original-content', tbody.innerHTML);

        // Mostrar loading
        tbody.innerHTML = `
            <tr>
                <td colspan="100%" class="table-loading">
                    <div class="table-loading-content">
                        <i class="fas fa-spinner fa-spin"></i>
                        <span>Carregando dados...</span>
                    </div>
                </td>
            </tr>
        `;
    }

    /**
     * Remove loading de tabelas
     * @param {string} tableId - ID da tabela
     */
    hideTable(tableId) {
        const table = document.getElementById(tableId);
        if (!table) return;

        const tbody = table.querySelector('tbody');
        if (!tbody) return;

        const originalContent = tbody.getAttribute('data-original-content');
        if (originalContent) {
            tbody.innerHTML = originalContent;
        }
    }

    /**
     * Remove todos os loaders ativos
     */
    hideAll() {
        this.activeLoaders.forEach(loaderId => {
            // Encontrar elemento pelo loader ID
            const element = document.querySelector(`[data-loader-id="${loaderId}"]`);
            if (element) {
                const elementId = element.id;
                this.hide(elementId);
            }
        });
    }

    /**
     * Verifica se há loaders ativos
     */
    hasActiveLoaders() {
        return this.activeLoaders.size > 0;
    }
}

// Instância global
window.loadingManager = new LoadingManager();

// CSS para loading states
const loadingCSS = `
    .loading-state {
        position: relative;
        pointer-events: none;
    }

    .loading-container {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        text-align: center;
    }

    .loading-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.8);
        z-index: 1000;
    }

    .loading-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
    }

    .loading-content i {
        font-size: 2rem;
        color: var(--rm-primary, #4facfe);
    }

    .loading-text {
        font-weight: 500;
        color: var(--rm-text-primary, #333);
    }

    .loading-button {
        opacity: 0.7;
        cursor: not-allowed !important;
    }

    .loading-input {
        opacity: 0.5;
        cursor: not-allowed !important;
    }

    .form-loading-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }

    .form-loading-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
        padding: 2rem;
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    .table-loading {
        text-align: center;
        padding: 3rem;
    }

    .table-loading-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
    }

    /* Dark mode */
    [data-theme="dark"] .loading-overlay {
        background: rgba(0, 0, 0, 0.8);
    }

    [data-theme="dark"] .form-loading-overlay {
        background: rgba(0, 0, 0, 0.9);
    }

    [data-theme="dark"] .form-loading-content {
        background: var(--rm-card-bg, #2d3748);
        color: var(--rm-text-primary, #e2e8f0);
    }
`;

// Adicionar CSS ao head
const style = document.createElement('style');
style.textContent = loadingCSS;
document.head.appendChild(style);

// Exportar para uso global
window.LoadingManager = LoadingManager;
