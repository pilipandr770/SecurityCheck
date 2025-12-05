/**
 * SecurityCheck - Утилитарные функции
 * Вспомогательные функции для работы с UI
 */

(function() {
    'use strict';

    /**
     * Валидация URL
     */
    function isValidUrl(string) {
        try {
            const url = new URL(string);
            return url.protocol === 'http:' || url.protocol === 'https:';
        } catch (_) {
            // Попробовать добавить https://
            try {
                const url = new URL('https://' + string);
                return true;
            } catch (_) {
                return false;
            }
        }
    }

    /**
     * Нормализация URL (добавить https:// если нет)
     */
    function normalizeUrl(url) {
        url = url.trim();
        
        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            return 'https://' + url;
        }
        
        return url;
    }

    /**
     * Извлечь домен из URL
     */
    function extractDomain(url) {
        try {
            const urlObj = new URL(normalizeUrl(url));
            let domain = urlObj.hostname;
            
            // Убрать www.
            if (domain.startsWith('www.')) {
                domain = domain.substring(4);
            }
            
            return domain;
        } catch (error) {
            return url;
        }
    }

    /**
     * Получить класс badge для severity
     */
    function getSeverityBadgeClass(severity) {
        const mapping = {
            'critical': 'badge-danger',
            'high': 'badge-danger',
            'medium': 'badge-warning',
            'low': 'badge-info',
            'info': 'badge-secondary'
        };
        
        return mapping[severity] || 'badge-secondary';
    }

    /**
     * Получить класс badge для threat level
     */
    function getThreatLevelBadgeClass(threatLevel) {
        const mapping = {
            'danger': 'badge-danger',
            'warning': 'badge-warning',
            'safe': 'badge-success'
        };
        
        return mapping[threatLevel] || 'badge-secondary';
    }

    /**
     * Получить иконку для типа сканирования
     */
    function getScanTypeIcon(scanType) {
        const mapping = {
            'web_scan': 'fa-globe',
            'link_check': 'fa-link',
            'file_analysis': 'fa-file',
            'domain_intel': 'fa-search'
        };
        
        return mapping[scanType] || 'fa-question';
    }

    /**
     * Рассчитать буквенную оценку из числа
     */
    function calculateGrade(score) {
        if (score >= 90) return 'A';
        if (score >= 80) return 'B';
        if (score >= 70) return 'C';
        if (score >= 60) return 'D';
        return 'F';
    }

    /**
     * Получить класс для оценки
     */
    function getGradeClass(grade) {
        const mapping = {
            'A': 'grade-a',
            'B': 'grade-b',
            'C': 'grade-c',
            'D': 'grade-d',
            'F': 'grade-f'
        };
        
        return mapping[grade] || 'grade-f';
    }

    /**
     * Создать HTML для результата сканирования
     */
    function createScanResultHtml(result) {
        const severityClass = getSeverityBadgeClass(result.severity);
        const severityLabel = {
            'critical': 'КРИТИЧНО',
            'high': 'ВЫСОКАЯ',
            'medium': 'СРЕДНЯЯ',
            'low': 'НИЗКАЯ',
            'info': 'ИНФО'
        }[result.severity] || result.severity.toUpperCase();
        
        return `
            <div class="scan-result-item ${result.severity}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">
                            <span class="badge ${severityClass}">${severityLabel}</span>
                            ${escapeHtml(result.title)}
                        </h6>
                        ${result.description ? `<p class="mb-2 text-muted">${escapeHtml(result.description)}</p>` : ''}
                        ${result.evidence ? `
                            <div class="alert alert-secondary mb-2">
                                <strong>Доказательство:</strong> <code>${escapeHtml(result.evidence)}</code>
                            </div>
                        ` : ''}
                        ${result.ai_explanation ? `
                            <div class="alert alert-info mb-2">
                                <i class="fas fa-robot"></i> <strong>AI Объяснение:</strong> ${escapeHtml(result.ai_explanation)}
                            </div>
                        ` : ''}
                        ${result.ai_fix ? `
                            <div class="alert alert-success mb-0">
                                <i class="fas fa-wrench"></i> <strong>Как исправить:</strong> ${escapeHtml(result.ai_fix)}
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Показать прогресс бар
     */
    function showProgress(elementId, percent, label = '') {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        element.innerHTML = `
            <div class="progress">
                <div class="progress-bar" role="progressbar" 
                     style="width: ${percent}%" 
                     aria-valuenow="${percent}" 
                     aria-valuemin="0" 
                     aria-valuemax="100">
                    ${label || percent + '%'}
                </div>
            </div>
        `;
    }

    /**
     * Показать индикатор загрузки
     */
    function showLoading(elementId, message = 'Загрузка...') {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        element.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Загрузка...</span>
                </div>
                <p class="text-muted">${message}</p>
            </div>
        `;
    }

    /**
     * Показать сообщение об ошибке
     */
    function showError(elementId, message) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        element.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Ошибка:</strong> ${message}
            </div>
        `;
    }

    /**
     * Показать пустое состояние
     */
    function showEmptyState(elementId, title, description, iconClass = 'fa-inbox') {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        element.innerHTML = `
            <div class="text-center py-5">
                <i class="fas ${iconClass} fa-3x text-muted mb-3"></i>
                <h5>${title}</h5>
                <p class="text-muted">${description}</p>
            </div>
        `;
    }

    /**
     * Относительное время ("2 часа назад")
     */
    function timeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);
        
        if (seconds < 60) {
            return 'только что';
        }
        
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) {
            return `${minutes} ${pluralize(minutes, 'минуту', 'минуты', 'минут')} назад`;
        }
        
        const hours = Math.floor(minutes / 60);
        if (hours < 24) {
            return `${hours} ${pluralize(hours, 'час', 'часа', 'часов')} назад`;
        }
        
        const days = Math.floor(hours / 24);
        if (days < 7) {
            return `${days} ${pluralize(days, 'день', 'дня', 'дней')} назад`;
        }
        
        // Иначе показать дату
        return date.toLocaleDateString('ru-RU');
    }

    /**
     * Правильное склонение для чисел
     */
    function pluralize(number, one, two, five) {
        let n = Math.abs(number);
        n %= 100;
        
        if (n >= 5 && n <= 20) {
            return five;
        }
        
        n %= 10;
        if (n === 1) {
            return one;
        }
        if (n >= 2 && n <= 4) {
            return two;
        }
        
        return five;
    }

    /**
     * Безопасное экранирование HTML
     */
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    /**
     * Truncate text
     */
    function truncate(text, length = 100) {
        if (text.length <= length) {
            return text;
        }
        
        return text.substring(0, length) + '...';
    }

    /**
     * Экспорт функций в глобальную область
     */
    window.SecurityCheckUtils = {
        isValidUrl,
        normalizeUrl,
        extractDomain,
        getSeverityBadgeClass,
        getThreatLevelBadgeClass,
        getScanTypeIcon,
        calculateGrade,
        getSecurityGrade: calculateGrade, // Алиас для обратной совместимости
        getGradeClass,
        createScanResultHtml,
        showProgress,
        showLoading,
        showError,
        showEmptyState,
        timeAgo,
        pluralize,
        escapeHtml,
        truncate
    };

})();
