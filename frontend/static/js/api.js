/**
 * SecurityCheck - API клиент
 * Функции для взаимодействия с backend API
 */

(function() {
    'use strict';

    const API_BASE = '/api';

    /**
     * Базовая функция для API запросов
     */
    async function apiRequest(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };

        const config = { ...defaultOptions, ...options };

        try {
            const response = await fetch(`${API_BASE}${endpoint}`, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Ошибка запроса');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    /**
     * Начать сканирование сайта
     */
    async function startWebScan(url) {
        return apiRequest('/web-scans/start', {
            method: 'POST',
            body: JSON.stringify({ url })
        });
    }

    /**
     * Получить результаты сканирования сайта
     */
    async function getWebScan(scanId) {
        return apiRequest(`/web-scans/${scanId}`);
    }

    /**
     * Получить статус сканирования
     */
    async function getScanStatus(scanId) {
        return apiRequest(`/web-scans/${scanId}/status`);
    }

    /**
     * Получить историю сканирований
     */
    async function getWebScanHistory(page = 1, limit = 20) {
        return apiRequest(`/web-scans/history?page=${page}&limit=${limit}`);
    }

    /**
     * Проверить ссылку
     */
    async function checkLink(url) {
        return apiRequest('/link-checks/check', {
            method: 'POST',
            body: JSON.stringify({ url })
        });
    }

    /**
     * Получить историю проверок ссылок
     */
    async function getLinkCheckHistory(page = 1, limit = 20) {
        return apiRequest(`/link-checks/history?page=${page}&limit=${limit}`);
    }

    /**
     * Загрузить файл на анализ
     */
    async function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        return fetch(`${API_BASE}/file-analysis/upload`, {
            method: 'POST',
            body: formData
        }).then(res => {
            if (!res.ok) {
                return res.json().then(data => {
                    throw new Error(data.error || 'Ошибка загрузки');
                });
            }
            return res.json();
        });
    }

    /**
     * Получить результаты анализа файла
     */
    async function getFileAnalysis(analysisId) {
        return apiRequest(`/file-analysis/${analysisId}`);
    }

    /**
     * Получить статус анализа файла
     */
    async function getFileAnalysisStatus(analysisId) {
        return apiRequest(`/file-analysis/${analysisId}/status`);
    }

    /**
     * Получить информацию о домене
     */
    async function lookupDomain(domain) {
        return apiRequest('/domain-intel/lookup', {
            method: 'POST',
            body: JSON.stringify({ domain })
        });
    }

    /**
     * Получить DNS записи домена
     */
    async function getDnsRecords(intelId) {
        return apiRequest(`/domain-intel/${intelId}/dns-records`);
    }

    /**
     * Получить текущую подписку
     */
    async function getCurrentSubscription() {
        return apiRequest('/subscription/current');
    }

    /**
     * Получить тарифные планы
     */
    async function getSubscriptionPlans() {
        return apiRequest('/subscription/plans');
    }

    /**
     * Улучшить подписку
     */
    async function upgradeSubscription(plan, billing = 'monthly') {
        return apiRequest('/subscription/upgrade', {
            method: 'POST',
            body: JSON.stringify({ plan, billing })
        });
    }

    /**
     * Отменить подписку
     */
    async function cancelSubscription() {
        return apiRequest('/subscription/cancel', {
            method: 'POST'
        });
    }

    /**
     * Получить статистику пользователя
     */
    async function getUserStats() {
        return apiRequest('/dashboard/stats');
    }

    /**
     * Получить последние сканирования
     */
    async function getRecentScans(limit = 10) {
        return apiRequest(`/dashboard/recent?limit=${limit}`);
    }

    /**
     * Получить историю всех проверок
     */
    async function getHistory(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return apiRequest(`/dashboard/history?${queryString}`);
    }

    /**
     * Polling для отслеживания статуса
     */
    function pollStatus(checkFunction, scanId, interval = 2000, maxAttempts = 60) {
        let attempts = 0;

        return new Promise((resolve, reject) => {
            const poll = async () => {
                try {
                    const result = await checkFunction(scanId);
                    
                    if (result.status === 'completed') {
                        resolve(result);
                    } else if (result.status === 'failed') {
                        reject(new Error(result.error || 'Сканирование не удалось'));
                    } else if (attempts >= maxAttempts) {
                        reject(new Error('Превышено время ожидания'));
                    } else {
                        attempts++;
                        setTimeout(poll, interval);
                    }
                } catch (error) {
                    reject(error);
                }
            };

            poll();
        });
    }

    /**
     * Экспорт API в глобальную область
     */
    window.SecurityCheckAPI = {
        // Web Scans
        startWebScan,
        getWebScan,
        getScanStatus,
        getWebScanHistory,
        
        // Link Checks
        checkLink,
        getLinkCheckHistory,
        
        // File Analysis
        uploadFile,
        getFileAnalysis,
        getFileAnalysisStatus,
        
        // Domain Intel
        lookupDomain,
        getDnsRecords,
        
        // Subscription
        getCurrentSubscription,
        getSubscriptionPlans,
        upgradeSubscription,
        cancelSubscription,
        
        // Dashboard
        getUserStats,
        getRecentScans,
        getHistory,
        
        // Utilities
        pollStatus
    };

})();
