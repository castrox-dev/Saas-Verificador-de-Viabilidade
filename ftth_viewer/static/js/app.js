// Sistema de logging otimizado
(function(){
    const SILENCE_LOGS = true; // Reativado para debug do dark mode
    const LOG_LEVELS = {
        ERROR: 0,
        WARN: 1,
        INFO: 2,
        DEBUG: 3
    };
    
    let currentLogLevel = LOG_LEVELS.INFO;
    
    // Função para filtrar logs repetitivos
    const logFilter = (() => {
        const logCounts = new Map();
        const maxRepeats = 5; // Máximo de logs repetidos
        
        return (message, level) => {
            const key = `${level}:${message}`;
            const count = logCounts.get(key) || 0;
            
            if (count >= maxRepeats) {
                return false; // Não mostrar mais este log
            }
            
            logCounts.set(key, count + 1);
            return true;
        };
    })();
    
    if (SILENCE_LOGS) {
        console.log = function(){};
        console.info = function(){};
        console.debug = function(){};
        console.warn = function(){};
    } else {
        // Interceptar console.warn para filtrar logs repetitivos
        const originalWarn = console.warn;
        console.warn = function(...args) {
            const message = args.join(' ');
            if (logFilter(message, 'WARN')) {
                originalWarn.apply(console, args);
            }
        };
    }
    const originalError = console.error;
    console.error = function(){
        try {
            // Filtrar erros irrelevantes do DOM/Leaflet
            const errorString = Array.from(arguments).join(' ');
            const irrelevantErrors = [
                'Cannot read properties of undefined',
                'addEventParent',
                'reading \'addEventParent\'',
                'Leaflet internal error',
                'ResizeObserver loop limit exceeded'
            ];
            
            // Se o erro contém alguma das strings irrelevantes, não mostrar
            if (irrelevantErrors.some(pattern => errorString.includes(pattern))) {
                return;
            }
            
            const sanitized = Array.from(arguments).map(a => {
                if (a instanceof Error) return a.message || 'Erro';
                if (typeof a === 'string') {
                    return a.replace(/(api[_-]?key|token|secret|senha)=([^&\s]+)/ig, '$1=***');
                }
                return a;
            });
            originalError.apply(console, sanitized);
        } catch (e) {
            // Silenciar completamente erros no tratamento de erro
        }
    };
})();

// Base de API dinâmica: /<company_slug>/verificador/api ou fallback /verificador/api
const API_BASE = (() => {
    try {
        const parts = window.location.pathname.split('/').filter(Boolean);
        const first = parts[0] || '';
        if (first === 'verificador') {
            return '/verificador/api';
        }
        const isCompany = first && first !== 'rm' && first !== 'admin';
        return isCompany ? `/${first}/verificador/api` : '/verificador/api';
    } catch (_e) {
        return '/verificador/api';
    }
})();

// ===== DARK MODE FUNCTIONALITY =====
function initializeThemeToggle() {
    // Aguardar o DOM estar completamente carregado
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeThemeToggle);
        return;
    }
    
    // Logs temporários para debug do tema (não afetados pelo SILENCE_LOGS)
    const originalLog = console.log;
    const originalError = console.error;
    
    originalLog('🔧 Inicializando tema...');
    
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    
    if (!themeToggleBtn) {
        originalError('❌ Botão de tema não encontrado!');
        return;
    }
    
    originalLog('✅ Botão de tema encontrado:', themeToggleBtn);
    
    const themeIcon = themeToggleBtn.querySelector('i');
    
    if (!themeIcon) {
        originalError('❌ Ícone do tema não encontrado!');
        return;
    }
    
    originalLog('✅ Ícone do tema encontrado:', themeIcon);
    
    // Função para aplicar tema
    function setTheme(theme) {
        originalLog(`🎨 Aplicando tema: ${theme}`);
        
        // Aplicar tema ao documento
        document.documentElement.setAttribute('data-theme', theme);
        document.body.setAttribute('data-theme', theme);
        
        // Atualizar controles do Leaflet quando o tema mudar
        setTimeout(() => {
            const zoomControls = document.querySelectorAll('.leaflet-control-zoom a');
            const northControl = document.querySelector('.leaflet-control-north .north-arrow');
            
            if (theme === 'dark') {
                // Aplicar estilos escuros aos controles
                zoomControls.forEach(control => {
                    control.style.backgroundColor = '#2d2d2d';
                    control.style.borderColor = '#404040';
                    control.style.color = '#e5e7eb';
                });
                
                if (northControl) {
                    northControl.style.backgroundColor = '#2d2d2d';
                    northControl.style.borderColor = '#404040';
                    northControl.style.color = '#e5e7eb';
                }
            } else {
                // Aplicar estilos claros aos controles
                zoomControls.forEach(control => {
                    control.style.backgroundColor = 'white';
                    control.style.borderColor = '#e5e7eb';
                    control.style.color = '#374151';
                });
                
                if (northControl) {
                    northControl.style.backgroundColor = 'white';
                    northControl.style.borderColor = '#e5e7eb';
                    northControl.style.color = '#374151';
                }
            }
        }, 100);
        
        // Salvar no localStorage
        localStorage.setItem('theme', theme);
        
        // FORÇAR ESTILOS VISUAIS DIRETAMENTE PARA TESTE
        if (theme === 'dark') {
            document.body.style.backgroundColor = '#1a1a1a';
            document.body.style.color = '#ffffff';
            document.documentElement.style.backgroundColor = '#1a1a1a';
            document.documentElement.style.color = '#ffffff';
            
            // Aplicar estilos aos elementos principais
            const topBar = document.querySelector('.top-bar');
            if (topBar) {
                topBar.style.backgroundColor = '#1a1a1a';
                topBar.style.color = '#ffffff';
            }
            
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) {
                sidebar.style.backgroundColor = '#2d2d2d';
                sidebar.style.color = '#ffffff';
            }
            
            originalLog('🌙 Estilos escuros aplicados diretamente');
        } else {
            document.body.style.backgroundColor = '#ffffff';
            document.body.style.color = '#1a1a1a';
            document.documentElement.style.backgroundColor = '#ffffff';
            document.documentElement.style.color = '#1a1a1a';
            
            // Aplicar estilos aos elementos principais
            const topBar = document.querySelector('.top-bar');
            if (topBar) {
                topBar.style.backgroundColor = '#ffffff';
                topBar.style.color = '#1a1a1a';
            }
            
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) {
                sidebar.style.backgroundColor = '#f8f9fa';
                sidebar.style.color = '#1a1a1a';
            }
            
            originalLog('☀️ Estilos claros aplicados diretamente');
        }
        
        // Atualizar ícone
        if (theme === 'dark') {
            themeIcon.className = 'fas fa-sun';
            themeToggleBtn.title = 'Alternar para tema claro';
            originalLog('🌙 Ícone alterado para sol (modo escuro ativo)');
        } else {
            themeIcon.className = 'fas fa-moon';
            themeToggleBtn.title = 'Alternar para tema escuro';
            originalLog('☀️ Ícone alterado para lua (modo claro ativo)');
        }
        
        // Verificar se o tema foi aplicado
        const appliedTheme = document.documentElement.getAttribute('data-theme');
        originalLog(`✅ Tema aplicado: ${theme} (verificado: ${appliedTheme})`);
    }
    
    // Carregar tema salvo ou usar padrão (light)
    const savedTheme = localStorage.getItem('theme') || 'light';
    originalLog('📱 Tema salvo:', savedTheme);
    setTheme(savedTheme);
    
    // Event listener para o botão
    themeToggleBtn.addEventListener('click', () => {
        originalLog('🖱️ Botão de tema clicado!');
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        originalLog(`🔄 Alterando tema de ${currentTheme} para ${newTheme}`);
        setTheme(newTheme);
        originalLog(`✅ Tema alterado para: ${newTheme}`);
    });
    
    originalLog('🎉 Inicialização do tema concluída!');
}

// Função global para testar o dark mode
window.testDarkMode = function() {
    const originalLog = console.log;
    originalLog('🧪 Testando dark mode...');
    
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    originalLog('Tema atual:', currentTheme);
    
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    originalLog('Alterando para:', newTheme);
    
    document.documentElement.setAttribute('data-theme', newTheme);
    document.body.setAttribute('data-theme', newTheme);
    
    // Teste visual
    document.body.style.backgroundColor = newTheme === 'dark' ? '#1a1a1a' : '#ffffff';
    document.body.style.color = newTheme === 'dark' ? '#ffffff' : '#1a1a1a';
    
    originalLog('✅ Teste concluído! Tema:', newTheme);
    
    return newTheme;
};

// Função de diagnóstico completo do dark mode
window.diagnoseDarkMode = function() {
    const originalLog = console.log;
    originalLog('🔍 === DIAGNÓSTICO COMPLETO DO DARK MODE ===');
    
    // 1. Verificar elementos HTML
    const themeBtn = document.getElementById('theme-toggle-btn');
    const themeIcon = themeBtn ? themeBtn.querySelector('i') : null;
    
    originalLog('1. Elementos HTML:');
    originalLog('   - Botão encontrado:', !!themeBtn);
    originalLog('   - Ícone encontrado:', !!themeIcon);
    
    if (themeBtn) {
        originalLog('   - Botão classes:', themeBtn.className);
        originalLog('   - Botão title:', themeBtn.title);
    }
    
    if (themeIcon) {
        originalLog('   - Ícone classes:', themeIcon.className);
    }
    
    // 2. Verificar atributos de tema
    const htmlTheme = document.documentElement.getAttribute('data-theme');
    const bodyTheme = document.body.getAttribute('data-theme');
    
    originalLog('2. Atributos de tema:');
    originalLog('   - HTML data-theme:', htmlTheme);
    originalLog('   - Body data-theme:', bodyTheme);
    
    // 3. Verificar localStorage
    const savedTheme = localStorage.getItem('theme');
    originalLog('3. LocalStorage:');
    originalLog('   - Tema salvo:', savedTheme);
    
    // 4. Verificar estilos CSS
    const computedStyle = window.getComputedStyle(document.body);
    originalLog('4. Estilos aplicados:');
    originalLog('   - Background:', computedStyle.backgroundColor);
    originalLog('   - Color:', computedStyle.color);
    
    // 5. Verificar variáveis CSS
    const rootStyle = window.getComputedStyle(document.documentElement);
    originalLog('5. Variáveis CSS:');
    originalLog('   - --bg-primary:', rootStyle.getPropertyValue('--bg-primary'));
    originalLog('   - --text-primary:', rootStyle.getPropertyValue('--text-primary'));
    originalLog('   - --dark-bg-primary:', rootStyle.getPropertyValue('--dark-bg-primary'));
    originalLog('   - --dark-text-primary:', rootStyle.getPropertyValue('--dark-text-primary'));
    
    // 6. Testar funcionalidade
    originalLog('6. Testando funcionalidade...');
    if (themeBtn) {
        originalLog('   - Simulando clique...');
        themeBtn.click();
        
        setTimeout(() => {
            const newTheme = document.documentElement.getAttribute('data-theme');
            originalLog('   - Tema após clique:', newTheme);
            originalLog('🔍 === FIM DO DIAGNÓSTICO ===');
        }, 100);
    } else {
        originalLog('   - Botão não encontrado, não é possível testar');
        originalLog('🔍 === FIM DO DIAGNÓSTICO ===');
    }
};

// Elementos da barra de pesquisa principal - serão inicializados quando o DOM estiver pronto
let searchInput, searchBtn, clearSearchBtn, searchResults;

// Variável para controlar debounce da busca
let searchTimeout;
// Camada com todos os CTOs atualmente desenhados
let currentLayer = null;
// Variável para controlar o modo de clique/navegação
let isClickMode = false;

// Cache inteligente com múltiplas camadas
const smartCache = (() => {
    const stores = {
        search: new Map(),
        coordinates: new Map(),
        viability: new Map(),
        routes: new Map()
    };
    
    const meta = {
        search: new Map(),
        coordinates: new Map(),
        viability: new Map(),
        routes: new Map()
    };
    
    const TTL = {
        search: 10 * 60 * 1000,      // 10 minutos
        coordinates: 60 * 60 * 1000, // 1 hora
        viability: 30 * 60 * 1000,   // 30 minutos
        routes: 2 * 60 * 60 * 1000   // 2 horas
    };
    
    return {
        get(type, key) {
            const store = stores[type];
            const metaStore = meta[type];
            const ts = metaStore.get(key);
            
            if (!ts) return null;
            if (Date.now() - ts > TTL[type]) {
                store.delete(key);
                metaStore.delete(key);
                return null;
            }
            return store.get(key) || null;
        },
        
        set(type, key, value) {
            stores[type].set(key, Array.isArray(value) ? value.slice() : value);
            meta[type].set(key, Date.now());
        },
        
        cleanExpired() {
            const now = Date.now();
            Object.keys(stores).forEach(type => {
                const store = stores[type];
                const metaStore = meta[type];
                
                for (const [key, ts] of metaStore.entries()) {
                    if (now - ts > TTL[type]) {
                        store.delete(key);
                        metaStore.delete(key);
                    }
                }
            });
        },
        
        size(type) { 
            return type ? stores[type].size : Object.values(stores).reduce((sum, store) => sum + store.size, 0);
        },
        
        clear(type) {
            if (type) {
                stores[type].clear();
                meta[type].clear();
            } else {
                Object.values(stores).forEach(store => store.clear());
                Object.values(meta).forEach(metaStore => metaStore.clear());
            }
        }
    };
})();

// Cache simples para compatibilidade (deprecated)
const searchCache = smartCache;

// Sistema de monitoramento de performance
const performanceMonitor = (() => {
    const metrics = {
        loadTimes: [],
        cacheHits: 0,
        cacheMisses: 0,
        apiCalls: 0,
        errors: 0
    };
    
    return {
        startTimer(label) {
            return performance.now();
        },
        
        endTimer(startTime, label) {
            const duration = performance.now() - startTime;
            metrics.loadTimes.push({ label, duration, timestamp: Date.now() });
            
            // Manter apenas os últimos 100 tempos
            if (metrics.loadTimes.length > 100) {
                metrics.loadTimes = metrics.loadTimes.slice(-100);
            }
            
            return duration;
        },
        
        recordCacheHit() {
            metrics.cacheHits++;
        },
        
        recordCacheMiss() {
            metrics.cacheMisses++;
        },
        
        recordApiCall() {
            metrics.apiCalls++;
        },
        
        recordError() {
            metrics.errors++;
        },
        
        getStats() {
            const avgLoadTime = metrics.loadTimes.length > 0 
                ? metrics.loadTimes.reduce((sum, item) => sum + item.duration, 0) / metrics.loadTimes.length 
                : 0;
            
            const cacheHitRate = metrics.cacheHits + metrics.cacheMisses > 0 
                ? (metrics.cacheHits / (metrics.cacheHits + metrics.cacheMisses) * 100).toFixed(1)
                : 0;
            
            return {
                avgLoadTime: avgLoadTime.toFixed(2),
                cacheHitRate: `${cacheHitRate}%`,
                apiCalls: metrics.apiCalls,
                errors: metrics.errors,
                totalRequests: metrics.cacheHits + metrics.cacheMisses
            };
        },
        
        showIndicator() {
            const stats = this.getStats();
            const indicator = document.createElement('div');
            indicator.className = 'performance-indicator show';
            indicator.innerHTML = `
                <div>⚡ ${stats.avgLoadTime}ms</div>
                <div>📦 ${stats.cacheHitRate}</div>
                <div>🌐 ${stats.apiCalls}</div>
                <div>❌ ${stats.errors}</div>
            `;
            
            document.body.appendChild(indicator);
            
            setTimeout(() => {
                indicator.classList.remove('show');
                setTimeout(() => indicator.remove(), 300);
            }, 2000);
        }
    };
})();

function cleanExpiredCache() {
    try {
        searchCache.cleanExpired();
    } catch (e) {
        console.warn('cleanExpiredCache falhou:', e);
    }
}

// Inicialização do mapa Leaflet (Maricá e limites do Brasil)
const brazilBounds = L.latLngBounds(
    L.latLng(-34.0, -74.0),  // sudoeste aproximado
    L.latLng(5.5, -34.0)     // nordeste aproximado
);

const map = L.map('map', {
    zoomControl: false,
    preferCanvas: true,
    maxBounds: brazilBounds,
    maxBoundsViscosity: 1.0
});

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    minZoom: 5,
    noWrap: true,
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Adicionar controle de zoom no canto inferior esquerdo
L.control.zoom({ position: 'bottomleft' }).addTo(map);

// Adicionar controle de direção norte (bússola)
const northControl = L.Control.extend({
    onAdd: function(map) {
        const container = L.DomUtil.create('div', 'leaflet-control leaflet-control-north');
        container.innerHTML = '<div class="north-arrow">N</div>';
        container.style.cssText = `
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 16px;
            color: #374151;
            cursor: pointer;
            transition: all 0.2s ease;
        `;
        
        container.addEventListener('mouseenter', function() {
            this.style.background = '#ff6600';
            this.style.color = 'white';
            this.style.transform = 'scale(1.05)';
        });
        
        container.addEventListener('mouseleave', function() {
            this.style.background = 'white';
            this.style.color = '#374151';
            this.style.transform = 'scale(1)';
        });
        
        container.addEventListener('click', function() {
            // Resetar zoom e centralizar para norte
            map.setView(map.getCenter(), map.getZoom());
        });
        
        return container;
    }
});

new northControl({ position: 'bottomright' }).addTo(map);

// Vista inicial em Maricá, RJ
map.setView([-22.919, -42.818], 12);

// Tornar acessível globalmente
window.map = map;

// Helpers: CEP validation, CEP search via ViaCEP, and notifications
function extractCEP(query) {
    const digits = (query || '').replace(/\D/g, '');
    return /^\d{8}$/.test(digits) ? digits : null;
}

function isValidCEP(query) {
    return extractCEP(query) !== null;
}

async function searchByCEP(query) {
    const cep = extractCEP(query);
    if (!cep) return [];
    // Tenta ViaCEP primeiro, depois BrasilAPI como fallback
    let info = null;
    try {
        const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
        const data = await response.json();
        if (!data || data.erro) throw new Error('ViaCEP retornou erro');
        info = {
            street: data.logradouro || '',
            neighborhood: data.bairro || '',
            city: data.localidade || '',
            state: data.uf || '',
            raw: data
        };
    } catch (e) {
        console.warn('ViaCEP falhou, tentando BrasilAPI...', e);
        try {
            // Preferir v2; se falhar, tentar v1
            let data = null;
            try {
                const r2 = await fetch(`https://brasilapi.com.br/api/cep/v2/${cep}`);
                data = await r2.json();
                if (data && (data.message || data.errors)) throw new Error(data.message || 'BrasilAPI v2 erro');
            } catch (errV2) {
                console.warn('BrasilAPI v2 falhou, tentando v1...', errV2);
                const r1 = await fetch(`https://brasilapi.com.br/api/cep/v1/${cep}`);
                data = await r1.json();
            }
            if (!data || data.errors) throw new Error('BrasilAPI sem resultado');
            info = {
                street: data.street || '',
                neighborhood: data.neighborhood || '',
                city: data.city || '',
                state: data.state || '',
                raw: data
            };
        } catch (e2) {
            console.warn('Erro ao consultar BrasilAPI:', e2);
            return [];
        }
    }

    const addressStr = [
        info.street,
        info.neighborhood,
        `${info.city}${info.state ? ' - ' + info.state : ''}`,
        'Brasil'
    ].filter(Boolean).join(', ');

    return [{
        display_name: addressStr || `${cep}, Brasil`,
        type: 'CEP',
        importance: 1.0,
        address: info.raw,
        cepNormalized: cep,
        searchCity: info.city,
        searchState: info.state
    }];
}

function showNotification(message, type = 'info') {
    try {
        console.log(`[${type}] ${message}`);
        let container = document.getElementById('app-notifications');
        if (!container) {
            container = document.createElement('div');
            container.id = 'app-notifications';
            container.style.position = 'fixed';
            container.style.top = '80px';
            container.style.right = '20px';
            container.style.zIndex = '2000';
            container.style.display = 'flex';
            container.style.flexDirection = 'column';
            container.style.gap = '8px';
            document.body.appendChild(container);
        }
        const el = document.createElement('div');
        el.textContent = message;
        el.style.padding = '10px 14px';
        el.style.borderRadius = '6px';
        el.style.boxShadow = '0 3px 10px rgba(0,0,0,0.15)';
        el.style.fontSize = '14px';
        el.style.color = '#fff';
        el.style.background = type === 'success' ? '#2ecc71' : (type === 'error' ? '#e74c3c' : '#1976d2');
        container.appendChild(el);
        setTimeout(() => {
            el.style.opacity = '0';
            el.style.transition = 'opacity 300ms ease';
            setTimeout(() => el.remove(), 300);
        }, 3000);
    } catch (e) {
        console.log('Notification:', message);
    }
}

// Parse coordinates from query, supports "lat, lon" or "lat lon"
function parseCoordinatesFromQuery(query) {
    const q = (query || '').trim();
    if (!q) return null;

    // 1) Tenta DMS com letras de hemisfério (ex.: 22°54'59.5"S 42°48'35.2"W)
    const dmsTokens = [];
    const dmsRegex = /(-?\d+(?:\.\d+)?)\s*[°º]?\s*(\d{1,2})?\s*['′’]?\s*(\d+(?:\.\d+)?)?\s*["″”]?\s*([NnSsEeWwOo])/g;
    let m;
    while ((m = dmsRegex.exec(q)) !== null) {
        const deg = parseFloat(m[1]);
        const min = m[2] ? parseFloat(m[2]) : 0;
        const sec = m[3] ? parseFloat(m[3]) : 0;
        let hemi = m[4].toUpperCase();
        // Português: 'O' (Oeste) equivale a 'W'
        if (hemi === 'O') hemi = 'W';
        const dec = Math.abs(deg) + (min / 60) + (sec / 3600);
        const signed = (hemi === 'S' || hemi === 'W') ? -dec : dec;
        dmsTokens.push({ value: signed, hemi });
    }
    if (dmsTokens.length >= 2) {
        // Prefere NS para latitude e EW para longitude
        const latToken = dmsTokens.find(t => t.hemi === 'N' || t.hemi === 'S') || dmsTokens[0];
        const lonToken = dmsTokens.find(t => t.hemi === 'E' || t.hemi === 'W') || dmsTokens[1];
        const lat = latToken?.value;
        const lon = lonToken?.value;
        if (isFinite(lat) && isFinite(lon) && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
            return { lat, lon };
        }
    }

    // 2) Fallback: decimal "lat, lon" ou "lat lon"
    const normalized = q.replace(/[,;]/g, ' ').trim();
    const matches = normalized.match(/[-+]?\d*\.?\d+/g);
    if (!matches || matches.length < 2) return null;
    const lat = parseFloat(matches[0]);
    const lon = parseFloat(matches[1]);
    if (!isFinite(lat) || !isFinite(lon)) return null;
    if (lat < -90 || lat > 90 || lon < -180 || lon > 180) return null;
    return { lat, lon };
}

// Função searchAddress removida - pertencia ao primeiro método de pesquisa

// Função displaySearchResults removida - pertencia ao primeiro método de pesquisa

// Funções de pesquisa removidas - pertenciam ao primeiro método de pesquisa

// Esconder dropdown quando clicar fora
document.addEventListener('click', (e) => {
    const searchContainer = document.querySelector('.top-search-container');
    if (searchResults && searchContainer && !searchContainer.contains(e.target)) {
        searchResults.classList.remove('show');
    }
});

// Função para resumir endereço
function resumirEndereco(endereco) {
    // Verificar se endereco é válido
    if (!endereco || typeof endereco !== 'string') {
        return endereco || '';
    }
    
    // Pegar apenas a primeira parte (rua/avenida) e cidade
    const partes = endereco.split(',');
    if (partes.length >= 2) {
        const rua = partes[0].trim();
        const cidade = partes[1].trim();
        return `${rua}, ${cidade}`;
    }
    return endereco.length > 50 ? endereco.substring(0, 50) + '...' : endereco;
}

// Função util para normalizar número do CTO (remove prefixos e mantém dígitos com . ou -)
function formatCtoNumber(name) {
    if (!name) return 'Desconhecido';
    const str = String(name).trim();
    // Captura sequências como 16, 16.01, 12-3, etc.
    const match = str.match(/\d+(?:[.\-]\d+)*/);
    if (match) return match[0];
    // Fallback: remove tudo que não for dígito, ponto ou hífen
    const cleaned = str.replace(/[^0-9.\-]/g, '').replace(/^[-.]+|[-.]+$/g, '').trim();
    return cleaned || str;
}

// Funções da barra de pesquisa principal
function initializeMainSearch() {
    // Aguardar um pouco para garantir que o DOM esteja pronto
    setTimeout(() => {
        // Inicializar elementos do DOM
        searchInput = document.getElementById('search-input');
        searchBtn = document.getElementById('search-btn');
        clearSearchBtn = document.getElementById('clear-search'); // Opcional
        searchResults = document.getElementById('search-results');
        
        if (!searchInput || !searchBtn || !searchResults) {
            console.error('Elementos da barra de pesquisa não encontrados!');
            console.log('Elementos encontrados:', {
                searchInput: !!searchInput,
                searchBtn: !!searchBtn,
                clearSearchBtn: !!clearSearchBtn,
                searchResults: !!searchResults
            });
            return;
        }

    // Event listeners
    searchBtn.addEventListener('click', () => {
        performSearch().catch(error => {
            console.error('Erro na pesquisa:', error);
            showNotification('Erro ao realizar pesquisa', 'error');
        });
    });
    
    // Adicionar event listener apenas se o botão existir
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', clearSearch);
    }
    
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch().catch(error => {
                console.error('Erro na pesquisa:', error);
                showNotification('Erro ao realizar pesquisa', 'error');
            });
        }
    });

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        if (query.length === 0) {
            if (clearSearchBtn) {
                clearSearchBtn.style.display = 'none';
            }
            hideSearchResults();
        } else {
            if (clearSearchBtn) {
                clearSearchBtn.style.display = 'block';
            }
        }
    });

    // Fechar resultados ao clicar fora
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-container')) {
            hideSearchResults();
        }
    });
    
    console.log('✅ Barra de pesquisa inicializada com sucesso!');
    }, 100); // Aguardar 100ms para garantir que o DOM esteja pronto
}

async function performSearch() {
    const query = searchInput.value.trim();
    if (!query) return;

    showSearchLoading();

    try {
        // Verificar se é coordenada
        const coords = parseCoordinatesFromQuery(query);
        if (coords) {
            await processSearchResultWithConfirmation(coords.lat, coords.lng, `Coordenadas: ${coords.lat}, ${coords.lng}`);
            hideSearchResults();
            return;
        }

        // Método unificado: buscar por CEP ou endereço
        await searchUnified(query);

    } catch (error) {
        console.error('Erro na pesquisa:', error);
        showNotification('Erro ao realizar pesquisa', 'error');
    } finally {
        hideSearchLoading();
    }
}

// Método unificado de pesquisa que funciona para CEP e endereços
async function searchUnified(query) {
    let searchQuery = query;
    let addressText = query;

    // Se for CEP, buscar informações do endereço primeiro
    if (isValidCEP(query)) {
        try {
            const cepResults = await searchByCEP(query);
            if (cepResults && cepResults.length > 0) {
                const cepData = cepResults[0];
                searchQuery = cepData.display_name;
                addressText = `${cepData.display_name} - CEP: ${query}`;
            }
        } catch (error) {
            console.warn('Erro ao buscar CEP, tentando busca direta:', error);
        }
    }

    // Buscar coordenadas usando Nominatim
    try {
        const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&countrycodes=br&limit=1`);
        const results = await response.json();

        if (results && results.length > 0) {
            const result = results[0];
            await processSearchResultWithConfirmation(parseFloat(result.lat), parseFloat(result.lon), addressText);
            hideSearchResults();
        } else {
            // Endereço não encontrado - marcar no centro do mapa atual e mostrar popup de confirmação
            const center = map.getCenter();
            await markLocationWithConfirmation(center.lat, center.lng, `Endereço não encontrado: ${query}`);
            hideSearchResults();
        }
    } catch (error) {
        console.error('Erro na busca:', error);
        showNotification('Erro ao buscar localização', 'error');
        hideSearchResults();
    }
}

// Função auxiliar para processar resultado da pesquisa com confirmação
async function processSearchResultWithConfirmation(lat, lng, addressText) {
    await markLocationWithConfirmation(lat, lng, addressText);
}

// Função para marcar localização e mostrar popup de confirmação
async function markLocationWithConfirmation(lat, lng, addressText) {
    map.setView([lat, lng], 16);
    
    // Remover marcador anterior se existir
    if (window.searchMarker && map.hasLayer(window.searchMarker)) {
        map.removeLayer(window.searchMarker);
    }
    
    // Criar ícone do marcador de pesquisa
    const searchIcon = L.divIcon({
        className: 'search-marker',
        html: '<div style="background-color: #ff4444; width: 16px; height: 16px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 10px rgba(255,68,68,0.8); position: relative;"><div style="position: absolute; top: -2px; left: -2px; width: 20px; height: 20px; border-radius: 50%; background-color: rgba(255,68,68,0.4); animation: pulse 1s infinite;"></div></div>',
        iconSize: [22, 22],
        iconAnchor: [11, 11]
    });
    
    // Adicionar marcador
    window.searchMarker = L.marker([lat, lng], { icon: searchIcon }).addTo(map);
    
    // Popup de confirmação
    const confirmPopup = `
        <div class="viability-popup">
            <h4 class="viability-popup-title">Verificar Viabilidade?</h4>
            <div class="popup-actions">
                <button class="confirm-verify-btn">Sim</button>
                <button class="cancel-verify-btn">Não</button>
            </div>
        </div>`;
    
    window.searchMarker.bindPopup(confirmPopup).openPopup();
    
    // Conectar botões do popup quando renderizado
    const connectPopupButtons = () => {
        const popupNode = document.querySelector('.leaflet-popup-content');
        if (!popupNode) {
            // Tentar novamente após um pequeno delay
            setTimeout(connectPopupButtons, 50);
            return;
        }
        
        const confirmBtn = popupNode.querySelector('.confirm-verify-btn');
        const cancelBtn = popupNode.querySelector('.cancel-verify-btn');
        
        if (confirmBtn && !confirmBtn.hasAttribute('data-connected')) {
            confirmBtn.setAttribute('data-connected', 'true');
            confirmBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Botão Sim clicado');
                
                if (window.searchMarker && typeof window.searchMarker.setPopupContent === 'function') {
                    window.searchMarker.setPopupContent('<div class="loading-popup">Verificando viabilidade...</div>');
                }
                verificarViabilidade(lat, lng, addressText).catch(error => {
                    console.error('Erro na verificação de viabilidade:', error);
                    showNotification('Erro ao verificar viabilidade', 'error');
                });
            });
        }
        
        if (cancelBtn && !cancelBtn.hasAttribute('data-connected')) {
            cancelBtn.setAttribute('data-connected', 'true');
            cancelBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Botão Não clicado');
                
                // Simplesmente remove o marcador e mantém o mapa como estava
                if (window.searchMarker && map.hasLayer(window.searchMarker)) {
                    map.removeLayer(window.searchMarker);
                    window.searchMarker = null;
                }
                // Remover notificação desnecessária
            });
        }
    };
    
    // Aguardar o popup ser renderizado
    setTimeout(connectPopupButtons, 100);
}



async function displaySearchResults(results) {
    if (!searchResults) return;

    searchResults.innerHTML = '';
    
    results.forEach((result, index) => {
        const item = document.createElement('div');
        item.className = 'search-result-item';
        item.innerHTML = `
            <div class="search-result-title">${result.display_name && typeof result.display_name === 'string' ? result.display_name.split(',')[0] : 'Local'}</div>
            <div class="search-result-address">${result.display_name || 'Endereço não disponível'}</div>
        `;
        
        item.addEventListener('click', () => {
            const lat = parseFloat(result.lat);
            const lng = parseFloat(result.lon);
            map.setView([lat, lng], 16);
            
            // Remover marcador anterior se existir
            if (window.searchMarker && map.hasLayer(window.searchMarker)) {
                map.removeLayer(window.searchMarker);
            }
            
            // Criar ícone do marcador de pesquisa
            const searchIcon = L.divIcon({
                className: 'search-marker',
                html: '<div style="background-color: #ff4444; width: 16px; height: 16px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 10px rgba(255,68,68,0.8); position: relative;"><div style="position: absolute; top: -2px; left: -2px; width: 20px; height: 20px; border-radius: 50%; background-color: rgba(255,68,68,0.4); animation: pulse 1s infinite;"></div></div>',
                iconSize: [22, 22],
                iconAnchor: [11, 11]
            });
            
            // Adicionar marcador
            window.searchMarker = L.marker([lat, lng], { icon: searchIcon }).addTo(map);
            
            // Mostrar popup de carregamento
            window.searchMarker.bindPopup('<div class="loading-popup">Verificando viabilidade...</div>').openPopup();
            
            // Verificar viabilidade automaticamente com tratamento de erro
            verificarViabilidade(lat, lng, result.display_name).catch(error => {
                console.error('Erro na verificação de viabilidade:', error);
                showNotification('Erro ao verificar viabilidade', 'error');
            });
            
            searchInput.value = result.display_name && typeof result.display_name === 'string' ? result.display_name.split(',')[0] : 'Local';
            hideSearchResults();
        });
        
        searchResults.appendChild(item);
    });
    
    searchResults.style.display = 'block';
}

function clearSearch() {
    searchInput.value = '';
    if (clearSearchBtn) {
        clearSearchBtn.style.display = 'none';
    }
    hideSearchResults();
    searchInput.focus();
}

function hideSearchResults() {
    if (searchResults) {
        searchResults.style.display = 'none';
    }
}

function showSearchLoading() {
    if (searchResults) {
        searchResults.innerHTML = '<div class="search-result-item">Pesquisando...</div>';
        searchResults.style.display = 'block';
    }
}

function hideSearchLoading() {
    // A função displaySearchResults ou hideSearchResults cuidará disso
}

// Funções para o loading screen da verificação de viabilidade
function showViabilityLoading() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'flex';
    }
}

function hideViabilityLoading() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
    }
}

// Função para verificar viabilidade
async function verificarViabilidade(lat, lon, endereco) {
    try {
        // Remover notificação desnecessária
        showViabilityLoading(); // Mostrar loading screen
        
        // Timeout para a verificação de viabilidade
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 segundos
        
        const response = await fetch(`${API_BASE}/verificar-viabilidade?lat=${lat}&lon=${lon}`, {
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();

        if (data.erro) {
            console.error('Erro na verificação:', data.erro);
            showNotification(`Erro na verificação: ${data.erro}`, 'error');
            if (window.searchMarker && typeof window.searchMarker.setPopupContent === 'function') {
                window.searchMarker.setPopupContent(`
                    <div class="viability-popup">
                        <p style="color: #e74c3c;">Erro: ${data.erro}</p>
                    </div>
                `);
            }
            return;
        }

        // Notificar sucesso na verificação
        showNotification(`Viabilidade verificada: ${data.viabilidade.status}`, 'success');

        // Remover linha anterior se existir
        if (window.viabilityLine) {
            map.removeLayer(window.viabilityLine);
        }

        // Remover marcador do CTO anterior se existir
        if (window.ctoMarker) {
            map.removeLayer(window.ctoMarker);
        }

        // Remover camada anterior de todos os CTOs se existir
        if (currentLayer) {
            map.removeLayer(currentLayer);
        }

        // Não carregar todos os CTOs do arquivo durante a verificação.
        // Exibiremos apenas o CTO que atende (marcador destacado) e a rota.
        // Essa mudança evita poluir o mapa com pontos não relevantes.

        // Adicionar marcador destacado do CTO mais próximo
        const ctoIcon = L.divIcon({
            className: 'cto-marker',
            html: `
                <div class="cto-marker-icon">
                    <span class="cto-ring"></span>
                    <span class="cto-dot"></span>
                </div>
            `,
            iconSize: [28, 28],
            iconAnchor: [14, 14]
        });

        window.ctoMarker = L.marker([data.cto?.lat || 0, data.cto?.lon || 0], { 
            icon: ctoIcon 
        }).addTo(map);

        // Desenhar linha seguindo a rota das ruas - Estilo Google Maps
        let routeCoordinates = [];
        
        if (data.rota?.geometria && Array.isArray(data.rota.geometria) && data.rota.geometria.length > 0) {
            // Converter coordenadas da rota de [lon, lat] para [lat, lon] para o Leaflet
            routeCoordinates = data.rota.geometria.map(coord => [coord[1], coord[0]]);
        } else {
            // Fallback para linha reta se não houver geometria da rota
            routeCoordinates = [
                [lat, lon],
                [data.cto?.lat || 0, data.cto?.lon || 0]
            ];
            console.log('⚠️ Usando linha reta - rota por ruas não disponível');
        }
        
        // Remover linha anterior se existir
        if (window.viabilityLine) {
            map.removeLayer(window.viabilityLine);
        }
        if (window.routeBorder) {
            map.removeLayer(window.routeBorder);
        }
        
        // Determinar cor da rota baseada na viabilidade
        const isViable = data.viabilidade.status === 'Viável';
        const routeColor = isViable ? '#1976D2' : '#D32F2F'; // Azul Google ou vermelho
        
        // Criar borda branca (efeito Google Maps)
        window.routeBorder = L.polyline(routeCoordinates, {
            color: '#FFFFFF',
            weight: 8,
            opacity: 0.9,
            smoothFactor: 3.0,
            lineCap: 'round',
            lineJoin: 'round'
        }).addTo(map);
        
        // Criar linha principal colorida
        window.viabilityLine = L.polyline(routeCoordinates, {
            color: routeColor,
            weight: 6,
            opacity: 1.0,
            smoothFactor: 3.0,
            lineCap: 'round',
            lineJoin: 'round'
        }).addTo(map);
        
        // Adicionar efeito de animação pulsante
        let pulseOpacity = 1.0;
        let increasing = false;
        
        const pulseAnimation = setInterval(() => {
            if (increasing) {
                pulseOpacity += 0.03;
                if (pulseOpacity >= 1.0) {
                    increasing = false;
                }
            } else {
                pulseOpacity -= 0.03;
                if (pulseOpacity <= 0.7) {
                    increasing = true;
                }
            }
            
            if (window.viabilityLine && map.hasLayer(window.viabilityLine)) {
                window.viabilityLine.setStyle({ opacity: pulseOpacity });
            } else {
                clearInterval(pulseAnimation);
            }
        }, 80);
        
        // Ajustar zoom para mostrar toda a rota com padding
        if (routeCoordinates.length > 1) {
            const bounds = L.latLngBounds(routeCoordinates);
            map.fitBounds(bounds, { 
                padding: [30, 30],
                maxZoom: 16
            });
        }

        // Criar novo popup com resultado da verificação
        const enderecoResumido = resumirEndereco(endereco);
        const arquivoMapa = data.cto?.arquivo || 'N/A';
        const resultPopupContent = `
            <div class="viability-result-popup">
                <h4>Resultado</h4>
                <div class="viability-result-details">
                    <p><strong>Endereço:</strong> ${enderecoResumido}</p>
                    <p><strong>Distância:</strong> ${data.distancia.metros}m</p>
                    <p><strong>Status:</strong> <span style="color: ${data.viabilidade.cor}; font-weight: bold;">${data.viabilidade.status}</span></p>
                    <p><strong>CTO:</strong> ${formatCtoNumber(data.cto?.nome || 'N/A')}</p>
                    <p><strong>Mapa:</strong> ${arquivoMapa}</p>
                </div>
                <button onclick="fecharVerificacao()" class="viability-close-btn">
                    Fechar
                </button>
            </div>
        `;

        if (window.searchMarker && typeof window.searchMarker.setPopupContent === 'function') {
            window.searchMarker.setPopupContent(resultPopupContent);
            // Abrir o popup automaticamente quando a verificação terminar
            window.searchMarker.openPopup();
        }

        // Ajustar zoom para mostrar tanto o endereço quanto o CTO com margem adequada
        const group = new L.featureGroup([window.searchMarker, window.ctoMarker, window.viabilityLine]);
        const bounds = group.getBounds();
        
        // Adicionar padding maior para melhor visualização
        map.fitBounds(bounds.pad(0.3), {
            maxZoom: 17 // Limitar zoom máximo para não ficar muito próximo
        });
        hideViabilityLoading(); // Esconder loading screen no sucesso
    } catch (error) {
        console.error('Erro ao verificar viabilidade:', error);
        hideViabilityLoading(); // Esconder loading screen no erro
        
        let errorMessage = 'Erro ao verificar viabilidade';
        if (error.name === 'AbortError') {
            errorMessage = 'Verificação demorou mais que 60 segundos e foi cancelada. Tente novamente.';
            showNotification('Timeout na verificação - tente novamente', 'error');
        } else {
            showNotification('Erro de conexão na verificação', 'error');
        }
        
        if (window.searchMarker && typeof window.searchMarker.setPopupContent === 'function') {
            window.searchMarker.setPopupContent(`
                <div class="viability-popup">
                    <p style="color: #e74c3c;">${errorMessage}</p>
                </div>
            `);
        }
    }

}

// Event listener global para botões CTO (usa event delegation)
function setupCTOButtonListeners() {
    const ctoGrid = document.querySelector('.cto-grid');
    if (!ctoGrid) return;
    
    // Usar event delegation para evitar duplicação de listeners
    ctoGrid.addEventListener('click', async (event) => {
        const button = event.target.closest('.cto-btn');
        if (!button) return;
        
        const filename = button.getAttribute('data-file');
        const fileType = button.getAttribute('data-type');
        
        if (!filename) {
            console.error('Nome do arquivo não encontrado no botão');
            return;
        }
        
        // Adicionar feedback visual
        button.classList.add('loading');
        button.disabled = true;
        
        try {
            // Carregar o arquivo KML/KMZ/CSV/XLS/XLSX
            await loadKML(filename);
            
            // Fechar sidebar em dispositivos móveis
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('overlay');
            if (sidebar && window.innerWidth <= 768) {
                sidebar.classList.remove('active');
                if (overlay) overlay.classList.remove('active');
                document.body.classList.remove('no-scroll');
            }
            
        } catch (error) {
            console.error('Erro ao carregar CTO:', error);
            const detail = (error && error.message) ? ` - ${error.message}` : '';
            showNotification(`Erro ao carregar CTO: ${filename}${detail}`, 'error');
        } finally {
            // Remover feedback visual
            button.classList.remove('loading');
            button.disabled = false;
        }
    });
}

// Função legacy para compatibilidade (não faz nada, event delegation é usado)
function initializeCtoButtons() {
    // Função mantida para compatibilidade, mas não é mais necessária
    // porque usamos event delegation em setupCTOButtonListeners()
}

// Nova função: carregar KML/KMZ e exibir CTOs com lazy loading
async function loadKML(filename) {
    const timer = performanceMonitor.startTimer('loadKML');
    console.log('📥 Carregando arquivo:', filename);
    if (!filename) throw new Error('Nome de arquivo inválido');

    // Verificar cache primeiro
    const cacheKey = `coords_${filename}`;
    const cachedData = smartCache.get('coordinates', cacheKey);
    if (cachedData) {
        console.log('📦 Usando dados do cache para:', filename);
        performanceMonitor.recordCacheHit();
        performanceMonitor.endTimer(timer, 'loadKML-cached');
        return processKMLData(cachedData, filename);
    }

    performanceMonitor.recordCacheMiss();
    performanceMonitor.recordApiCall();

    // Timeout controlado
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s

    const url = `${API_BASE}/coordenadas?arquivo=${encodeURIComponent(filename)}`;
    let data;
    try {
        const resp = await fetch(url, { signal: controller.signal });
        clearTimeout(timeoutId);
        data = await resp.json();
        
        // Salvar no cache
        smartCache.set('coordinates', cacheKey, data);
        
        const duration = performanceMonitor.endTimer(timer, 'loadKML-api');
        console.log(`⚡ Arquivo carregado em ${duration.toFixed(2)}ms`);
    } catch (err) {
        clearTimeout(timeoutId);
        console.error('Falha ao buscar coordenadas:', err);
        performanceMonitor.recordError();
        performanceMonitor.endTimer(timer, 'loadKML-error');
        throw err;
    }

    if (data && data.erro) {
        console.error('Erro da API:', data.erro);
        throw new Error(data.erro);
    }
    if (!Array.isArray(data) || data.length === 0) {
        console.warn('Nenhuma coordenada encontrada no arquivo:', filename);
        if (typeof showNotification === 'function') {
            showNotification(`Sem coordenadas em ${filename}`, 'error');
        }
        return;
    }

    // Remover camada anterior se existir
    if (window.viabilityLine) {
        map.removeLayer(window.viabilityLine);
        window.viabilityLine = null;
    }
    if (window.routeBorder) {
        map.removeLayer(window.routeBorder);
        window.routeBorder = null;
    }
    if (window.ctoMarker) {
        map.removeLayer(window.ctoMarker);
        window.ctoMarker = null;
    }
    if (window.searchMarker) {
        map.removeLayer(window.searchMarker);
        window.searchMarker = null;
    }
    if (typeof currentLayer !== 'undefined' && currentLayer) {
        try { map.removeLayer(currentLayer); } catch (e) {}
        currentLayer = null;
    }

    // Criar nova camada para os CTOs
    currentLayer = L.layerGroup();

    // Ícone azul pequeno para pontos de CTO
    const blueIcon = L.divIcon({
        className: 'custom-blue-marker',
        html: '<div style="background-color: #007bff; width: 10px; height: 10px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.4);"></div>',
        iconSize: [10, 10],
        iconAnchor: [5, 5]
    });

    // Função para verificar se um ponto está em Maricá
    function isInMarica(lat, lng) {
        // Limites aproximados de Maricá, RJ
        return lat >= -22.95 && lat <= -22.88 && lng >= -42.85 && lng <= -42.80;
    }

    const bounds = L.latLngBounds([]);
    let filteredCount = 0;
    
    data.forEach(coord => {
        if (coord.tipo === 'point' && (coord.lat !== undefined && coord.lng !== undefined)) {
            // Converter coordenadas de string para número se necessário
            let lat = typeof coord.lat === 'string' ? parseFloat(coord.lat.replace(',', '.')) : coord.lat;
            let lng = typeof coord.lng === 'string' ? parseFloat(coord.lng.replace(',', '.')) : coord.lng;
            
            // Validar se as coordenadas são números válidos
            if (isNaN(lat) || isNaN(lng) || !isFinite(lat) || !isFinite(lng)) {
                console.warn('Coordenadas inválidas ignoradas:', coord);
                return;
            }
            
            // Validar se as coordenadas estão dentro de limites razoáveis
            if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
                console.warn('Coordenadas fora dos limites válidos ignoradas:', coord);
                return;
            }
            
            // Filtrar apenas pontos em Maricá para o arquivo Centro Marica.kmz
            if (filename === 'Centro Marica.kmz' && !isInMarica(lat, lng)) {
                return; // Pular pontos fora de Maricá
            }
            
            const marker = L.marker([lat, lng], { icon: blueIcon });
            if (coord.nome) {
                marker.bindPopup(coord.nome);
            }
            marker.addTo(currentLayer);
            bounds.extend([lat, lng]);
            filteredCount++;
        } else if (coord.tipo === 'line' && Array.isArray(coord.coordenadas)) {
            // Validar e filtrar coordenadas válidas para a linha
            const validCoords = coord.coordenadas.filter(point => {
                if (!Array.isArray(point) || point.length < 2) return false;
                const lat = parseFloat(point[0]);
                const lng = parseFloat(point[1]);
                return !isNaN(lat) && !isNaN(lng) && isFinite(lat) && isFinite(lng) &&
                       lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180;
            });
            
            if (validCoords.length >= 2) {
                const polyline = L.polyline(validCoords, { color: 'blue', weight: 3 });
                if (coord.nome) {
                    polyline.bindPopup(coord.nome);
                }
                polyline.addTo(currentLayer);
                validCoords.forEach(point => bounds.extend(point));
                filteredCount++;
            } else {
                // Silenciar warnings para linhas com coordenadas insuficientes
                // Isso é normal em arquivos KML/KMZ - algumas linhas podem ter apenas 1 ponto
                // Não é um erro, apenas dados que não podem ser renderizados como linhas
            }
        }
    });

    // Adicionar camada ao mapa
    currentLayer.addTo(map);

    // Ajustar a visão para englobar todos os pontos
    if (bounds.isValid()) {
        try {
            map.fitBounds(bounds.pad(0.25), { maxZoom: 17 });
        } catch (e) {
            console.warn('Falha ao ajustar os bounds:', e);
        }
    }
    
    // Notificação única de sucesso
    if (typeof showNotification === 'function') {
        const base = filename.replace(/\.(kml|kmz|csv|xls|xlsx)$/i, '');
        showNotification(`${base} carregado!`, 'success');
    }
}

// Função separada para processar dados KML (reutilizável e otimizada)
function processKMLData(data, filename) {
    if (!Array.isArray(data) || data.length === 0) {
        console.warn('Nenhuma coordenada encontrada no arquivo:', filename);
        if (typeof showNotification === 'function') {
            showNotification(`Sem coordenadas em ${filename}`, 'error');
        }
        return;
    }

    // Remover camada anterior se existir
    if (window.viabilityLine) {
        map.removeLayer(window.viabilityLine);
        window.viabilityLine = null;
    }
    if (window.routeBorder) {
        map.removeLayer(window.routeBorder);
        window.routeBorder = null;
    }
    if (window.ctoMarker) {
        map.removeLayer(window.ctoMarker);
        window.ctoMarker = null;
    }
    if (window.searchMarker) {
        map.removeLayer(window.searchMarker);
        window.searchMarker = null;
    }
    if (typeof currentLayer !== 'undefined' && currentLayer) {
        try { map.removeLayer(currentLayer); } catch (e) {}
        currentLayer = null;
    }

    // Criar nova camada para os CTOs
    currentLayer = L.layerGroup();

    // Ícone otimizado para pontos de CTO
    const blueIcon = L.divIcon({
        className: 'cto-marker-optimized',
        html: '<div style="background-color: #007bff; width: 8px; height: 8px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 5px rgba(0,123,255,0.8);"></div>',
        iconSize: [12, 12],
        iconAnchor: [6, 6]
    });

    // Processar em lotes para melhor performance
    const batchSize = 50;
    let processed = 0;
    
    function processBatch(startIndex) {
        const endIndex = Math.min(startIndex + batchSize, data.length);
        
        for (let i = startIndex; i < endIndex; i++) {
            const coord = data[i];
            try {
                if (coord.tipo === 'point' && (coord.lat !== undefined && coord.lng !== undefined)) {
                    let lat = typeof coord.lat === 'string' ? parseFloat(coord.lat.replace(',', '.')) : coord.lat;
                    let lng = typeof coord.lng === 'string' ? parseFloat(coord.lng.replace(',', '.')) : coord.lng;
                    
                    // Validação mais rigorosa
                    if (isNaN(lat) || isNaN(lng) || !isFinite(lat) || !isFinite(lng)) {
                        continue;
                    }
                    
                    if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
                        continue;
                    }

                    const marker = L.marker([lat, lng], { icon: blueIcon }).addTo(currentLayer);
                    
                    // Popup otimizado com escape de caracteres especiais
                    const nome = (coord.nome || 'CTO').replace(/'/g, "\\'");
                    const popupContent = `
                        <div class="cto-popup-optimized">
                            <h4>${nome}</h4>
                            <p><strong>Arquivo:</strong> ${filename}</p>
                            <p><strong>Coordenadas:</strong> ${lat.toFixed(6)}, ${lng.toFixed(6)}</p>
                            <button onclick="verificarViabilidade(${lat}, ${lng}, '${nome}')" class="btn-verificar-optimized">
                                Verificar Viabilidade
                            </button>
                        </div>
                    `;
                    
                    marker.bindPopup(popupContent);
                    processed++;
                }
            } catch (error) {
                // Log mais silencioso para erros comuns
                if (error.message && !error.message.includes('Invalid LatLng')) {
                    console.warn(`Erro ao processar coordenada ${i}:`, error.message);
                }
            }
        }
        
        // Continuar processamento se houver mais dados
        if (endIndex < data.length) {
            setTimeout(() => processBatch(endIndex), 5); // Delay mínimo para não bloquear UI
        } else {
            // Processamento concluído
            currentLayer.addTo(map);
            
            // Ajustar vista do mapa para mostrar todos os pontos
            if (processed > 0) {
                const group = new L.featureGroup(currentLayer.getLayers());
                map.fitBounds(group.getBounds().pad(0.1));
            }
            
            console.log(`✅ ${processed} CTOs carregados do arquivo ${filename}`);
            
            // Notificação de sucesso
            if (typeof showNotification === 'function') {
                const base = filename.replace(/\.(kml|kmz|csv|xls|xlsx)$/i, '');
                showNotification(`${base} carregado! (${processed} pontos)`, 'success');
            }
        }
    }
    
    // Iniciar processamento em lotes
    processBatch(0);
}

// Função para inicializar upload de arquivos (drag & drop + botão)
// COMENTADA - Elementos de upload não existem no HTML atual
/*
function initializeFileUpload() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const uploadBtn = document.getElementById('upload-btn');
    const progress = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const uploadResults = document.getElementById('upload-results');

    if (!uploadArea || !fileInput || !uploadBtn) {
        console.warn('Área de upload não encontrada; inicialização ignorada.');
        return;
    }

    function resetProgress() {
        if (progress) progress.style.display = 'none';
        if (progressFill) progressFill.style.width = '0%';
        if (progressText) progressText.textContent = 'Enviando...';
    }

    function setProgress(percent, text) {
        if (progress && progressFill) {
            progress.style.display = 'block';
            progressFill.style.width = `${percent}%`;
        }
        if (progressText && text) progressText.textContent = text;
    }

    function showResult(message, type = 'success') {
        if (!uploadResults) return;
        const item = document.createElement('div');
        item.className = `upload-result ${type}`;
        item.textContent = message;
        uploadResults.prepend(item);
    }

    function uploadFile(file) {
        return new Promise((resolve, reject) => {
            const name = file?.name || 'arquivo';
            const ext = name.toLowerCase().split('.').pop();
            if (!['kml', 'kmz'].includes(ext)) {
                showResult(`Formato inválido: ${name}. Use .kml ou .kmz`, 'error');
                if (typeof showNotification === 'function') {
                    showNotification(`Formato inválido: ${name}`, 'error');
                }
                return reject(new Error('Formato inválido'));
            }

            const formData = new FormData();
            formData.append('file', file);

            setProgress(5, 'Preparando envio...');

            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/upload');

            xhr.upload.onprogress = function (e) {
                if (e.lengthComputable) {
                    const percent = Math.min(95, Math.round((e.loaded / e.total) * 95));
                    setProgress(percent, `Enviando (${percent}%)...`);
                } else {
                    setProgress(50, 'Enviando...');
                }
            };

            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4) {
                    try {
                        const resp = JSON.parse(xhr.responseText || '{}');
                        if (xhr.status >= 200 && xhr.status < 300 && resp && resp.sucesso) {
                            setProgress(100, 'Concluído');
                            showResult(`✅ ${name} enviado (${resp.coordenadas_encontradas} coordenadas)`, 'success');
                            if (typeof showNotification === 'function') {
                                showNotification(`Arquivo ${name} enviado com sucesso!`, 'success');
                            }
                            resolve(resp);
                        } else {
                            const msg = (resp && resp.erro) ? resp.erro : `Falha ao enviar ${name}`;
                            showResult(`❌ ${msg}`, 'error');
                            if (typeof showNotification === 'function') {
                                showNotification(msg, 'error');
                            }
                            reject(new Error(msg));
                        }
                    } catch (err) {
                        showResult(`❌ Erro ao processar resposta para ${name}`, 'error');
                        reject(err);
                    } finally {
                        setTimeout(() => resetProgress(), 1200);
                    }
                }
            };

            xhr.onerror = function () {
                showResult(`❌ Erro de rede ao enviar ${name}`, 'error');
                if (typeof showNotification === 'function') {
                    showNotification(`Erro de rede ao enviar ${name}`, 'error');
                }
                reject(new Error('Network error'));
                setTimeout(() => resetProgress(), 1200);
            };

            xhr.send(formData);
        });
    }

    function handleFiles(files) {
        if (!files || files.length === 0) return;
        const list = Array.from(files);
        (async () => {
            for (const file of list) {
                try {
                    await uploadFile(file);
                } catch (err) {
                    console.error('Erro no upload:', err);
                }
            }
        })();
    }

    // Interações drag & drop
    ['dragenter', 'dragover'].forEach(evt => {
        uploadArea.addEventListener(evt, e => {
            e.preventDefault();
            e.stopPropagation();
            uploadArea.classList.add('dragover');
        });
    });
    ['dragleave', 'drop'].forEach(evt => {
        uploadArea.addEventListener(evt, e => {
            e.preventDefault();
            e.stopPropagation();
            uploadArea.classList.remove('dragover');
        });
    });
    uploadArea.addEventListener('drop', e => {
        handleFiles(e.dataTransfer.files);
    });

    // Clique para selecionar arquivos
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => handleFiles(fileInput.files));
}
*/

// Inicializar upload de arquivos
// initializeFileUpload(); // Movido para DOMContentLoaded
 
 // Inicializar botões dos CTOs
// initializeCtoButtons(); // Movido para DOMContentLoaded
 
 // Inicializar dashboard e carregar arquivos
 cleanExpiredCache();
 // loadKmlFiles(); // Comentado - não precisamos mais da lista dinâmica
 
 // Atualizar dashboard periodicamente (a cada 5 minutos)
 setInterval(() => {
     cleanExpiredCache();
 }, 5 * 60 * 1000);
 

 
// Inicializar barra de pesquisa principal
// initializeMainSearch(); // Removido - será chamado no DOMContentLoaded

// Inicializar menu hambúrguer e sidebar
// initializeMenuToggle(); // Movido para DOMContentLoaded

// Inicializar botão de alternância do cursor
// initializeCursorToggle(); // Movido para DOMContentLoaded

// ===== FUNCIONALIDADES MELHORADAS DA BARRA DE PESQUISA =====
 
 // Variáveis globais para a barra de pesquisa melhorada
 let searchHistory = [];
 let currentSuggestions = [];
 let selectedSuggestionIndex = -1;
 
 // Inicializar funcionalidades melhoradas da barra de pesquisa
function initializeEnhancedSearchBar() {
    // Carregar histórico do localStorage
    loadSearchHistory();
     
     // Inicializar eventos
     initializeSearchEvents();
     initializeFilterEvents();
     initializeHistoryEvents();
     initializeKeyboardShortcuts();
     
     console.log('✅ Barra de pesquisa melhorada inicializada!');
 }
 
 // Carregar histórico de pesquisas do localStorage
 function loadSearchHistory() {
     try {
         const saved = localStorage.getItem('search_history');
         if (saved) {
             searchHistory = JSON.parse(saved);
             console.log(`📚 Histórico carregado: ${searchHistory.length} itens`);
         }
     } catch (e) {
         console.warn('⚠️ Erro ao carregar histórico:', e);
         searchHistory = [];
     }
 }
 
 // Salvar histórico no localStorage
 function saveSearchHistory() {
     try {
         // Manter apenas os últimos 20 itens
         const limitedHistory = searchHistory.slice(-20);
         localStorage.setItem('search_history', JSON.stringify(limitedHistory));
         searchHistory = limitedHistory;
     } catch (e) {
         console.warn('⚠️ Erro ao salvar histórico:', e);
     }
 }
 
 // Adicionar item ao histórico
 function addToSearchHistory(query) {
     if (!query || query.trim().length < 2) return;
     
     const cleanQuery = query.trim();
     
     // Remover duplicatas
     searchHistory = searchHistory.filter(item => item.query !== cleanQuery);
     
     // Adicionar no início
     searchHistory.unshift({
         query: cleanQuery,
         timestamp: Date.now(),
         type: detectSearchType(cleanQuery)
     });
     
     saveSearchHistory();
     console.log(`📝 Adicionado ao histórico: "${cleanQuery}"`);
 }
 
 // Detectar tipo de pesquisa
 function detectSearchType(query) {
     const numberPattern = /^\d+$/;
     
     if (isValidCEP(query)) return 'cep';
     if (numberPattern.test(query)) return 'number';
     if (query.includes(',') || query.includes('-')) return 'address';
     return 'city';
 }
 
 // Inicializar eventos da pesquisa
 function initializeSearchEvents() {
     console.log('🔧 Inicializando eventos de pesquisa...');
     
     // Aguardar o DOM estar completamente carregado
     if (document.readyState === 'loading') {
         document.addEventListener('DOMContentLoaded', initializeSearchEvents);
         return;
     }
     
     const searchInput = document.getElementById('search-input');
    const clearBtn = document.querySelector('.clear-search-btn');
    
    if (!searchInput) {
        console.error('❌ Campo de pesquisa não encontrado!');
        return;
    }
     
     // Remover event listeners existentes para evitar duplicação
     const newSearchInput = searchInput.cloneNode(true);
     searchInput.parentNode.replaceChild(newSearchInput, searchInput);
     
     // Referenciar o novo elemento
     const freshSearchInput = document.getElementById('search-input');
     
     // Evento de input apenas para mostrar/ocultar botão de limpar
    freshSearchInput.addEventListener('input', function(e) {
        const query = e.target.value;
        console.log('⌨️ Input event disparado com query:', query);
        
        // Mostrar sugestões (inclui detecção de CEP)
        showSuggestions(query);
        
        // Limpar timeout anterior se existir
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        
        // Se a query estiver vazia, limpar resultados
        if (!query || query.trim().length === 0) {
            hideAllDropdowns();
            // Limpar resultados de pesquisa se existirem
            const resultsContainer = document.getElementById('search-results');
            if (resultsContainer) {
                resultsContainer.innerHTML = '';
                resultsContainer.style.display = 'none';
            }
            return;
        }
        
        // Não executar busca automática - aguardar Enter ou clique na lupa
    });
     
     // Event listener para focus (sem sugestões ou histórico)
     freshSearchInput.addEventListener('focus', function() {
     });
     
     // Event listener para blur
     freshSearchInput.addEventListener('blur', function() {
         // Delay para permitir cliques em sugestões
         setTimeout(() => {
             hideSuggestions();
         }, 200);
     });
     
     // Event listener para Enter no campo (usa keydown para maior compatibilidade)
    freshSearchInput.addEventListener('keydown', function(e) {
         if (e.key === 'Enter') {
             console.log('⌨️ Enter pressionado!');
             e.preventDefault();
             
             // Se o dropdown de sugestões está visível, deixa o handler global decidir
             const suggestionsDropdown = document.querySelector('.search-suggestions-dropdown');
             if (suggestionsDropdown && suggestionsDropdown.style.display !== 'none') {
                 return;
             }
             
             // Cancelar qualquer timeout pendente para pesquisa imediata
             if (searchTimeout) {
                 clearTimeout(searchTimeout);
                 searchTimeout = null;
             }
             
             const query = this.value.trim();
            if (query) {
                addToSearchHistory(query);
                searchUnified(query);
                hideAllDropdowns();
            }
         }
     });
     
     // Event listener para botão de limpar
     if (clearBtn) {
         clearBtn.addEventListener('click', function() {
             freshSearchInput.value = '';
             freshSearchInput.focus();
             hideAllDropdowns();
             // Limpar resultados de pesquisa
             const resultsContainer = document.getElementById('search-results');
             if (resultsContainer) {
                 resultsContainer.innerHTML = '';
                 resultsContainer.style.display = 'none';
             }
         });
     }
     
     // Reconectar botão da lupa após clonagem do input
     const searchBtn = document.getElementById('search-btn');
     if (searchBtn) {
         // Remover listeners antigos
         const newSearchBtn = searchBtn.cloneNode(true);
         searchBtn.parentNode.replaceChild(newSearchBtn, searchBtn);
         
         // Adicionar novo listener
        newSearchBtn.addEventListener('click', function() {
            const query = freshSearchInput.value.trim();
            if (query) {
                addToSearchHistory(query);
                searchUnified(query);
                hideAllDropdowns();
            }
        });
     }
 }
 
 // Inicializar eventos dos filtros
 function initializeFilterEvents() {
     const filterBtn = document.querySelector('.filter-btn');
     const filterDropdown = document.querySelector('.filter-dropdown');
     
     if (filterBtn && filterDropdown) {
         filterBtn.addEventListener('click', function(e) {
             e.stopPropagation();
             toggleDropdown(filterDropdown, filterBtn);
         });
         
         // Event listeners para opções de filtro
         const filterOptions = filterDropdown.querySelectorAll('.filter-option');
         filterOptions.forEach(option => {
             option.addEventListener('click', function() {
                 // Implementar lógica de filtro aqui
                 console.log('Filtro selecionado:', this.textContent);
                 hideAllDropdowns();
             });
         });
     }
 }
 
 // Inicializar eventos de histórico
 function initializeHistoryEvents() {
     const historyBtn = document.querySelector('.history-btn');
     const historyDropdown = document.querySelector('.history-dropdown');
     
     if (historyBtn && historyDropdown) {
         historyBtn.addEventListener('click', function(e) {
             e.stopPropagation();
             showSearchHistory();
         });
     }
 }
 
 // Inicializar atalhos de teclado
 function initializeKeyboardShortcuts() {
     document.addEventListener('keydown', function(e) {
         const searchInput = document.getElementById('search-input');
         const suggestionsDropdown = document.querySelector('.search-suggestions-dropdown');
         
         // Ctrl/Cmd + K para focar na pesquisa
         if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
             e.preventDefault();
             if (searchInput) {
                 searchInput.focus();
                 searchInput.select();
             }
         }
         
         // Escape para fechar dropdowns
         if (e.key === 'Escape') {
             hideAllDropdowns();
             if (searchInput) {
                 searchInput.blur();
             }
         }
         
         // Navegação por setas nas sugestões
         if (suggestionsDropdown && suggestionsDropdown.style.display !== 'none') {
             if (e.key === 'ArrowDown') {
                 e.preventDefault();
                 navigateSuggestions(1);
             } else if (e.key === 'ArrowUp') {
                 e.preventDefault();
                 navigateSuggestions(-1);
             } else if (e.key === 'Enter') {
                 e.preventDefault();
                 if (selectedSuggestionIndex >= 0) {
                     selectSuggestion(selectedSuggestionIndex);
                 } else {
                     // Se não há sugestão selecionada, executar pesquisa imediata
                     if (searchTimeout) {
                         clearTimeout(searchTimeout);
                         searchTimeout = null;
                     }
                     
                     const query = document.getElementById('search-input').value.trim();
                    if (query) {
                        addToSearchHistory(query);
                        searchUnified(query);
                        hideAllDropdowns();
                    }
                 }
             }
         }
     });
 }
 
 // Função para mostrar sugestões
function showSuggestions(query) {
    if (!query || query.trim().length < 2) {
        hideSuggestions();
        return;
    }
    
    const suggestions = generateSuggestions(query);
    const dropdown = document.querySelector('.search-suggestions-dropdown');
    
    if (!dropdown || suggestions.length === 0) {
        hideSuggestions();
        return;
    }
    
    dropdown.innerHTML = suggestions.map((suggestion, index) => `
        <div class="suggestion-item" data-index="${index}" onclick="selectSuggestion(${index})">
            <i class="suggestion-icon ${getSuggestionIcon(suggestion.type)}"></i>
            <span class="suggestion-text">${suggestion.text}</span>
            <span class="suggestion-type">${suggestion.type}</span>
        </div>
    `).join('');
    
    currentSuggestions = suggestions;
    selectedSuggestionIndex = -1;
    
    console.log('📋 Dropdown innerHTML após inserção:', dropdown.innerHTML);
    console.log('📋 Chamando showDropdown...');
    showDropdown(dropdown);
    console.log('📋 Dropdown style display após showDropdown:', dropdown.style.display);
}
 
 // Função para gerar sugestões
 function generateSuggestions(query) {
     const suggestions = [];
     const lowerQuery = query.toLowerCase();
     
     // Sugestões baseadas no histórico
     const historyMatches = searchHistory
         .filter(item => item.query.toLowerCase().includes(lowerQuery))
         .slice(0, 3)
         .map(item => ({
             text: item.query,
             type: item.type,
             source: 'history'
         }));
     
     suggestions.push(...historyMatches);
     
     // Sugestões automáticas baseadas no tipo
     if (/^\d/.test(query)) {
         if (query.length <= 8) {
             suggestions.push({
                 text: query + ' (CEP)',
                 type: 'cep',
                 source: 'auto'
             });
         }
     } else {
         suggestions.push({
             text: query,
             type: 'address',
             source: 'auto'
         });
     }
     
     return suggestions.slice(0, 5);
 }
 
 // Função para obter ícone da sugestão
 function getSuggestionIcon(type) {
     switch (type) {
         case 'cep': return 'fas fa-map-pin';
         case 'address': return 'fas fa-map-marker-alt';
         case 'number': return 'fas fa-hashtag';
         default: return 'fas fa-search';
     }
 }
 
 // Função para navegar pelas sugestões
 function navigateSuggestions(direction) {
     const suggestions = document.querySelectorAll('.suggestion-item');
     if (suggestions.length === 0) return;
     
     // Remove seleção anterior
     suggestions.forEach(item => item.classList.remove('selected'));
     
     // Calcula novo índice
     selectedSuggestionIndex += direction;
     
     if (selectedSuggestionIndex < 0) {
         selectedSuggestionIndex = suggestions.length - 1;
     } else if (selectedSuggestionIndex >= suggestions.length) {
         selectedSuggestionIndex = 0;
     }
     
     // Adiciona nova seleção
     suggestions[selectedSuggestionIndex].classList.add('selected');
 }
 
 // Função para selecionar sugestão
window.selectSuggestion = function(index) {
    if (index < 0 || index >= currentSuggestions.length) {
        return;
    }
    
    const suggestion = currentSuggestions[index];
    const searchInput = document.getElementById('search-input');
    
    if (searchInput) {
        const cleanText = suggestion.text.replace(' (CEP)', '');
        searchInput.value = cleanText;
        addToSearchHistory(cleanText);
        searchUnified(cleanText);
        hideAllDropdowns();
        searchInput.focus();
    }
}
 
 // Função para mostrar histórico de pesquisa
 function showSearchHistory() {
     const dropdown = document.querySelector('.history-dropdown');
     if (!dropdown) return;
     
     if (searchHistory.length === 0) {
         dropdown.innerHTML = '<div class="history-empty">Nenhum histórico de pesquisa</div>';
     } else {
         dropdown.innerHTML = `
             <div class="history-header">
                 <span>Pesquisas recentes</span>
                 <button class="clear-history-btn" onclick="clearSearchHistory()">
                     <i class="fas fa-trash"></i>
                 </button>
             </div>
             ${searchHistory.slice(0, 10).map((item, index) => `
                 <div class="history-item" onclick="selectSuggestion(${index})">
                     <i class="history-icon ${getSuggestionIcon(item.type)}"></i>
                     <span class="history-text">${item.query}</span>
                     <span class="history-time">${new Date(item.timestamp).toLocaleDateString()}</span>
                 </div>
             `).join('')}
         `;
         
         // Atualizar currentSuggestions para permitir seleção
         currentSuggestions = searchHistory.slice(0, 10).map(item => ({
             text: item.query,
             type: item.type,
             source: 'history'
         }));
     }
     
     showDropdown(dropdown);
 }
 
 // Função para limpar histórico
 function clearSearchHistory() {
     searchHistory = [];
     saveSearchHistory();
     showSearchHistory();
     showNotification('Histórico de pesquisa limpo', 'success');
 }
 
 // Função para mostrar dropdown
function showDropdown(dropdown) {
    hideAllDropdowns();
    dropdown.style.display = 'block';
}
 
 // Função para esconder sugestões
 function hideSuggestions() {
     const dropdown = document.querySelector('.search-suggestions-dropdown');
     if (dropdown) {
         dropdown.style.display = 'none';
     }
 }
 
 // Função para alternar dropdown
 function toggleDropdown(dropdown, button) {
     if (dropdown.style.display === 'block') {
         dropdown.style.display = 'none';
         button.classList.remove('active');
     } else {
         hideAllDropdowns();
         dropdown.style.display = 'block';
         button.classList.add('active');
     }
 }
 
 // Função para esconder todos os dropdowns
 function hideAllDropdowns() {
     const dropdowns = document.querySelectorAll('.search-suggestions-dropdown, .filter-dropdown, .history-dropdown');
     const buttons = document.querySelectorAll('.filter-btn, .history-btn');
     
     dropdowns.forEach(dropdown => {
         dropdown.style.display = 'none';
     });
     
     buttons.forEach(button => {
         button.classList.remove('active');
     });
     
     selectedSuggestionIndex = -1;
     
     // Limpar seleções
     const selectedItems = document.querySelectorAll('.suggestion-item.selected, .history-item.selected');
     selectedItems.forEach(item => {
         item.classList.remove('selected');
     });
 }
 
 // Event listener global para fechar dropdowns
 document.addEventListener('click', function(e) {
     const searchContainer = e.target.closest('.search-container');
     if (!searchContainer) {
         hideAllDropdowns();
     }
 });
 
 // Adicionar estilos adicionais
const additionalStyle = document.createElement('style');
additionalStyle.textContent = `
    .suggestion-item.selected,
    .history-item.selected {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%) !important;
        color: white !important;
    }
    
    .suggestion-item.selected .suggestion-icon,
    .suggestion-item.selected .suggestion-type,
    .history-item.selected .history-icon {
        color: white !important;
    }
    
    /* Estilos para botões do popup do mapa */
    .leaflet-popup-content button {
        transition: all 0.2s ease !important;
    }
    
    .leaflet-popup-content button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
    }
    
    .leaflet-popup-content button:active {
        transform: translateY(0) !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    /* Melhorar aparência do popup */
    .leaflet-popup-content-wrapper {
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    }
    
    .leaflet-popup-tip {
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
`;
document.head.appendChild(additionalStyle);

// Estilos para o ícone de CTO minimalista com pulso
additionalStyle.textContent += `
    .cto-marker-icon {
        position: relative;
        width: 28px;
        height: 28px;
    }
    .cto-marker-icon::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 34px;
        height: 34px;
        transform: translate(-50%, -50%);
        border-radius: 50%;
        background: rgba(255,255,255,0.95);
        box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    }
    .cto-marker-icon .cto-ring {
        position: absolute;
        top: 50%;
        left: 50%;
        width: 26px;
        height: 26px;
        transform: translate(-50%, -50%);
        border-radius: 50%;
        border: 4px solid var(--primary-color);
        background: rgba(255,255,255,0.15);
        box-shadow: 0 0 12px rgba(0,0,0,0.3);
    }
    .cto-marker-icon .cto-dot {
        position: absolute;
        top: 50%;
        left: 50%;
        width: 10px;
        height: 10px;
        transform: translate(-50%, -50%);
        border-radius: 50%;
        background: var(--primary-color);
        border: 2px solid #fff;
        box-shadow: 0 0 8px rgba(0,0,0,0.3);
    }
    .cto-marker-icon::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 28px;
        height: 28px;
        transform: translate(-50%, -50%);
        border-radius: 50%;
        border: 3px solid var(--primary-color);
        opacity: 0.8;
        animation: ctoPulse 1.6s ease-out infinite;
    }
    @keyframes ctoPulse {
        0% { transform: translate(-50%, -50%) scale(1); opacity: 0.8; }
        100% { transform: translate(-50%, -50%) scale(2); opacity: 0; }
    }
`;

 
 // Inicializar funcionalidades melhoradas da barra de pesquisa
 initializeEnhancedSearchBar();





// Inicializa o menu hambúrguer e controla a sidebar
function initializeMenuToggle() {
    console.log('🍔 Inicializando menu...');
    const sidebar = document.getElementById('sidebar');
    const menuToggle = document.getElementById('menu-toggle');
    const closeMenu = document.getElementById('close-menu');
    const overlay = document.getElementById('overlay');

    if (!sidebar || !menuToggle) {
        console.error('❌ Elementos de menu não encontrados.');
        return;
    }

    function openSidebar() {
        sidebar.classList.add('active');
        menuToggle.classList.add('active');
        if (overlay) overlay.classList.add('active');
        document.body.classList.add('no-scroll');
        if (typeof hideAllDropdowns === 'function') hideAllDropdowns();
    }

    function closeSidebar() {
        sidebar.classList.remove('active');
        menuToggle.classList.remove('active');
        if (overlay) overlay.classList.remove('active');
        document.body.classList.remove('no-scroll');
    }

    // Abrir/fechar ao clicar no botão hambúrguer
    menuToggle.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (sidebar.classList.contains('active')) {
            closeSidebar();
        } else {
            openSidebar();
        }
    });

    // Fechar ao clicar no botão de fechar dentro da sidebar
    if (closeMenu) {
        closeMenu.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            closeSidebar();
        });
    }

    // Fechar ao clicar no overlay
    if (overlay) {
        overlay.addEventListener('click', (e) => {
            e.preventDefault();
            closeSidebar();
        });
    }

    // Fechar ao clicar fora da sidebar
    document.addEventListener('click', (e) => {
        const clickedInsideSidebar = e.target.closest('#sidebar');
        const clickedMenuToggle = e.target.closest('#menu-toggle');
        if (!clickedInsideSidebar && !clickedMenuToggle && sidebar.classList.contains('active')) {
            closeSidebar();
        }
    });

    // Fechar com ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeSidebar();
        }
    });
}

// Função para inicializar o botão de alternância do cursor
function initializeCursorToggle() {
    console.log('🔄 Inicializando alternância do cursor...');
    
    // Aguardar o DOM estar completamente carregado
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeCursorToggle);
        return;
    }
    
    const cursorToggleBtn = document.getElementById('cursor-toggle-btn');
    const map = window.map;
    
    if (!cursorToggleBtn) {
        console.error('❌ Botão de alternância do cursor não encontrado!');
        return;
    }
    
    if (!map) {
        console.error('❌ Mapa não encontrado!');
        return;
    }
    
    // Verificar se o evento já foi adicionado
    if (cursorToggleBtn.hasAttribute('data-initialized')) {
        console.log('⚠️ Botão já inicializado, pulando...');
        return;
    }
    
    // Adicionar evento de clique no botão
    cursorToggleBtn.addEventListener('click', function() {
        console.log('🔄 Alternando modo do cursor...');
        toggleCursorMode();
    });
    
    // Marcar como inicializado
    cursorToggleBtn.setAttribute('data-initialized', 'true');
    
    console.log('✅ Alternância do cursor inicializada com sucesso!');
}

// Função para alternar entre modo navegação e modo clique
function toggleCursorMode() {
    const cursorToggleBtn = document.getElementById('cursor-toggle-btn');
    const iconElement = cursorToggleBtn.querySelector('i');
    const textElement = cursorToggleBtn.querySelector('.cursor-mode-text');
    
    isClickMode = !isClickMode;
    
    if (isClickMode) {
        // Ativar modo clique
        console.log('✅ Modo clique ativado');
        cursorToggleBtn.classList.add('click-mode');
        iconElement.className = 'fas fa-crosshairs';
        textElement.textContent = 'Marcar';
        cursorToggleBtn.title = 'Modo marcação ativo - Clique no mapa para marcar';
        
        // Alterar cursor do mapa
        document.getElementById('map').style.cursor = 'crosshair';
        
        // Desabilitar arrastar e zoom do mapa
        map.dragging.disable();
        map.scrollWheelZoom.disable();
        map.doubleClickZoom.disable();
        map.touchZoom.disable();
        map.boxZoom.disable();
        map.keyboard.disable();
        
        // Adicionar evento de clique no mapa
        map.on('click', onMapClick);
        
        showNotification('Modo marcação ativado', 'info');
    } else {
        // Ativar modo navegação
        console.log('🧭 Modo navegação ativado');
        cursorToggleBtn.classList.remove('click-mode');
        iconElement.className = 'fas fa-hand-pointer';
        textElement.textContent = 'Navegar';
        cursorToggleBtn.title = 'Alternar para modo de marcação';
        
        // Restaurar cursor do mapa
        document.getElementById('map').style.cursor = '';
        
        // Reabilitar arrastar e zoom do mapa
        map.dragging.enable();
        map.scrollWheelZoom.enable();
        map.doubleClickZoom.enable();
        map.touchZoom.enable();
        map.boxZoom.enable();
        map.keyboard.enable();
        
        // Remover evento de clique no mapa
        map.off('click', onMapClick);
        
        // Remover notificação desnecessária
    }
}

// Função para lidar com cliques no mapa quando em modo marcação
async function onMapClick(e) {
    if (!isClickMode) return;
    
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;
    
    // Remover marcador anterior se existir
    if (window.searchMarker) {
        map.removeLayer(window.searchMarker);
    }
    
    // Adicionar marcador no local clicado
    window.searchMarker = L.marker([lat, lng], {
        icon: L.divIcon({
            className: 'custom-marker',
            html: '<i class="fas fa-map-pin" style="color: #e74c3c; font-size: 24px;"></i>',
            iconSize: [24, 24],
            iconAnchor: [12, 24]
        })
    }).addTo(map);
    
    // Mostrar popup simples diretamente
    const simplePopupContent = `
        <div class="viability-popup map-click-popup">
            <h4 class="viability-popup-title">Verificar Viabilidade?</h4>
            <div class="popup-actions">
                <button onclick="verificarViabilidade(${lat}, ${lng})" class="confirm-verify-btn">
                    Sim
                </button>
                <button onclick="apenasMarcar(${lat}, ${lng})" class="cancel-verify-btn">
                    Não
                </button>
            </div>
        </div>
    `;
    
    window.searchMarker.bindPopup(simplePopupContent, {
        closeOnClick: false,
        autoClose: false,
        className: 'custom-popup'
    }).openPopup();
    
    // Voltar para modo navegação após marcar
    setTimeout(() => {
        if (isClickMode) {
            toggleCursorMode();
        }
    }, 100);
}

// Disponibilizar ação global para fechar a verificação e resetar o mapa
window.fecharVerificacao = function() {
    try {
        // Remover linha de viabilidade e borda de rota
        if (window.viabilityLine && map.hasLayer(window.viabilityLine)) {
            map.removeLayer(window.viabilityLine);
            window.viabilityLine = null;
        }
        if (window.routeBorder && map.hasLayer(window.routeBorder)) {
            map.removeLayer(window.routeBorder);
            window.routeBorder = null;
        }
        // Remover marcador do CTO
        if (window.ctoMarker && map.hasLayer(window.ctoMarker)) {
            map.removeLayer(window.ctoMarker);
            window.ctoMarker = null;
        }
        // Remover camada com todos os CTOs
        if (currentLayer && map.hasLayer(currentLayer)) {
            map.removeLayer(currentLayer);
            currentLayer = null;
        }
        // Remover marcador de busca
        if (window.searchMarker && map.hasLayer(window.searchMarker)) {
            map.removeLayer(window.searchMarker);
            window.searchMarker = null;
        }
        // Limpar UI de busca
        if (typeof searchResults !== 'undefined' && searchResults) {
            searchResults.classList.remove('show');
            searchResults.innerHTML = '';
        }
        if (typeof addressSearch !== 'undefined' && addressSearch) {
            addressSearch.value = '';
        }
        // Resetar mapa para a visão inicial (Maricá)
        map.setView([-22.919, -42.818], 12);
        // Remover notificação desnecessária
    } catch (err) {
        console.error('Erro ao fechar verificação:', err);
    }
};

// Função para apenas marcar o local sem verificar viabilidade
window.apenasMarcar = function(lat, lng) {
    // Fechar popup atual
    map.closePopup();
    
    // Remover marcador se existir
    if (window.searchMarker && map.hasLayer(window.searchMarker)) {
        map.removeLayer(window.searchMarker);
        window.searchMarker = null;
    }
    
    // Remover linha de viabilidade se existir
    if (window.viabilityLine && map.hasLayer(window.viabilityLine)) {
        map.removeLayer(window.viabilityLine);
        window.viabilityLine = null;
    }
    
    // Remover marcador CTO se existir
    if (window.ctoMarker && map.hasLayer(window.ctoMarker)) {
        map.removeLayer(window.ctoMarker);
        window.ctoMarker = null;
    }
    
    // Remover notificação desnecessária
};


// Função para carregar arquivos dinamicamente da API
async function loadCTOFiles() {
    try {
        const response = await fetch(`${API_BASE}/arquivos`);
        const arquivos = await response.json();
        
        const ctoGrid = document.querySelector('.cto-grid');
        if (!ctoGrid) return;
        
        // Mapeamento de ícones por tipo
        const iconMap = {
            'kml': { class: 'kml', icon: 'fa-map-marker-alt' },
            'kmz': { class: 'kmz', icon: 'fa-map-marked-alt' },
            'csv': { class: 'csv', icon: 'fa-file-csv' },
            'xls': { class: 'xls', icon: 'fa-file-excel' },
            'xlsx': { class: 'xlsx', icon: 'fa-file-excel' }
        };
        
        // Limpar apenas os botões dinâmicos (mantém os hardcoded que já existem)
        // Na verdade, vamos remover todos e recriar apenas os que existem
        
        arquivos.forEach(arquivo => {
            // Verificar se o botão já existe (hardcoded)
            const existingBtn = document.querySelector(`[data-file="${arquivo.nome}"]`);
            if (existingBtn) return; // Não duplicar botões já existentes
            
            // Criar novo botão para arquivo da API
            const iconInfo = iconMap[arquivo.tipo] || { class: 'kml', icon: 'fa-map-marker-alt' };
            const nomeDisplay = arquivo.nome.replace(/\.[^.]+$/, ''); // Remove extensão
            
            const button = document.createElement('button');
            button.className = 'cto-card cto-btn';
            button.setAttribute('data-file', arquivo.nome);
            button.setAttribute('data-type', arquivo.tipo);
            
            button.innerHTML = `
                <div class="cto-icon ${iconInfo.class}">
                    <i class="fas ${iconInfo.icon}"></i>
                </div>
                <div class="cto-info">
                    <span class="cto-name">${nomeDisplay}</span>
                    <span class="cto-type">${arquivo.tipo.toUpperCase()}</span>
                </div>
            `;
            
            ctoGrid.appendChild(button);
        });
        
        console.log(`✅ ${arquivos.length} arquivos carregados dinamicamente`);
    } catch (error) {
        console.error('Erro ao carregar arquivos:', error);
    }
}

// ===== INICIALIZAÇÃO DO SISTEMA =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Iniciando sistema...');
    
    // Inicializar modo escuro PRIMEIRO
    console.log('🌙 Inicializando tema primeiro...');
    initializeThemeToggle();
    
    // Aguardar um pouco antes de inicializar outras funcionalidades
    setTimeout(() => {
        console.log('🔧 Inicializando outras funcionalidades...');
        initializeMainSearch();
        setupCTOButtonListeners(); // Usar event delegation (funciona para todos os botões)
        loadCTOFiles(); // Carregar arquivos dinamicamente e adicionar novos botões
        initializeCursorToggle();
        initializeMenuToggle();
        
        console.log('✅ Sistema inicializado com sucesso!');
        console.log('💡 Dica: Use Ctrl+Shift+P para ver estatísticas de performance');
        
        // Atalho de teclado para mostrar estatísticas de performance (Ctrl+Shift+P)
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.shiftKey && e.key === 'P') {
                e.preventDefault();
                performanceMonitor.showIndicator();
            }
        });
    }, 100);
});

// Inicialização imediata do tema (caso o DOM já esteja pronto)
if (document.readyState === 'loading') {
    console.log('📄 DOM ainda carregando, aguardando...');
} else {
    console.log('📄 DOM já pronto, inicializando tema imediatamente...');
    initializeThemeToggle();
}