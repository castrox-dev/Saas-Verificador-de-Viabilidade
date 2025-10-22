/**
 * Sistema de Notificações Toast Profissional
 * Autor: RM Systems
 */

class ToastManager {
    constructor() {
        this.container = null;
        this.toasts = [];
        this.init();
    }

    init() {
        // Criar container se não existir
        if (!document.querySelector('.toast-container')) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        } else {
            this.container = document.querySelector('.toast-container');
        }
    }

    show(message, type = 'info', title = null, duration = 5000) {
        const toast = this.createToast(message, type, title, duration);
        this.container.appendChild(toast);
        this.toasts.push(toast);

        // Animar entrada
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);

        // Auto remover
        if (duration > 0) {
            this.startProgress(toast, duration);
            setTimeout(() => {
                this.remove(toast);
            }, duration);
        }

        return toast;
    }

    createToast(message, type, title, duration) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };

        const titles = {
            success: title || 'Sucesso',
            error: title || 'Erro',
            warning: title || 'Atenção',
            info: title || 'Informação'
        };

        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || icons.info}</div>
            <div class="toast-content">
                <div class="toast-title">${titles[type]}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="toastManager.remove(this.parentElement)">×</button>
            ${duration > 0 ? '<div class="toast-progress"></div>' : ''}
        `;

        return toast;
    }

    startProgress(toast, duration) {
        const progress = toast.querySelector('.toast-progress');
        if (progress) {
            progress.style.width = '100%';
            setTimeout(() => {
                progress.style.width = '0%';
                progress.style.transition = `width ${duration}ms linear`;
            }, 50);
        }
    }

    remove(toast) {
        if (toast && toast.parentElement) {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.parentElement.removeChild(toast);
                }
                this.toasts = this.toasts.filter(t => t !== toast);
            }, 300);
        }
    }

    success(message, title = null, duration = 5000) {
        return this.show(message, 'success', title, duration);
    }

    error(message, title = null, duration = 7000) {
        return this.show(message, 'error', title, duration);
    }

    warning(message, title = null, duration = 6000) {
        return this.show(message, 'warning', title, duration);
    }

    info(message, title = null, duration = 5000) {
        return this.show(message, 'info', title, duration);
    }

    clear() {
        this.toasts.forEach(toast => this.remove(toast));
    }
}

// Instância global
const toastManager = new ToastManager();

// Funções de conveniência globais
window.showToast = (message, type, title, duration) => toastManager.show(message, type, title, duration);
window.showSuccess = (message, title, duration) => toastManager.success(message, title, duration);
window.showError = (message, title, duration) => toastManager.error(message, title, duration);
window.showWarning = (message, title, duration) => toastManager.warning(message, title, duration);
window.showInfo = (message, title, duration) => toastManager.info(message, title, duration);

// Converter mensagens Django em toasts
document.addEventListener('DOMContentLoaded', function() {
    const messages = document.querySelectorAll('.messages li');
    messages.forEach(message => {
        const text = message.textContent.trim();
        const classList = message.classList;
        
        let type = 'info';
        if (classList.contains('success')) type = 'success';
        else if (classList.contains('error')) type = 'error';
        else if (classList.contains('warning')) type = 'warning';
        
        if (text) {
            toastManager.show(text, type);
            message.style.display = 'none';
        }
    });
});

// Exportar para uso em módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ToastManager;
}