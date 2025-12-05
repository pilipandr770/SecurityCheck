/**
 * SecurityCheck - Основной JavaScript
 * Общие функции и утилиты
 */

(function() {
    'use strict';

    // Инициализация при загрузке страницы
    document.addEventListener('DOMContentLoaded', function() {
        initTooltips();
        initPopovers();
        initAlerts();
        initFormValidation();
        initCopyButtons();
    });

    /**
     * Инициализация Bootstrap tooltips
     */
    function initTooltips() {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        [...tooltipTriggerList].map(el => new bootstrap.Tooltip(el));
    }

    /**
     * Инициализация Bootstrap popovers
     */
    function initPopovers() {
        const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
        [...popoverTriggerList].map(el => new bootstrap.Popover(el));
    }

    /**
     * Автоматическое скрытие алертов через 5 секунд
     */
    function initAlerts() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        
        alerts.forEach(alert => {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        });
    }

    /**
     * Валидация форм Bootstrap
     */
    function initFormValidation() {
        const forms = document.querySelectorAll('.needs-validation');
        
        Array.from(forms).forEach(form => {
            form.addEventListener('submit', event => {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                
                form.classList.add('was-validated');
            }, false);
        });
    }

    /**
     * Кнопки копирования в буфер
     */
    function initCopyButtons() {
        const copyButtons = document.querySelectorAll('[data-copy]');
        
        copyButtons.forEach(button => {
            button.addEventListener('click', function() {
                const text = this.getAttribute('data-copy');
                copyToClipboard(text);
                
                // Показать уведомление
                showNotification('Скопировано в буфер обмена', 'success');
                
                // Изменить иконку
                const icon = this.querySelector('i');
                if (icon) {
                    icon.classList.remove('fa-copy');
                    icon.classList.add('fa-check');
                    
                    setTimeout(() => {
                        icon.classList.remove('fa-check');
                        icon.classList.add('fa-copy');
                    }, 2000);
                }
            });
        });
    }

    /**
     * Копирование текста в буфер обмена
     */
    function copyToClipboard(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text);
        } else {
            // Fallback для старых браузеров
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
        }
    }

    /**
     * Показать уведомление (toast)
     */
    function showNotification(message, type = 'info') {
        const toast = createToast(message, type);
        document.body.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Удалить после скрытия
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    /**
     * Создать элемент toast
     */
    function createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        toast.style.position = 'fixed';
        toast.style.top = '20px';
        toast.style.right = '20px';
        toast.style.zIndex = '9999';
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        return toast;
    }

    /**
     * Показать индикатор загрузки в кнопке
     */
    function showButtonLoading(button, loadingText = 'Загрузка...') {
        button.disabled = true;
        button.dataset.originalHtml = button.innerHTML;
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            ${loadingText}
        `;
    }

    /**
     * Скрыть индикатор загрузки в кнопке
     */
    function hideButtonLoading(button) {
        button.disabled = false;
        if (button.dataset.originalHtml) {
            button.innerHTML = button.dataset.originalHtml;
            delete button.dataset.originalHtml;
        }
    }

    /**
     * Форматирование даты
     */
    function formatDate(dateString) {
        const date = new Date(dateString);
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        
        return `${day}.${month}.${year} ${hours}:${minutes}`;
    }

    /**
     * Форматирование размера файла
     */
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Debounce функция
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Экспорт функций в глобальную область
     */
    window.SecurityCheck = {
        showNotification,
        showButtonLoading,
        hideButtonLoading,
        formatDate,
        formatFileSize,
        debounce,
        copyToClipboard
    };

})();
