/**
 * Sistema de Notificações Toast para RM Systems SaaS
 */
class ToastManager {
    constructor() {
        this.toasts = new Map();
        this.container = null;
        this.init();
    }

    init() {
        this.createContainer();
        this.addStyles();
    }

    createContainer() {
        this.container = document.createElement('div');
        this.container.id = 'toast-container';
        this.container.className = 'toast-container';
        document.body.appendChild(this.container);
    }

    show(message, type = 'info', duration = 5000, options = {}) {
        const toastId = `toast_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        const toast = {
            id: toastId,
            message,
            type,
            duration,
            options: {
                position: 'top-right',
                closable: true,
                ...options
            }
        };

        this.toasts.set(toastId, toast);
        this.renderToast(toast);
        
        if (duration > 0) {
            setTimeout(() => this.hide(toastId), duration);
        }

        return toastId;
    }

    success(message, duration = 5000) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 7000) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration = 6000) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration = 5000) {
        return this.show(message, 'info', duration);
    }

    renderToast(toast) {
        const toastElement = document.createElement('div');
        toastElement.id = toast.id;
        toastElement.className = `toast toast-${toast.type}`;
        
        const icon = this.getIcon(toast.type);
        const closeButton = toast.options.closable ? 
            `<button class="toast-close" onclick="toastManager.hide('${toast.id}')">&times;</button>` : '';

        toastElement.innerHTML = `
            <div class="toast-content">
                <div class="toast-icon">${icon}</div>
                <div class="toast-message">${toast.message}</div>
                ${closeButton}
            </div>
        `;

        this.container.appendChild(toastElement);
        
        // Animação de entrada
        setTimeout(() => toastElement.classList.add('show'), 100);
    }

    hide(toastId) {
        const toastElement = document.getElementById(toastId);
        if (toastElement) {
            toastElement.classList.add('hide');
            setTimeout(() => {
                if (toastElement.parentNode) {
                    toastElement.parentNode.removeChild(toastElement);
                }
                this.toasts.delete(toastId);
            }, 300);
        }
    }

    getIcon(type) {
        const icons = {
            success: '<i class="fas fa-check-circle"></i>',
            error: '<i class="fas fa-exclamation-circle"></i>',
            warning: '<i class="fas fa-exclamation-triangle"></i>',
            info: '<i class="fas fa-info-circle"></i>'
        };
        return icons[type] || icons.info;
    }

    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .toast-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }

            .toast {
                min-width: 300px;
                max-width: 500px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                transform: translateX(100%);
                opacity: 0;
                transition: all 0.3s ease;
            }

            .toast.show {
                transform: translateX(0);
                opacity: 1;
            }

            .toast.hide {
                transform: translateX(100%);
                opacity: 0;
            }

            .toast-content {
                display: flex;
                align-items: center;
                padding: 16px;
                gap: 12px;
            }

            .toast-icon {
                font-size: 20px;
                flex-shrink: 0;
            }

            .toast-message {
                flex: 1;
                font-weight: 500;
            }

            .toast-close {
                background: none;
                border: none;
                font-size: 18px;
                cursor: pointer;
                color: #666;
                padding: 0;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .toast-success {
                border-left: 4px solid #10b981;
            }

            .toast-success .toast-icon {
                color: #10b981;
            }

            .toast-error {
                border-left: 4px solid #ef4444;
            }

            .toast-error .toast-icon {
                color: #ef4444;
            }

            .toast-warning {
                border-left: 4px solid #f59e0b;
            }

            .toast-warning .toast-icon {
                color: #f59e0b;
            }

            .toast-info {
                border-left: 4px solid #3b82f6;
            }

            .toast-info .toast-icon {
                color: #3b82f6;
            }

            /* Dark mode */
            [data-theme="dark"] .toast {
                background: var(--rm-card-bg, #2d3748);
                color: var(--rm-text-primary, #e2e8f0);
            }

            [data-theme="dark"] .toast-close {
                color: var(--rm-text-secondary, #a0aec0);
            }
        `;
        document.head.appendChild(style);
    }
}

// Instância global
window.toastManager = new ToastManager();
