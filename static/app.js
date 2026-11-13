/**
 * ALGOQUANT INDIA - FRONTEND CONTROLLER & DUAL STRATEGY ENGINE
 * Top 200 Market Cap Companies: Daily Swing (50 EMA) & Intraday Momentum (200 EMA 15m)
 */

// Application State
const state = {
    mode: 'daily',           // 'daily' | 'intraday'
    signals: [],
    summary: {},
    activeTab: 'core',       // 'core' | 'enhanced'
    activeFilter: 'actionable', // Default: Only show genuine actionable stocks that qualify the entry filter
    searchQuery: '',
    currentChartData: null,
    isLoading: false
};

// DOM Elements
const el = {
    loadingSpinner: document.getElementById('loading-spinner'),
    signalsContainer: document.getElementById('signals-container'),
    emptyState: document.getElementById('empty-state'),
    btnRefresh: document.getElementById('btn-refresh-scan'),
    btnExportCsv: document.getElementById('btn-export-csv'),
    inputSearch: document.getElementById('input-search'),
    strategyTabs: document.querySelectorAll('.strategy-tab'),
    filterPills: document.querySelectorAll('.pill'),
    enhancedExplainer: document.getElementById('enhanced-explainer'),
    
    // Mode Switcher Buttons
    btnModeDaily: document.getElementById('btn-mode-daily'),
    btnModeIntraday: document.getElementById('btn-mode-intraday'),
    btnModePortfolio: document.getElementById('btn-mode-portfolio'),
    screenerView: document.getElementById('screener-view'),
    portfolioView: document.getElementById('portfolio-view'),
    btnRefreshPortfolio: document.getElementById('btn-refresh-portfolio'),
    
    // Dynamic Headings & Banners
    headerStrategySubtitle: document.getElementById('header-strategy-subtitle'),
    bannerModeVal: document.getElementById('banner-mode-val'),
    bannerSetupVal: document.getElementById('banner-setup-val'),
    tabCoreLabel: document.getElementById('tab-core-label'),
    signalsHeading: document.getElementById('signals-table-heading'),
    signalsDesc: document.getElementById('signals-table-desc'),
    loadingText: document.getElementById('loading-text'),
    kpiTriggersLabel: document.getElementById('kpi-triggers-label'),
    kpiTriggersSub: document.getElementById('kpi-triggers-sub'),
    
    // KPIs
    kpiTotalScanned: document.getElementById('kpi-total-scanned'),
    kpiTotalTriggers: document.getElementById('kpi-total-triggers'),
    kpiActionableCount: document.getElementById('kpi-actionable-count'),
    kpiUnsuitableCount: document.getElementById('kpi-unsuitable-count'),
    kpiProCount: document.getElementById('kpi-pro-count'),
    
    // Chart Modal
    chartModal: document.getElementById('chart-modal'),
    btnCloseChartModal: document.getElementById('btn-close-chart-modal'),
    modalStockTitle: document.getElementById('modal-stock-title'),
    modalStockBadges: document.getElementById('modal-stock-badges'),
    modalStatsBar: document.getElementById('modal-stats-bar'),
    chartCanvas: document.getElementById('stock-chart-canvas'),
    legendEmaLabel: document.getElementById('legend-ema-label'),
    legendSecondaryPill: document.getElementById('legend-secondary-pill'),
    
    // Calc Modal
    calcModal: document.getElementById('calc-modal'),
    btnCloseCalcModal: document.getElementById('btn-close-calc-modal'),
    calcForm: document.getElementById('calc-form'),
    calcSymbol: document.getElementById('calc-symbol'),
    calcCapital: document.getElementById('calc-capital'),
    calcRiskPct: document.getElementById('calc-risk-pct'),
    calcEntryPrice: document.getElementById('calc-entry-price'),
    calcStopLoss: document.getElementById('calc-stop-loss'),
    calcTarget1: document.getElementById('calc-target1'),
    calcResults: document.getElementById('calc-results'),
    resMaxRisk: document.getElementById('res-max-risk'),
    resShares: document.getElementById('res-shares'),
    resTotalInvest: document.getElementById('res-total-invest'),
    resPortfolioPct: document.getElementById('res-portfolio-pct'),
    resProfitT1: document.getElementById('res-profit-t1'),
    resProfitT2: document.getElementById('res-profit-t2')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    fetchScanData(false);
    fetchMarketStatus();
});

// Fetch Live Market Status & Benchmark Indices (Nifty 50, India VIX)
async function fetchMarketStatus() {
    try {
        const resp = await fetch('/api/market-status');
        const data = await resp.json();
        if (data.status === 'success') {
            const niftyEl = document.getElementById('nifty-price');
            const niftyChgEl = document.getElementById('nifty-change');
            const vixEl = document.getElementById('vix-price');
            const vixChgEl = document.getElementById('vix-change');
            const mktStatusEl = document.getElementById('market-status-indicator');
            const lastDataTimeEl = document.getElementById('last-data-time');
            const regimeBadgeEl = document.getElementById('market-regime-badge');

            if (niftyEl && data.nifty.price) {
                niftyEl.textContent = '₹' + Number(data.nifty.price).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            }
            if (niftyChgEl && data.nifty.change_pct !== undefined) {
                const sign = data.nifty.change_pct >= 0 ? '+' : '';
                niftyChgEl.textContent = `${sign}${data.nifty.change_pct}%`;
                niftyChgEl.className = `pill-badge ${data.nifty.change_pct >= 0 ? 'badge-green' : 'badge-red'}`;
            }

            if (vixEl && data.vix.price) {
                vixEl.textContent = Number(data.vix.price).toFixed(2);
            }
            if (vixChgEl && data.vix.change_pct !== undefined) {
                const sign = data.vix.change_pct >= 0 ? '+' : '';
                vixChgEl.textContent = `${sign}${data.vix.change_pct}%`;
                vixChgEl.className = `pill-badge ${data.vix.price > 20 ? 'badge-red' : 'badge-green'}`;
            }

            if (mktStatusEl) {
                mktStatusEl.innerHTML = `<span class="pulse-dot ${data.is_open ? 'pulse-green' : 'pulse-amber'}"></span> ${data.market_status_text}`;
            }
            if (lastDataTimeEl && data.time_str) {
                lastDataTimeEl.textContent = data.time_str;
            }
            if (regimeBadgeEl && data.market_regime) {
                regimeBadgeEl.textContent = data.market_regime;
                regimeBadgeEl.className = `regime-badge ${data.regime_badge || 'badge-neutral'}`;
            }
        }
    } catch (e) {
        console.warn('Market status fetch:', e);
    }
}

function initEventListeners() {
    // Mode Switcher: Daily vs Intraday
    el.btnModeDaily.addEventListener('click', () => {
        if (state.mode === 'daily') return;
        setMode('daily');
    });

    el.btnModeIntraday.addEventListener('click', () => {
        if (state.mode === 'intraday') return;
        setMode('intraday');
    });

    el.btnModePortfolio.addEventListener('click', () => {
        if (state.mode === 'portfolio') return;
        setMode('portfolio');
    });

    if (el.btnRefreshPortfolio) {
        el.btnRefreshPortfolio.addEventListener('click', () => {
            fetchPortfolioData(true);
        });
    }

    initPortfolioManager();

    // Refresh Button
    el.btnRefresh.addEventListener('click', () => {
        fetchScanData(true);
    });

    // Auto-Refresh Momentum Universe (Dynamic Screener)
    const btnRefreshUniv = document.getElementById('btn-refresh-universe');
    if (btnRefreshUniv) {
        btnRefreshUniv.addEventListener('click', async () => {
            btnRefreshUniv.disabled = true;
            btnRefreshUniv.innerHTML = '<i class="fa-solid fa-spinner fa-spin text-cyan"></i> Discovering Leaders...';
            try {
                const resp = await fetch('/api/universe/refresh', { method: 'POST' });
                const res = await resp.json();
                showNotification(res.message || 'Auto-discovery started across NSE universe!', 'info');
                setTimeout(() => {
                    fetchScanData(true);
                    btnRefreshUniv.disabled = false;
                    btnRefreshUniv.innerHTML = '<i class="fa-solid fa-arrows-rotate text-cyan"></i> Auto-Refresh Momentum';
                }, 4000);
            } catch (err) {
                console.error(err);
                btnRefreshUniv.disabled = false;
                btnRefreshUniv.innerHTML = '<i class="fa-solid fa-arrows-rotate text-cyan"></i> Auto-Refresh Momentum';
            }
        });
    }

    // Export CSV
    el.btnExportCsv.addEventListener('click', () => {
        window.location.href = `/api/export_csv?mode=${state.mode}`;
    });

    // Search Input
    el.inputSearch.addEventListener('input', (e) => {
        state.searchQuery = e.target.value.trim().toLowerCase();
        renderSignals();
    });

    // Strategy Tabs (Core vs Enhanced Pro)
    el.strategyTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            el.strategyTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            state.activeTab = tab.dataset.tab;
            
            if (state.activeTab === 'enhanced') {
                el.enhancedExplainer.classList.remove('hidden');
            } else {
                el.enhancedExplainer.classList.add('hidden');
            }
            renderSignals();
        });
    });

    // Filter Pills
    el.filterPills.forEach(pill => {
        pill.addEventListener('click', () => {
            el.filterPills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            state.activeFilter = pill.dataset.filter;
            renderSignals();
        });
    });

    // Modal Close Buttons
    el.btnCloseChartModal.addEventListener('click', () => {
        el.chartModal.classList.add('hidden');
    });

    el.btnCloseCalcModal.addEventListener('click', () => {
        el.calcModal.classList.add('hidden');
    });

    // Close on overlay backdrop click
    window.addEventListener('click', (e) => {
        if (e.target === el.chartModal) el.chartModal.classList.add('hidden');
        if (e.target === el.calcModal) el.calcModal.classList.add('hidden');
    });

    // Position Calculator Form Submission
    el.calcForm.addEventListener('submit', (e) => {
        e.preventDefault();
        calculatePositionSizing();
    });
}

// Switch between Daily Swing, Intraday Momentum, and Pro Swing Portfolio modes
function setMode(newMode) {
    state.mode = newMode;

    if (newMode === 'portfolio') {
        el.btnModeDaily.classList.remove('active');
        el.btnModeIntraday.classList.remove('active');
        el.btnModePortfolio.classList.add('active');

        if (el.screenerView) el.screenerView.classList.add('hidden');
        if (el.portfolioView) el.portfolioView.classList.remove('hidden');
        el.headerStrategySubtitle.textContent = 'Pro Swing Trader Portfolio & Real-Time Technical Engine';

        fetchPortfolioData(false);
        return;
    }

    // Returning to screener modes
    el.btnModePortfolio.classList.remove('active');
    if (el.portfolioView) el.portfolioView.classList.add('hidden');
    if (el.screenerView) el.screenerView.classList.remove('hidden');

    if (newMode === 'daily') {
        el.btnModeDaily.classList.add('active');
        el.btnModeIntraday.classList.remove('active');
        
        el.headerStrategySubtitle.textContent = 'Daily 50 EMA + Supertrend (10, 3) Swing Screener';
        el.bannerModeVal.textContent = 'Daily Swing Trading';
        if (el.bannerSetupVal) el.bannerSetupVal.textContent = 'Price vs 50 EMA + Supertrend (10, 3) | Full Swing Lookback';
        el.tabCoreLabel.textContent = 'Core Swing Setup (50 EMA + Supertrend 10,3)';
        el.signalsHeading.textContent = 'Nifty 500 Market Cap Triggers (Daily Timeframe)';
        el.signalsDesc.textContent = 'Real-time scan across NSE Nifty 500 with actionable entry feasibility';
        el.loadingText.textContent = 'Scanning Nifty 500 Indian Stocks (Daily)...';
        el.kpiTriggersLabel.textContent = 'Swing Crossovers';
        el.kpiTriggersSub.textContent = 'Swing triggers found';
        el.calcRiskPct.value = '1.0';
    } else {
        el.btnModeDaily.classList.remove('active');
        el.btnModeIntraday.classList.add('active');
        
        el.headerStrategySubtitle.textContent = 'Intraday 200 EMA + Supertrend (10, 3) Momentum Screener';
        el.bannerModeVal.textContent = 'Intraday Momentum Trading';
        if (el.bannerSetupVal) el.bannerSetupVal.textContent = 'Intraday 15m Price vs 200 EMA + Supertrend (10, 3)';
        el.tabCoreLabel.textContent = 'Core Intraday Setup (200 EMA + Supertrend 10,3 - 15m)';
        el.signalsHeading.textContent = 'Nifty 500 Market Cap Intraday Triggers (15m Candles)';
        el.signalsDesc.textContent = 'Live intraday session triggers with 200 EMA breakout and suitability analysis';
        el.loadingText.textContent = 'Scanning Nifty 500 Indian Stocks (15m Intraday)...';
        el.kpiTriggersLabel.textContent = 'Intraday Triggers';
        el.kpiTriggersSub.textContent = 'Recent 15m bar breakouts';
        el.calcRiskPct.value = '0.5';
    }

    fetchScanData(false);
}

// Fetch Screener Data from API
async function fetchScanData(forceRefresh = false) {
    state.isLoading = true;
    el.loadingSpinner.classList.remove('hidden');
    if (!state.signals || state.signals.length === 0) {
        el.signalsContainer.innerHTML = '';
    }
    el.emptyState.classList.add('hidden');
    el.btnRefresh.disabled = true;
    el.btnRefresh.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Scanning...';

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 20000);
        const url = `/api/scan?mode=${state.mode}&refresh=${forceRefresh}`;
        const resp = await fetch(url, { signal: controller.signal });
        clearTimeout(timeoutId);
        const data = await resp.json();

        state.signals = data.signals || [];
        state.summary = data.summary || {};

        // Update KPIs
        el.kpiTotalScanned.textContent = data.total_scanned_stocks || '500';
        el.kpiTotalTriggers.textContent = data.total_triggers_found || '0';
        el.kpiActionableCount.textContent = (state.summary.actionable_buys || 0) + (state.summary.actionable_sells || 0);
        el.kpiUnsuitableCount.textContent = state.summary.not_suitable || '0';
        el.kpiProCount.textContent = state.summary.pro_enhanced_picks || '0';

        renderSignals();

        // If background worker is currently updating, show indicator without auto-refresh loop
        if (data.is_updating) {
            el.btnRefresh.innerHTML = '<i class="fa-solid fa-circle-notch text-cyan"></i> Scan Updating (Click to Reload)';
        }
    } catch (err) {
        console.error('Scan Error:', err);
        if (!state.signals || state.signals.length === 0) {
            el.signalsContainer.innerHTML = `<div class="empty-container"><i class="fa-solid fa-triangle-exclamation empty-icon text-red"></i><div class="empty-title">Failed to fetch market data</div><div class="empty-desc">${err.message}</div></div>`;
        } else if (typeof showNotification === 'function') {
            showNotification('Network delay: displayed last cached scan.', 'warning');
        }
    } finally {
        state.isLoading = false;
        el.loadingSpinner.classList.add('hidden');
        el.btnRefresh.disabled = false;
        el.btnRefresh.innerHTML = '<i class="fa-solid fa-rotate"></i> Refresh Scan';
    }
}

// Render Signals List / Cards
function renderSignals() {

    let filtered = [...state.signals];

    // Defensive deduplication by symbol: exactly 1 card per stock
    const seenSymbols = new Set();
    filtered = filtered.filter(s => {
        if (!s.symbol || seenSymbols.has(s.symbol)) return false;
        seenSymbols.add(s.symbol);
        return true;
    });

    // Filter by Strategy Tab (Enhanced Pro vs Core)
    if (state.activeTab === 'enhanced') {
        filtered = filtered.filter(s => s.enhanced_option.vol_confirmed);
    }

    // Filter by Filter Pill
    if (state.activeFilter === 'actionable') {
        filtered = filtered.filter(s => s.is_actionable);
    } else if (state.activeFilter === 'not_suitable') {
        filtered = filtered.filter(s => !s.is_actionable);
    } else if (state.activeFilter === 'BUY') {
        filtered = filtered.filter(s => s.signal_type === 'BUY');
    } else if (state.activeFilter === 'SELL') {
        filtered = filtered.filter(s => s.signal_type === 'SELL');
    }

    // Filter by Search Query
    if (state.searchQuery) {
        filtered = filtered.filter(s => 
            s.symbol.toLowerCase().includes(state.searchQuery) ||
            s.name.toLowerCase().includes(state.searchQuery) ||
            s.sector.toLowerCase().includes(state.searchQuery)
        );
    }

    el.signalsContainer.innerHTML = '';

    if (filtered.length === 0) {
        el.emptyState.classList.remove('hidden');
        return;
    }
    el.emptyState.classList.add('hidden');

    filtered.forEach(s => {
        const card = createSignalCard(s);
        el.signalsContainer.appendChild(card);
    });
}

// Create a Single Signal Card Component
function createSignalCard(s) {
    const card = document.createElement('div');
    const isActionable = s.is_actionable;
    const isOverextended = s.suitability.includes('OVEREXTENDED') || s.suitability.includes('OVER-DUMPED');
    const isInvalidated = s.suitability.includes('INVALIDATED') || s.suitability.includes('BREAKDOWN');
    
    card.className = `signal-card ${isActionable ? 'signal-card-actionable' : (isOverextended ? 'signal-card-overextended' : 'signal-card-invalidated')}`;
    if (s.enhanced_option && s.enhanced_option.vol_confirmed) {
        card.classList.add('signal-card-pro');
    }

    const isBuy = s.signal_type === 'BUY';
    const pctChangeColor = s.pct_from_trigger >= 0 ? 'text-green' : 'text-red';
    const pctChangeSign = s.pct_from_trigger > 0 ? '+' : '';

    // Age / Time Badge
    let ageBadge = '';
    if (state.mode === 'daily') {
        if (s.days_ago === 0) {
            ageBadge = '<span class="badge badge-success"><span class="pulse-dot"></span> TODAY (FRESH)</span>';
        } else if (s.days_ago === 1) {
            ageBadge = '<span class="badge badge-secondary">1 DAY AGO</span>';
        } else {
            ageBadge = `<span class="badge badge-secondary">${s.days_ago} DAYS AGO</span>`;
        }
    } else {
        // Intraday (Bars / Minutes)
        if (s.bars_ago <= 1) {
            ageBadge = '<span class="badge badge-success"><span class="pulse-dot"></span> LIVE / JUST NOW</span>';
        } else if (s.bars_ago <= 4) {
            ageBadge = `<span class="badge badge-secondary">${s.bars_ago * 15} MINS AGO</span>`;
        } else {
            ageBadge = `<span class="badge badge-secondary">${s.days_ago}h AGO (${s.bars_ago} bars)</span>`;
        }
    }

    // Suitability Verdict Badge
    let verdictBadge = '';
    if (isActionable) {
        verdictBadge = `<span class="badge badge-success"><i class="fa-solid fa-circle-check"></i> ${s.suitability}</span>`;
    } else if (isOverextended) {
        verdictBadge = `<span class="badge badge-warning"><i class="fa-solid fa-triangle-exclamation"></i> ${s.suitability}</span>`;
    } else if (isInvalidated) {
        verdictBadge = `<span class="badge badge-danger"><i class="fa-solid fa-ban"></i> ${s.suitability}</span>`;
    } else {
        verdictBadge = `<span class="badge badge-amber"><i class="fa-solid fa-shield"></i> ${s.suitability}</span>`;
    }

    const proScoreBadge = s.confidence_label ? 
        `<span class="badge badge-pro"><i class="fa-solid fa-gauge-high"></i> ${s.confidence_label}</span>` :
        `<span class="badge badge-pro"><i class="fa-solid fa-crown"></i> PRO SCORE ${s.enhanced_option.pro_score}</span>`;

    card.innerHTML = `
        <div class="card-top-row">
            <div class="stock-identity">
                <span class="stock-symbol">${s.symbol}</span>
                <div>
                    <div class="stock-name">${s.name}</div>
                    <span class="stock-sector">${s.sector}</span>
                </div>
            </div>
            <div class="card-status-badges">
                <span class="badge ${isBuy ? 'badge-success' : 'badge-danger'}">
                    <i class="fa-solid ${isBuy ? 'fa-arrow-trend-up' : 'fa-arrow-trend-down'}"></i> ${s.signal_type}
                </span>
                ${ageBadge}
                ${verdictBadge}
                ${proScoreBadge}
            </div>
        </div>

        <div class="metrics-strip">
            <div class="m-item">
                <span class="m-label">Current Price</span>
                <span class="m-val">₹${s.current_price.toLocaleString('en-IN', {minimumFractionDigits: 2})}</span>
            </div>
            <div class="m-item">
                <span class="m-label">Trigger Price</span>
                <span class="m-val">₹${s.trigger_price.toLocaleString('en-IN', {minimumFractionDigits: 2})}</span>
            </div>
            <div class="m-item">
                <span class="m-label">Move Since Trigger</span>
                <span class="m-val ${pctChangeColor}">${pctChangeSign}${s.pct_from_trigger.toFixed(2)}%</span>
            </div>
            <div class="m-item">
                <span class="m-label">${s.main_ema_name}</span>
                <span class="m-val" style="color: var(--accent-cyan)">₹${s.main_ema.toLocaleString('en-IN', {minimumFractionDigits: 2})}</span>
            </div>
            <div class="m-item">
                <span class="m-label">Supertrend (10,3)</span>
                <span class="m-val" style="color: ${s.supertrend_direction.includes('Bullish') ? 'var(--bullish-green)' : 'var(--bearish-red)'}">
                    ₹${s.supertrend.toLocaleString('en-IN', {minimumFractionDigits: 2})}
                </span>
            </div>
            <div class="m-item">
                <span class="m-label">Stop-Loss (Supertrend)</span>
                <span class="m-val text-red">₹${s.stop_loss.toLocaleString('en-IN', {minimumFractionDigits: 2})} (-${s.risk_pct}%)</span>
                <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:2px;">
                    <span style="color:var(--accent-gold); font-weight:700;"><i class="fa-solid fa-shield-halved"></i> 5% Rule SL:</span>
                    <strong style="color:#fff;">₹${(s.sl_5pct || (s.current_price * 0.95)).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</strong>
                </div>
            </div>
            <div class="m-item">
                <span class="m-label">Target 1 (1:1.5)</span>
                <span class="m-val text-green">₹${s.target1.toLocaleString('en-IN', {minimumFractionDigits: 2})}</span>
            </div>
            <div class="m-item">
                <span class="m-label">Target 2 (1:2.5)</span>
                <span class="m-val text-green">₹${s.target2.toLocaleString('en-IN', {minimumFractionDigits: 2})}</span>
            </div>
            ${s.target3 ? `
            <div class="m-item">
                <span class="m-label">Target 3 (4R)</span>
                <span class="m-val text-green">₹${s.target3.toLocaleString('en-IN', {minimumFractionDigits: 2})}</span>
            </div>` : ''}
        </div>

        <div class="card-analysis-row">
            <div class="analysis-reason">
                <i class="fa-solid fa-circle-info" style="color: var(--accent-cyan); margin-top: 2px;"></i>
                <span><strong>Algo Diagnosis:</strong> ${s.reasons.join(' | ')}</span>
            </div>
            <div class="analysis-action-plan">
                <i class="fa-solid fa-bullseye" style="color: var(--bullish-green); margin-top: 2px;"></i>
                <span><strong>Action Plan:</strong> ${s.action_plan}</span>
            </div>
        </div>

        <div class="card-actions-row">
            <div class="card-extra-pills">
                <span><i class="fa-solid fa-clock"></i> ${state.mode === 'daily' ? 'Trigger Date:' : 'Trigger Bar:'} <strong>${s.trigger_date}</strong></span>
                <span>&bull;</span>
                <span>Timeframe: <strong>${s.timeframe}</strong></span>
                <span>&bull;</span>
                <span>RSI: <strong>${s.rsi14}</strong></span>
                <span>&bull;</span>
                <span>Vol Ratio: <strong>${s.volume_ratio}x</strong></span>
                ${s.adx14 ? `<span>&bull;</span><span>ADX: <strong>${s.adx14}</strong></span>` : ''}
                ${s.macd_hist !== undefined ? `<span>&bull;</span><span>MACD: <strong>${s.macd_hist > 0 ? '+' : ''}${s.macd_hist}</strong></span>` : ''}
                ${s.roc20 !== undefined ? `<span>&bull;</span><span>ROC20: <strong>${s.roc20 > 0 ? '+' : ''}${s.roc20}%</strong></span>` : ''}
            </div>

            <div class="card-btn-group">
                <button class="btn btn-secondary btn-sm btn-chart" data-symbol="${s.symbol}">
                    <i class="fa-solid fa-chart-candlestick"></i> View ${state.mode === 'daily' ? 'Daily' : '15m'} Chart
                </button>
                <button class="btn btn-primary btn-sm btn-calc" 
                    data-symbol="${s.symbol}" 
                    data-price="${s.current_price}" 
                    data-sl="${s.stop_loss}" 
                    data-t1="${s.target1}">
                    <i class="fa-solid fa-calculator"></i> Size Position
                </button>
            </div>
        </div>
    `;

    // Bind Button Clicks
    card.querySelector('.btn-chart').addEventListener('click', () => {
        openChartModal(s);
    });

    card.querySelector('.btn-calc').addEventListener('click', (e) => {
        const btn = e.currentTarget;
        openCalcModal(
            btn.dataset.symbol,
            btn.dataset.price,
            btn.dataset.sl,
            btn.dataset.t1
        );
    });

    return card;
}

// Open Interactive Candlestick Chart Modal
async function openChartModal(input) {
    let sym = '';
    let s = null;

    if (typeof input === 'string') {
        sym = input.trim().toUpperCase();
        s = portfolioState.holdings.find(h => h.symbol === sym) ||
            portfolioState.watchlist.find(w => w.symbol === sym) ||
            { symbol: sym, name: sym };
    } else if (input && typeof input === 'object') {
        s = input;
        sym = (s.symbol || '').toUpperCase();
    }

    if (!sym) return;

    // Use daily mode if in portfolio view, else respect active screener mode
    const chartMode = (state.mode === 'intraday') ? 'intraday' : 'daily';
    const isIntraday = chartMode === 'intraday';

    // Header & Badges
    const stockName = s.name || sym;
    const tfLabel = isIntraday ? '15m Intraday' : 'Daily Candlesticks';
    el.modalStockTitle.textContent = `${sym} - ${stockName} (${tfLabel})`;

    const signalBadge = s.signal_type ? 
        `<span class="badge ${s.signal_type === 'BUY' ? 'badge-success' : 'badge-danger'}">${s.signal_type}</span>` :
        (s.exit_verdict ? `<span class="badge badge-${s.verdict_badge || 'success'}">${s.exit_verdict}</span>` : '');

    const ageBadge = s.days_ago !== undefined ?
        `<span class="badge badge-secondary">${isIntraday ? `${s.days_ago}h ago` : `${s.days_ago}d ago`}</span>` :
        (s.hold_days !== undefined ? `<span class="badge badge-secondary">Hold: ${s.hold_days}d</span>` : '');

    const suitBadge = s.suitability ?
        `<span class="badge ${s.is_actionable ? 'badge-success' : 'badge-warning'}">${s.suitability}</span>` : '';

    el.modalStockBadges.innerHTML = `${signalBadge} ${ageBadge} ${suitBadge}`;

    // Stats bar
    const cmp = s.current_price || '--';
    const mainEmaName = isIntraday ? '200 EMA' : '50 EMA';
    const mainEmaVal = s.main_ema || s.ema50 || '--';
    const stVal = s.supertrend || '--';
    const isBull = s.supertrend_dir === 1 || s.signal_type === 'BUY';
    const stColor = isBull ? 'var(--bullish-green)' : 'var(--bearish-red)';
    const slVal = s.trailing_sl || s.suggested_sl || s.stop_loss || '--';
    const t1Val = s.target_price_action_high || s.target1 || '--';

    el.modalStatsBar.innerHTML = `
        <span>CMP: <strong>₹${cmp}</strong></span>
        <span>${mainEmaName}: <strong style="color: var(--accent-cyan)">₹${mainEmaVal}</strong></span>
        <span>Supertrend: <strong style="color: ${stColor}">₹${stVal}</strong></span>
        <span>Stop-Loss: <strong class="text-red">₹${slVal}</strong></span>
        <span>Target: <strong class="text-green">₹${t1Val}</strong></span>
    `;

    // Legend adjustments
    if (!isIntraday) {
        el.legendEmaLabel.textContent = '50 EMA';
        if (state.mode === 'portfolio') {
            el.legendSecondaryPill.classList.add('hidden');
        } else {
            el.legendSecondaryPill.classList.remove('hidden');
        }
    } else {
        el.legendEmaLabel.textContent = '200 EMA (Intraday)';
        el.legendSecondaryPill.classList.add('hidden');
    }

    el.chartModal.classList.remove('hidden');

    try {
        const resp = await fetch(`/api/stock/${sym}?mode=${chartMode}`);
        const chartData = await resp.json();
        if (chartData.error) {
            console.error('Failed to load chart data:', chartData.error);
            return;
        }
        state.currentChartData = chartData;

        const chartSignal = {
            stop_loss: parseFloat(slVal) || null,
            target1: parseFloat(t1Val) || null,
            ...s
        };

        renderCandlestickChart(chartData, chartSignal);
    } catch (err) {
        console.error('Failed to load chart data:', err);
    }
}

// Render High-Resolution Candlestick Chart on Canvas
function renderCandlestickChart(chartData, signalInfo) {
    const canvas = el.chartCanvas;
    const ctx = canvas.getContext('2d');

    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;

    // Background
    ctx.fillStyle = '#090d16';
    ctx.fillRect(0, 0, w, h);

    const candles = chartData.candles || [];
    if (candles.length === 0) return;

    // Show last 65 candles for high clarity
    const visibleCandles = candles.slice(-65);
    const n = visibleCandles.length;

    let minPrice = Infinity;
    let maxPrice = -Infinity;

    visibleCandles.forEach(c => {
        if (c.low < minPrice) minPrice = c.low;
        if (c.high > maxPrice) maxPrice = c.high;
    });

    if (signalInfo && signalInfo.stop_loss && signalInfo.stop_loss < minPrice) minPrice = signalInfo.stop_loss * 0.99;
    if (signalInfo && signalInfo.target1 && signalInfo.target1 > maxPrice) maxPrice = signalInfo.target1 * 1.01;

    const padPrice = (maxPrice - minPrice) * 0.08;
    minPrice -= padPrice;
    maxPrice += padPrice;
    const priceRange = maxPrice - minPrice;

    const paddingLeft = 15;
    const paddingRight = 80;
    const paddingTop = 20;
    const paddingBottom = 30;

    const plotW = w - paddingLeft - paddingRight;
    const plotH = h - paddingTop - paddingBottom;

    const priceToY = (p) => paddingTop + plotH - ((p - minPrice) / priceRange) * plotH;
    const candleW = Math.max(2, (plotW / n) * 0.7);
    const stepX = plotW / n;

    // Grid Lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    ctx.fillStyle = '#64748b';
    ctx.font = '10px JetBrains Mono';
    ctx.textAlign = 'left';

    const numGridLines = 6;
    for (let i = 0; i <= numGridLines; i++) {
        const gridPrice = minPrice + (priceRange / numGridLines) * i;
        const y = priceToY(gridPrice);
        ctx.beginPath();
        ctx.moveTo(paddingLeft, y);
        ctx.lineTo(w - paddingRight, y);
        ctx.stroke();

        ctx.fillText('₹' + gridPrice.toFixed(1), w - paddingRight + 8, y + 3);
    }

    const timeToXMap = {};
    visibleCandles.forEach((c, idx) => {
        timeToXMap[c.time] = paddingLeft + (idx + 0.5) * stepX;
    });

    // Secondary EMA (200 EMA on daily screener; hidden in portfolio view for pure 50 EMA focus)
    if (chartData.secondary_ema && chartData.secondary_ema.length > 0 && state.mode !== 'portfolio') {
        ctx.beginPath();
        ctx.strokeStyle = '#8b5cf6';
        ctx.lineWidth = 1.5;
        let started = false;
        chartData.secondary_ema.forEach(p => {
            if (timeToXMap[p.time] !== undefined) {
                const x = timeToXMap[p.time];
                const y = priceToY(p.value);
                if (!started) { ctx.moveTo(x, y); started = true; }
                else { ctx.lineTo(x, y); }
            }
        });
        ctx.stroke();
    }

    // Main EMA (50 EMA for Daily or 200 EMA for Intraday)
    if (chartData.main_ema) {
        ctx.beginPath();
        ctx.strokeStyle = '#06b6d4';
        ctx.lineWidth = 2.0;
        let started = false;
        chartData.main_ema.forEach(p => {
            if (timeToXMap[p.time] !== undefined) {
                const x = timeToXMap[p.time];
                const y = priceToY(p.value);
                if (!started) { ctx.moveTo(x, y); started = true; }
                else { ctx.lineTo(x, y); }
            }
        });
        ctx.stroke();
    }

    // Supertrend Stepped Lines
    if (chartData.supertrend) {
        ctx.lineWidth = 2.0;
        let prevPoint = null;
        chartData.supertrend.forEach(p => {
            if (timeToXMap[p.time] !== undefined) {
                const x = timeToXMap[p.time];
                const y = priceToY(p.value);
                if (prevPoint) {
                    ctx.beginPath();
                    ctx.strokeStyle = p.color;
                    ctx.moveTo(prevPoint.x, prevPoint.y);
                    ctx.lineTo(x, y);
                    ctx.stroke();
                }
                prevPoint = { x, y };
            }
        });
    }

    // Draw Candlesticks
    visibleCandles.forEach((c, idx) => {
        const x = paddingLeft + (idx + 0.5) * stepX;
        const openY = priceToY(c.open);
        const closeY = priceToY(c.close);
        const highY = priceToY(c.high);
        const lowY = priceToY(c.low);

        const isGreen = c.close >= c.open;
        const candleColor = isGreen ? '#10b981' : '#f43f5e';

        // High-Low Wick
        ctx.beginPath();
        ctx.strokeStyle = candleColor;
        ctx.lineWidth = 1.2;
        ctx.moveTo(x, highY);
        ctx.lineTo(x, lowY);
        ctx.stroke();

        // Real Body
        ctx.fillStyle = candleColor;
        const bodyY = Math.min(openY, closeY);
        const bodyH = Math.max(Math.abs(closeY - openY), 1.5);
        ctx.fillRect(x - candleW / 2, bodyY, candleW, bodyH);

        // Date / Time labels on X-axis (every 10 candles)
        if (idx % 10 === 0 || idx === n - 1) {
            ctx.fillStyle = '#64748b';
            ctx.font = '9px JetBrains Mono';
            ctx.textAlign = 'center';
            const label = state.mode === 'daily' ? c.time.slice(5) : c.time.slice(11, 16);
            ctx.fillText(label, x, h - 10);
        }
    });

    // Horizontal Stop-Loss Line (Dashed Red)
    if (signalInfo.stop_loss) {
        const slY = priceToY(signalInfo.stop_loss);
        ctx.save();
        ctx.setLineDash([5, 4]);
        ctx.strokeStyle = '#ef4444';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(paddingLeft, slY);
        ctx.lineTo(w - paddingRight, slY);
        ctx.stroke();
        ctx.fillStyle = '#ef4444';
        ctx.font = '10px JetBrains Mono';
        ctx.textAlign = 'left';
        ctx.fillText(`SL: ₹${signalInfo.stop_loss}`, w - paddingRight + 8, slY + 3);
        ctx.restore();
    }

    // Horizontal Target 1 Line (Dashed Green)
    if (signalInfo.target1) {
        const t1Y = priceToY(signalInfo.target1);
        ctx.save();
        ctx.setLineDash([5, 4]);
        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(paddingLeft, t1Y);
        ctx.lineTo(w - paddingRight, t1Y);
        ctx.stroke();
        ctx.fillStyle = '#10b981';
        ctx.font = '10px JetBrains Mono';
        ctx.textAlign = 'left';
        ctx.fillText(`T1: ₹${signalInfo.target1}`, w - paddingRight + 8, t1Y + 3);
        ctx.restore();
    }
}

// Open Position Sizing Calculator Modal
function openCalcModal(symbol, price, sl, t1) {
    el.calcSymbol.value = symbol;
    el.calcEntryPrice.value = parseFloat(price).toFixed(2);
    el.calcStopLoss.value = parseFloat(sl).toFixed(2);
    el.calcTarget1.value = parseFloat(t1 || (parseFloat(price) * 1.03)).toFixed(2);
    el.calcResults.classList.add('hidden');
    el.calcModal.classList.remove('hidden');

    calculatePositionSizing();
}

// Calculate Position Sizing
async function calculatePositionSizing() {
    const capital = parseFloat(el.calcCapital.value) || 200000;
    const riskPct = parseFloat(el.calcRiskPct.value) || 1.0;
    const entryPrice = parseFloat(el.calcEntryPrice.value) || 0;
    const stopLoss = parseFloat(el.calcStopLoss.value) || 0;

    if (entryPrice <= 0 || stopLoss <= 0) return;

    try {
        const resp = await fetch('/api/calculate_position', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                capital: capital,
                risk_pct: riskPct,
                entry_price: entryPrice,
                stop_loss: stopLoss
            })
        });

        const res = await resp.json();
        if (res.error) {
            alert(res.error);
            return;
        }

        el.resMaxRisk.textContent = `₹${res.max_risk_amount.toLocaleString('en-IN')}`;
        el.resShares.textContent = `${res.shares_to_buy.toLocaleString('en-IN')} Shares`;
        el.resTotalInvest.textContent = `₹${res.total_investment.toLocaleString('en-IN')}`;
        el.resPortfolioPct.textContent = `${res.portfolio_allocation_pct}% of Capital`;
        el.resProfitT1.textContent = `+₹${res.profit_target1.toLocaleString('en-IN')}`;
        el.resProfitT2.textContent = `+₹${res.profit_target2.toLocaleString('en-IN')}`;

        el.calcResults.classList.remove('hidden');
    } catch (err) {
        console.error('Calculation error:', err);
    }
}

// ==============================================================================
// PRO SWING TRADER PORTFOLIO & REAL-TIME ANALYZER CONTROLLER
// ==============================================================================

const portfolioState = {
    holdings: [],
    watchlist: [],
    history: [],
    summary: {},
    history_stats: {},
    activeSubtab: 'holdings',
    addType: 'watchlist',
    pendingConfirmAction: null,
    allPortfolios: [],
    activePortfolioId: 'default',
    activePortfolioName: 'Main Swing Portfolio'
};

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function initPortfolioManager() {
    const segBtnWatchlist = document.getElementById('seg-btn-watchlist');
    const segBtnHolding = document.getElementById('seg-btn-holding');
    const holdingFields = document.getElementById('holding-fields');
    const watchlistFields = document.getElementById('watchlist-fields');
    const btnAddText = document.getElementById('btn-add-text');
    const pForm = document.getElementById('portfolio-add-form');
    const inputSymbol = document.getElementById('input-p-symbol');
    const btnQuickAnalyze = document.getElementById('btn-quick-analyze');
    const quickChips = document.querySelectorAll('#quick-stock-chips .chip');
    const btnToggleRules = document.getElementById('btn-toggle-pro-rules');
    const proRulesContent = document.getElementById('pro-rules-content');
    const toggleRulesText = document.getElementById('toggle-rules-text');

    // Subtabs buttons
    const subtabBtns = document.querySelectorAll('.p-subtab');

    // Set today's date as default in buy date input
    const inputBuyDate = document.getElementById('input-p-buydate');
    if (inputBuyDate) {
        inputBuyDate.value = new Date().toISOString().split('T')[0];
    }

    // Uppercase symbol input automatically
    if (inputSymbol) {
        inputSymbol.addEventListener('input', (e) => {
            e.target.value = e.target.value.toUpperCase().trim();
        });
    }

    // Segmented toggle: Watchlist vs Holding
    if (segBtnWatchlist && segBtnHolding) {
        segBtnWatchlist.addEventListener('click', () => {
            portfolioState.addType = 'watchlist';
            segBtnWatchlist.classList.add('active');
            segBtnHolding.classList.remove('active');
            watchlistFields.classList.remove('hidden');
            holdingFields.classList.add('hidden');
            btnAddText.textContent = 'Add to Watchlist';
        });

        segBtnHolding.addEventListener('click', () => {
            portfolioState.addType = 'holding';
            segBtnHolding.classList.add('active');
            segBtnWatchlist.classList.remove('active');
            holdingFields.classList.remove('hidden');
            watchlistFields.classList.add('hidden');
            btnAddText.textContent = 'Add to Portfolio Holdings';
        });
    }

    // Quick stock chips click
    quickChips.forEach(chip => {
        chip.addEventListener('click', () => {
            if (inputSymbol) {
                inputSymbol.value = chip.dataset.sym;
                runQuickAnalysis();
            }
        });
    });

    // Quick live analysis button
    if (btnQuickAnalyze) {
        btnQuickAnalyze.addEventListener('click', () => {
            runQuickAnalysis();
        });
    }

    // Form submit: Add stock
    if (pForm) {
        pForm.addEventListener('submit', handlePortfolioAdd);
    }

    // Toggle Pro Rules
    if (btnToggleRules && proRulesContent) {
        btnToggleRules.addEventListener('click', () => {
            const isHidden = proRulesContent.classList.contains('hidden');
            if (isHidden) {
                proRulesContent.classList.remove('hidden');
                toggleRulesText.textContent = 'Hide Rules';
            } else {
                proRulesContent.classList.add('hidden');
                toggleRulesText.textContent = 'View Rules';
            }
        });
    }

    // Subtabs Navigation
    subtabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            subtabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const target = btn.dataset.target;
            portfolioState.activeSubtab = target;

            const elHoldings = document.getElementById('tab-content-holdings');
            const elAllocation = document.getElementById('tab-content-allocation');
            const elAladdin = document.getElementById('tab-content-aladdin');
            const elWatchlist = document.getElementById('tab-content-watchlist');
            const elHistory = document.getElementById('tab-content-history');

            if (elHoldings) elHoldings.classList.toggle('hidden', target !== 'holdings');
            if (elAllocation) {
                elAllocation.classList.toggle('hidden', target !== 'allocation');
                if (target === 'allocation') renderAllocationBreakdown();
            }
            if (elAladdin) elAladdin.classList.toggle('hidden', target !== 'aladdin');
            if (elWatchlist) elWatchlist.classList.toggle('hidden', target !== 'watchlist');
            if (elHistory) elHistory.classList.toggle('hidden', target !== 'history');
        });
    });

    const btnOpenAladdin = document.getElementById('btn-view-aladdin-matrix');
    if (btnOpenAladdin) {
        btnOpenAladdin.addEventListener('click', () => {
            const subtabAladdin = document.getElementById('subtab-aladdin');
            if (subtabAladdin) {
                subtabAladdin.click();
                subtabAladdin.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }

    // Modals setup
    initPortfolioModals();
}

function initPortfolioModals() {
    // Edit Modal close & cancel
    const btnCloseEdit = document.getElementById('btn-close-edit-modal');
    const btnCancelEdit = document.getElementById('btn-cancel-edit');
    const editModal = document.getElementById('edit-item-modal');
    const editForm = document.getElementById('edit-item-form');

    if (btnCloseEdit) btnCloseEdit.addEventListener('click', () => editModal.classList.add('hidden'));
    if (btnCancelEdit) btnCancelEdit.addEventListener('click', () => editModal.classList.add('hidden'));
    if (editForm) editForm.addEventListener('submit', handleSaveEdit);

    // Close/Exit Trade Modal
    const btnCloseExit = document.getElementById('btn-close-exit-modal');
    const btnCancelExit = document.getElementById('btn-cancel-exit');
    const exitModal = document.getElementById('close-trade-modal');
    const exitForm = document.getElementById('close-trade-form');
    const inputExitPrice = document.getElementById('input-exit-price');
    const modalCreateP = document.getElementById('create-portfolio-modal');
    const modalPSettings = document.getElementById('portfolio-settings-modal');

    if (btnCloseExit) btnCloseExit.addEventListener('click', () => exitModal.classList.add('hidden'));
    if (btnCancelExit) btnCancelExit.addEventListener('click', () => exitModal.classList.add('hidden'));
    if (exitForm) exitForm.addEventListener('submit', handleConfirmExitTrade);

    if (inputExitPrice) {
        inputExitPrice.addEventListener('input', updateExitPnlPreview);
    }

    const inputExitShares = document.getElementById('input-exit-shares');
    if (inputExitShares) {
        inputExitShares.addEventListener('input', updateExitPnlPreview);
    }

    const inputExitDate = document.getElementById('input-exit-date');
    if (inputExitDate) {
        inputExitDate.addEventListener('change', () => {
            const id = document.getElementById('exit-item-id').value;
            const holding = portfolioState.holdings.find(h => h.id === id);
            if (holding && holding.buy_date && inputExitDate.value) {
                const diffTime = new Date(inputExitDate.value) - new Date(holding.buy_date);
                const diffDays = Math.max(0, Math.floor(diffTime / (1000 * 60 * 60 * 24)));
                const holdDaysInput = document.getElementById('input-exit-hold-days');
                if (holdDaysInput) holdDaysInput.value = diffDays;
            }
        });
    }

    // Confirm Modal
    const btnCloseConfirm = document.getElementById('btn-close-confirm-modal');
    const btnCancelConfirm = document.getElementById('btn-confirm-cancel');
    const btnProceedConfirm = document.getElementById('btn-confirm-proceed');
    const confirmModalEl = document.getElementById('confirm-modal');

    if (btnCloseConfirm) btnCloseConfirm.addEventListener('click', () => confirmModalEl && confirmModalEl.classList.add('hidden'));
    if (btnCancelConfirm) btnCancelConfirm.addEventListener('click', () => confirmModalEl && confirmModalEl.classList.add('hidden'));
    if (btnProceedConfirm) {
        btnProceedConfirm.addEventListener('click', () => {
            if (confirmModalEl) confirmModalEl.classList.add('hidden');
            if (typeof portfolioState.pendingConfirmAction === 'function') {
                portfolioState.pendingConfirmAction();
                portfolioState.pendingConfirmAction = null;
            }
        });
    }

    // Global functions for inline onclick bindings
    window.openCreatePortfolioModal = function() {
        const modal = document.getElementById('create-portfolio-modal');
        const inputName = document.getElementById('input-new-p-name');
        if (modal) {
            if (inputName) inputName.value = '';
            modal.classList.remove('hidden');
            if (inputName) setTimeout(() => inputName.focus(), 50);
        }
    };

    window.closeCreatePortfolioModal = function() {
        const modal = document.getElementById('create-portfolio-modal');
        if (modal) modal.classList.add('hidden');
    };

    window.openPortfolioSettingsModal = function() {
        const modal = document.getElementById('portfolio-settings-modal');
        const currentP = portfolioState.allPortfolios.find(p => p.id === portfolioState.activePortfolioId);
        const settingsPId = document.getElementById('settings-p-id');
        const inputName = document.getElementById('input-settings-p-name');
        const inputCap = document.getElementById('input-settings-p-capital');
        const inputRisk = document.getElementById('input-settings-p-risk');

        if (settingsPId) settingsPId.value = portfolioState.activePortfolioId;
        if (inputName) inputName.value = currentP ? currentP.name : (portfolioState.activePortfolioName || '');
        if (inputCap) inputCap.value = currentP ? currentP.total_capital : 500000;
        if (inputRisk) inputRisk.value = currentP ? currentP.max_risk_per_trade_pct : 1.0;

        if (modal) modal.classList.remove('hidden');
    };

    window.closePortfolioSettingsModal = function() {
        const modal = document.getElementById('portfolio-settings-modal');
        if (modal) modal.classList.add('hidden');
    };

    // Create Portfolio Modal Elements
    const btnOpenCreateP = document.getElementById('btn-create-portfolio');
    const btnCloseCreateP = document.getElementById('btn-close-create-pmodal');
    const btnCancelCreateP = document.getElementById('btn-cancel-create-p');
    const formCreateP = document.getElementById('create-portfolio-form');
    const inputNewPName = document.getElementById('input-new-p-name');
    const inputNewPCapital = document.getElementById('input-new-p-capital');
    const inputNewPRisk = document.getElementById('input-new-p-risk');

    if (btnOpenCreateP) {
        btnOpenCreateP.addEventListener('click', window.openCreatePortfolioModal);
    }
    if (btnCloseCreateP) {
        btnCloseCreateP.addEventListener('click', window.closeCreatePortfolioModal);
    }
    if (btnCancelCreateP) {
        btnCancelCreateP.addEventListener('click', window.closeCreatePortfolioModal);
    }
    window.handleCreatePortfolioSubmit = async function(e) {
        if (e) e.preventDefault();
        const inputNewPName = document.getElementById('input-new-p-name');
        const inputNewPCapital = document.getElementById('input-new-p-capital');
        const inputNewPRisk = document.getElementById('input-new-p-risk');
        const modalCreateP = document.getElementById('create-portfolio-modal');

        const name = (inputNewPName?.value || '').trim();
        const capital = parseFloat(inputNewPCapital?.value || '500000');
        const risk = parseFloat(inputNewPRisk?.value || '1.0');
        if (!name) {
            alert('Please enter a portfolio name.');
            return;
        }

        try {
            const resp = await fetch('/api/portfolios', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, total_capital: capital, max_risk_pct: risk })
            });
            const res = await resp.json();
            if (res.error) {
                alert(res.error);
                return;
            }
            if (modalCreateP) modalCreateP.classList.add('hidden');
            if (res.portfolio && res.portfolio.id) {
                portfolioState.activePortfolioId = res.portfolio.id;
                portfolioState.activePortfolioName = res.portfolio.name;
            }
            await fetchPortfoliosList();
            await fetchPortfolioData(false);
        } catch (err) {
            console.error('Error creating portfolio:', err);
        }
    };

    window.handlePortfolioSettingsSubmit = async function(e) {
        if (e) e.preventDefault();
        const settingsPId = document.getElementById('settings-p-id');
        const inputSettingsPName = document.getElementById('input-settings-p-name');
        const inputSettingsPCapital = document.getElementById('input-settings-p-capital');
        const inputSettingsPRisk = document.getElementById('input-settings-p-risk');
        const modalPSettings = document.getElementById('portfolio-settings-modal');

        const pid = settingsPId?.value || portfolioState.activePortfolioId;
        const name = (inputSettingsPName?.value || '').trim();
        const capital = parseFloat(inputSettingsPCapital?.value || '500000');
        const risk = parseFloat(inputSettingsPRisk?.value || '1.0');
        if (!name) {
            alert('Please enter a portfolio name.');
            return;
        }

        try {
            const resp = await fetch(`/api/portfolios/${pid}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, total_capital: capital, max_risk_pct: risk })
            });
            const res = await resp.json();
            if (res.error) {
                alert(res.error);
                return;
            }
            if (modalPSettings) modalPSettings.classList.add('hidden');
            if (res.portfolio) {
                portfolioState.activePortfolioName = res.portfolio.name;
            }
            await fetchPortfoliosList();
            await fetchPortfolioData(false);
        } catch (err) {
            console.error('Error updating portfolio:', err);
        }
    };

    window.handleDeleteActivePortfolio = function() {
        const settingsPId = document.getElementById('settings-p-id');
        const modalPSettings = document.getElementById('portfolio-settings-modal');
        const pid = settingsPId?.value || portfolioState.activePortfolioId;
        if (portfolioState.allPortfolios.length <= 1) {
            alert('Cannot delete the only portfolio. You must have at least one active portfolio.');
            return;
        }
        const currentP = portfolioState.allPortfolios.find(p => p.id === pid);
        const pName = currentP ? currentP.name : 'this portfolio';

        if (modalPSettings) modalPSettings.classList.add('hidden');
        confirmModal(`Are you sure you want to delete portfolio <strong>"${escapeHtml(pName)}"</strong>?<br><br><span class="text-red">All associated holdings, watchlist items, and trade journal records inside this portfolio will be deleted!</span>`, async () => {
            try {
                const resp = await fetch(`/api/portfolios/${pid}`, { method: 'DELETE' });
                const res = await resp.json();
                if (res.error) {
                    alert(res.error);
                    return;
                }
                if (res.active_portfolio_id) {
                    portfolioState.activePortfolioId = res.active_portfolio_id;
                }
                await fetchPortfoliosList();
                await fetchPortfolioData(false);
            } catch (err) {
                console.error('Error deleting portfolio:', err);
            }
        });
    };

    const formPSettings = document.getElementById('portfolio-settings-form');
    const btnDeleteActiveP = document.getElementById('btn-delete-active-portfolio');

    if (formCreateP) {
        formCreateP.addEventListener('submit', window.handleCreatePortfolioSubmit);
    }

    if (formPSettings) {
        formPSettings.addEventListener('submit', window.handlePortfolioSettingsSubmit);
    }

    if (btnDeleteActiveP) {
        btnDeleteActiveP.addEventListener('click', window.handleDeleteActivePortfolio);
    }

    // Close on backdrop click
    window.addEventListener('click', (e) => {
        if (editModal && e.target === editModal) editModal.classList.add('hidden');
        if (exitModal && e.target === exitModal) exitModal.classList.add('hidden');
        if (confirmModalEl && e.target === confirmModalEl) confirmModalEl.classList.add('hidden');
        if (modalCreateP && e.target === modalCreateP) modalCreateP.classList.add('hidden');
        if (modalPSettings && e.target === modalPSettings) modalPSettings.classList.add('hidden');
    });

    // Initial load of portfolios tabs
    fetchPortfoliosList();
}

// Fetch all portfolios list and active ID
async function fetchPortfoliosList() {
    try {
        const resp = await fetch('/api/portfolios');
        const data = await resp.json();
        if (data.portfolios) {
            portfolioState.allPortfolios = data.portfolios;
            if (data.active_portfolio_id) {
                portfolioState.activePortfolioId = data.active_portfolio_id;
            }
            renderPortfolioTabs();
        }
    } catch (e) {
        console.error('Error fetching portfolios list:', e);
    }
}

// Render tabs for all portfolios
function renderPortfolioTabs() {
    const container = document.getElementById('portfolio-tabs-container');
    if (!container) return;

    if (!portfolioState.allPortfolios || portfolioState.allPortfolios.length === 0) {
        container.innerHTML = '<span class="text-muted" style="font-size:0.8rem;">No portfolios</span>';
        return;
    }

    container.innerHTML = portfolioState.allPortfolios.map(p => {
        const isActive = p.id === portfolioState.activePortfolioId;
        return `
            <button type="button" class="p-tab-pill ${isActive ? 'active' : ''}" data-id="${p.id}" title="${p.name} (${p.holdings_count} active holdings)">
                <i class="fa-solid fa-briefcase"></i>
                <span>${escapeHtml(p.name)}</span>
                <span class="p-tab-badge">${p.holdings_count}</span>
            </button>
        `;
    }).join('');

    // Attach click events to pills
    container.querySelectorAll('.p-tab-pill').forEach(btn => {
        btn.addEventListener('click', () => {
            const pid = btn.dataset.id;
            if (pid && pid !== portfolioState.activePortfolioId) {
                switchActivePortfolio(pid);
            }
        });
    });
}

// Switch Active Portfolio
async function switchActivePortfolio(portfolioId) {
    try {
        const resp = await fetch('/api/portfolios/switch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ portfolio_id: portfolioId })
        });
        const res = await resp.json();
        if (res.success) {
            portfolioState.activePortfolioId = res.active_portfolio_id;
            portfolioState.activePortfolioName = res.name;
            renderPortfolioTabs();
            fetchPortfolioData(false);
            fetchPortfoliosList(); // update counts
        } else {
            alert(res.error || 'Failed to switch portfolio');
        }
    } catch (e) {
        console.error('Error switching portfolio:', e);
    }
}

// Fetch Full Portfolio Data
async function fetchPortfolioData(force = false) {
    const btnRefresh = document.getElementById('btn-refresh-portfolio');
    if (btnRefresh) {
        btnRefresh.disabled = true;
        btnRefresh.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Refreshing...';
    }

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000);
        const url = `/api/portfolio?refresh=${force}${portfolioState.activePortfolioId ? `&portfolio_id=${portfolioState.activePortfolioId}` : ''}`;
        const resp = await fetch(url, { signal: controller.signal });
        clearTimeout(timeoutId);
        const data = await resp.json();

        if (data.status === 'success') {
            portfolioState.holdings = data.holdings || [];
            portfolioState.watchlist = data.watchlist || [];
            portfolioState.history = data.history || [];
            portfolioState.summary = data.summary || {};
            portfolioState.history_stats = data.history_stats || {};
            portfolioState.aladdin_diagnostics = data.aladdin_diagnostics || {};
            if (data.portfolio_id) {
                portfolioState.activePortfolioId = data.portfolio_id;
            }
            if (data.portfolio_name) {
                portfolioState.activePortfolioName = data.portfolio_name;
            }

            renderPortfolioSummary();
            renderHoldings();
            renderAllocationBreakdown();
            renderAladdinDoctor();
            renderWatchlist();
            renderHistory();
            fetchPortfoliosList(); // keeps tab count badges synchronized
        }
    } catch (err) {
        console.error('Portfolio Fetch Error:', err);
        if (typeof showNotification === 'function') {
            showNotification('Network delay: Kept current portfolio view intact.', 'warning');
        }
    } finally {
        if (btnRefresh) {
            btnRefresh.disabled = false;
            btnRefresh.innerHTML = '<i class="fa-solid fa-rotate"></i> Refresh Live Quotes';
        }
    }
}

// Render Summary KPIs & Risk Alerts
function renderPortfolioSummary() {
    const s = portfolioState.summary || {};
    const hs = portfolioState.history_stats || {};
    const diag = portfolioState.aladdin_diagnostics || {};
    const dSumm = diag.summary || {};

    const elInvested = document.getElementById('pkpi-invested');
    const elCapDeployed = document.getElementById('pkpi-capital-deployed');
    const elValue = document.getElementById('pkpi-value');
    const elActiveCount = document.getElementById('pkpi-active-count');
    const elPnl = document.getElementById('pkpi-pnl');
    const elPnlCard = document.getElementById('pkpi-pnl-card');
    const elOpenRisk = document.getElementById('pkpi-open-risk');
    const elRiskPct = document.getElementById('pkpi-risk-pct');
    const elRealizedPnl = document.getElementById('pkpi-realized-pnl');
    const elWinRate = document.getElementById('pkpi-win-rate');

    const badgeHoldings = document.getElementById('badge-holdings-count');
    const badgeWatchlist = document.getElementById('badge-watchlist-count');
    const badgeHistory = document.getElementById('badge-history-count');
    const badgeAladdinTraps = document.getElementById('badge-aladdin-traps');

    if (badgeHoldings) badgeHoldings.textContent = portfolioState.holdings.length;
    if (badgeWatchlist) badgeWatchlist.textContent = portfolioState.watchlist.length;
    if (badgeHistory) badgeHistory.textContent = portfolioState.history.length;
    if (badgeAladdinTraps) badgeAladdinTraps.textContent = `${(diag.stage4_traps || []).length} Traps`;

    // Aladdin Quick Diagnostic Banner Elements
    const elScoreVal = document.getElementById('aladdin-score-val');
    const elScoreCircle = document.getElementById('aladdin-score-circle');
    const elRunnersStat = document.getElementById('val-runners-stat');
    const elBasesStat = document.getElementById('val-bases-stat');
    const elTrapsStat = document.getElementById('val-traps-stat');

    if (elScoreVal) {
        const score = diag.health_score || 0;
        elScoreVal.textContent = `${score}%`;
        if (elScoreCircle) {
            elScoreCircle.className = `aladdin-score-circle ${score < 50 ? 'border-red' : (score < 75 ? 'border-amber' : 'border-green')}`;
        }
    }
    if (elRunnersStat) elRunnersStat.textContent = `${(diag.stage2_runners || []).length} Stocks (${dSumm.runners_pct || 0}%)`;
    if (elBasesStat) elBasesStat.textContent = `${(diag.stage1_bases || []).length} Stocks (${dSumm.bases_pct || 0}%)`;
    if (elTrapsStat) elTrapsStat.textContent = `${(diag.stage4_traps || []).length} Traps (-₹${Math.abs(dSumm.total_trapped_loss || 0).toLocaleString('en-IN')})`;

    if (elInvested) elInvested.textContent = `₹${(s.total_invested || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
    if (elCapDeployed) elCapDeployed.textContent = `${s.capital_deployed_pct || 0}% of ₹${((s.total_capital || 500000)/100000).toFixed(1)}L Capital`;
    if (elValue) elValue.textContent = `₹${(s.current_portfolio_value || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
    if (elActiveCount) elActiveCount.textContent = `${s.active_positions_count || 0} Active Positions (${s.active_positions_count >= 4 && s.active_positions_count <= 8 ? 'Optimal Diversification' : 'Target 4-8 Stocks'})`;

    const pnl = s.total_unrealized_pnl || 0;
    const pnlPct = s.total_pnl_pct || 0;
    const isPos = pnl >= 0;
    if (elPnl) {
        elPnl.textContent = `${isPos ? '+' : ''}₹${pnl.toLocaleString('en-IN', { maximumFractionDigits: 2 })} (${isPos ? '+' : ''}${pnlPct}%)`;
        elPnl.className = `kpi-value ${isPos ? 'text-green' : 'text-red'}`;
    }

    if (elOpenRisk) elOpenRisk.textContent = `₹${(s.total_open_risk || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
    if (elRiskPct) elRiskPct.textContent = `${s.total_risk_pct_of_capital || 0}% of Capital at stake`;

    const realPnl = hs.total_realized_pnl || 0;
    if (elRealizedPnl) {
        elRealizedPnl.textContent = `${realPnl >= 0 ? '+' : ''}₹${realPnl.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
        elRealizedPnl.className = `kpi-value ${realPnl >= 0 ? 'text-gold' : 'text-red'}`;
    }
    if (elWinRate) {
        const xirrBadge = (hs.xirr_pct !== null && hs.xirr_pct !== undefined)
            ? ` &bull; XIRR: <span class="${hs.xirr_pct >= 0 ? 'text-green' : 'text-red'} font-bold">${hs.xirr_pct >= 0 ? '+' : ''}${hs.xirr_pct}%</span>`
            : '';
        elWinRate.innerHTML = `Win Rate: ${hs.win_rate || 0}% (${hs.wins_count || 0}W / ${hs.losses_count || 0}L)${xirrBadge}`;
    }

    // Render Risk Alerts Banner
    const alertsContainer = document.getElementById('portfolio-alerts-container');
    if (alertsContainer) {
        const alerts = s.risk_alerts || [];
        if (alerts.length > 0) {
            alertsContainer.innerHTML = alerts.map(a => `
                <div class="alert-banner-item alert-${a.type}">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    <div>${a.message}</div>
                </div>
            `).join('');
            alertsContainer.classList.remove('hidden');
        } else {
            alertsContainer.innerHTML = '';
            alertsContainer.classList.add('hidden');
        }
    }
}

// Render Pro Trade Plan Strip & Targets (SL, T1, T2, T3, T4)
function renderTradePlanStrip(plan, isBought = true) {
    if (!plan) return '';
    const sl = plan.sl || {};
    const t1 = plan.t1 || {};
    const t2 = plan.t2 || {};
    const t3 = plan.t3 || {};
    const t4 = plan.t4 || {};

    const formatNum = (n) => (n != null && !isNaN(n)) ? Number(n).toLocaleString('en-IN', { maximumFractionDigits: 2 }) : '--';

    return `
        <!-- Pro Trade Plan & Targets (SL, T1, T2, T3, T4) -->
        <div class="trade-plan-container">
            <div class="trade-plan-header">
                <span class="tp-title"><i class="fa-solid fa-crosshairs"></i> ALGO TRADE PLAN & TARGETS</span>
                <span class="tp-sub">${isBought ? 'Execution & Profit Booking Roadmap' : 'Planned Levels for Swing Entry'}</span>
            </div>
            <div class="trade-plan-grid">
                <!-- Stop Loss -->
                <div class="tp-card tp-card-sl">
                    <div class="tp-card-badge tp-badge-sl"><i class="fa-solid fa-shield-halved"></i> SL (Supertrend)</div>
                    <div class="tp-card-price text-red">₹${formatNum(sl.price)}</div>
                    <div class="tp-card-sub text-red">-${sl.dist_pct || 0}% (${sl.label || 'Supertrend SL'})</div>
                    <div style="margin-top:6px; padding-top:4px; border-top:1px dashed rgba(255,255,255,0.15); font-size:0.75rem; color:var(--text-secondary); line-height:1.2;">
                        <span style="color:var(--accent-gold); font-weight:700;"><i class="fa-solid fa-shield-halved"></i> 5% Rule SL:</span>
                        <strong style="color:#fff;">₹${formatNum(sl.sl_5pct || (plan.entry_price * 0.95))}</strong>
                    </div>
                    ${sl.open_risk_amt != null ? `<div class="tp-card-profit text-red" style="margin-top:3px;">Risk: ₹${formatNum(sl.open_risk_amt)}</div>` : ''}
                </div>

                <!-- Target 1 (1.5R) -->
                <div class="tp-card tp-card-target ${t1.is_hit ? 'tp-hit' : ''}">
                    <div class="tp-card-badge tp-badge-t1">
                        ${t1.is_hit ? '<i class="fa-solid fa-circle-check"></i> ' : ''}T1 &bull; 1.5R
                    </div>
                    <div class="tp-card-price text-green">₹${formatNum(t1.price)}</div>
                    <div class="tp-card-sub text-green">+${t1.dist_pct || 0}%</div>
                    <div class="tp-card-profit text-green">+₹${formatNum(t1.profit)}</div>
                </div>

                <!-- Target 2 (2.5R) -->
                <div class="tp-card tp-card-target ${t2.is_hit ? 'tp-hit' : ''}">
                    <div class="tp-card-badge tp-badge-t2">
                        ${t2.is_hit ? '<i class="fa-solid fa-circle-check"></i> ' : ''}T2 &bull; 2.5R
                    </div>
                    <div class="tp-card-price text-green">₹${formatNum(t2.price)}</div>
                    <div class="tp-card-sub text-green">+${t2.dist_pct || 0}%</div>
                    <div class="tp-card-profit text-green">+₹${formatNum(t2.profit)}</div>
                </div>

                <!-- Target 3 (3.5R / ATH) -->
                <div class="tp-card tp-card-target ${t3.is_hit ? 'tp-hit' : ''}">
                    <div class="tp-card-badge tp-badge-t3">
                        ${t3.is_hit ? '<i class="fa-solid fa-circle-check"></i> ' : ''}T3 &bull; 3.5R
                    </div>
                    <div class="tp-card-price text-cyan">₹${formatNum(t3.price)}</div>
                    <div class="tp-card-sub text-cyan">+${t3.dist_pct || 0}%</div>
                    <div class="tp-card-profit text-cyan">+₹${formatNum(t3.profit)}</div>
                </div>

                <!-- Target 4 (5.0R Runner) -->
                <div class="tp-card tp-card-target ${t4.is_hit ? 'tp-hit' : ''}">
                    <div class="tp-card-badge tp-badge-t4">
                        ${t4.is_hit ? '<i class="fa-solid fa-circle-check"></i> ' : ''}T4 &bull; 5.0R
                    </div>
                    <div class="tp-card-price" style="color:#c084fc;">₹${formatNum(t4.price)}</div>
                    <div class="tp-card-sub" style="color:#c084fc;">+${t4.dist_pct || 0}%</div>
                    <div class="tp-card-profit" style="color:#c084fc;">+₹${formatNum(t4.profit)}</div>
                </div>
            </div>
        </div>
    `;
}

// Render Active Holdings (Exit & Trailing Stop Tracker)
function renderHoldings() {
    const container = document.getElementById('holdings-list-container');
    if (!container) return;

    if (portfolioState.holdings.length === 0) {
        container.innerHTML = `
            <div class="empty-container">
                <i class="fa-solid fa-vault empty-icon"></i>
                <div class="empty-title">No Active Holdings Recorded</div>
                <div class="empty-desc">Enter a stock you own above, select "Already Bought", and let the system calculate real-time exit and trailing stop-loss signals.</div>
            </div>
        `;
        return;
    }

    container.innerHTML = portfolioState.holdings.map(h => {
        if (h.error) {
            return `
                <div class="holding-card border-critical">
                    <div class="p-card-top">
                        <div class="p-symbol-group">
                            <span class="p-symbol">${h.symbol}</span>
                            <span class="p-name">${h.name}</span>
                        </div>
                    </div>
                    <div class="text-red font-bold">${h.error}</div>
                    <div class="p-card-bottom">
                        <button class="btn btn-xs btn-danger btn-delete-item" data-type="holding" data-id="${h.id}" data-sym="${h.symbol}">
                            <i class="fa-solid fa-trash"></i> Delete
                        </button>
                    </div>
                </div>
            `;
        }

        const isGain = (h.unrealized_pnl || 0) >= 0;
        const pnlSign = isGain ? '+' : '';
        const dayMovePos = (h.day_change_pct || 0) >= 0;

        let borderClass = '';
        if (h.urgency === 'CRITICAL' || h.urgency === 'HIGH') borderClass = 'border-critical';
        else if (h.urgency === 'ACTIONABLE') borderClass = 'border-gold';

        return `
            <div class="holding-card ${borderClass}">
                <div class="p-card-top">
                    <div class="p-symbol-group">
                        <span class="p-symbol">${h.symbol}</span>
                        <div>
                            <div class="p-name">${h.name}</div>
                            <span class="p-sector-badge">${h.sector} &bull; Bought ${h.hold_days}d ago</span>
                            <span class="badge badge-cyan" style="font-size:0.72rem; font-weight:700; margin-left:0.35rem;" title="Percentage allocation of total invested capital">
                                <i class="fa-solid fa-chart-pie"></i> ${h.allocation_pct || 0}% Weight
                            </span>
                        </div>
                    </div>
                    <div class="p-price-group">
                        <div class="p-ltp">₹${h.current_price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</div>
                        <div class="p-change ${dayMovePos ? 'text-green' : 'text-red'}">
                            ${dayMovePos ? '+' : ''}${h.day_change_pct}% Today
                        </div>
                    </div>
                </div>

                <!-- Position Metrics Grid -->
                <div class="p-metrics-row">
                    <div class="p-metric-item">
                        <span class="p-m-lbl">Avg Buy Price</span>
                        <span class="p-m-val">₹${h.buy_price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                    </div>
                    <div class="p-metric-item">
                        <span class="p-m-lbl">Quantity</span>
                        <span class="p-m-val">${h.quantity} Shares</span>
                    </div>
                    <div class="p-metric-item">
                        <span class="p-m-lbl">Invested Capital</span>
                        <span class="p-m-val">₹${h.invested_capital.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                        <span style="font-size:0.75rem; color:var(--accent-cyan); font-weight:700;">
                            ${h.allocation_pct || 0}% allocation
                        </span>
                    </div>
                    <div class="p-metric-item">
                        <span class="p-m-lbl">Current Value</span>
                        <span class="p-m-val">₹${h.current_value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                    </div>
                    <div class="p-metric-item">
                        <span class="p-m-lbl">Unrealized P&L</span>
                        <span class="p-m-val ${isGain ? 'text-green' : 'text-red'}">
                            ${pnlSign}₹${h.unrealized_pnl.toLocaleString('en-IN', { maximumFractionDigits: 2 })} (${pnlSign}${h.pnl_pct}%)
                        </span>
                    </div>
                    <div class="p-metric-item highlight-box">
                        <span class="p-m-lbl">Supertrend Trailing SL</span>
                        <span class="p-m-val ${h.supertrend_dir === 1 ? 'text-green' : 'text-red'}">
                            ₹${h.trailing_sl.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                            <small style="font-size:0.7rem; font-weight:700;">(${h.supertrend_dir === 1 ? 'Bullish' : 'SELL SIGNAL'})</small>
                        </span>
                        <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:3px;">
                            <span style="color:var(--accent-gold); font-weight:700;"><i class="fa-solid fa-shield-halved"></i> 5% Rule SL:</span>
                            <strong style="color:#fff;">₹${((h.sl_5pct || (h.current_price * 0.95))).toLocaleString('en-IN', { maximumFractionDigits: 2 })}</strong>
                        </div>
                    </div>
                    <div class="p-metric-item">
                        <span class="p-m-lbl">Price Action High / ATH</span>
                        <span class="p-m-val text-cyan">
                            ₹${h.target_price_action_high || h.target1} / ₹${h.target_ath || h.target2}
                        </span>
                    </div>
                </div>

                <!-- Pro Trade Plan & Targets (SL, T1, T2, T3, T4) -->
                ${renderTradePlanStrip(h.trade_plan, true)}

                <!-- Real-Time Exit Verdict Box -->
                <div class="p-verdict-box verdict-${h.verdict_badge}">
                    <div class="p-verdict-title">
                        <i class="fa-solid fa-crosshairs"></i> ${h.exit_verdict}
                    </div>
                    <div class="p-verdict-plan">
                        <strong>Action Plan:</strong> ${h.action_plan}
                    </div>
                    <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:0.25rem;">
                        <strong>Technical Reasoning:</strong> ${(h.reasons || []).join(' ')}
                    </div>
                </div>

                <!-- Card Bottom Actions -->
                <div class="p-card-bottom">
                    <div class="p-notes-text">
                        ${h.notes ? `<i class="fa-solid fa-note-sticky"></i> "${h.notes}"` : ''}
                    </div>
                    <div class="p-actions-group">
                        <button class="btn btn-xs btn-outline btn-open-chart" data-sym="${h.symbol}">
                            <i class="fa-solid fa-chart-line"></i> Chart
                        </button>
                        <button class="btn btn-xs btn-outline btn-edit-item" data-type="holding" data-id="${h.id}">
                            <i class="fa-solid fa-pen"></i> Edit
                        </button>
                        <button class="btn btn-xs btn-gold btn-open-exit" data-id="${h.id}">
                            <i class="fa-solid fa-flag-checkered"></i> Exit Trade
                        </button>
                        <button class="btn btn-xs btn-danger btn-delete-item" data-type="holding" data-id="${h.id}" data-sym="${h.symbol}">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    bindPortfolioCardEvents();
}

// Render Aladdin Portfolio Doctor & Recovery Roadmap
function renderAladdinDoctor() {
    const container = document.getElementById('aladdin-doctor-container');
    if (!container) return;

    const diag = portfolioState.aladdin_diagnostics || {};
    const dSumm = diag.summary || {};
    const score = diag.health_score || 0;
    const runners = diag.stage2_runners || [];
    const bases = diag.stage1_bases || [];
    const traps = diag.stage4_traps || [];
    const special = diag.special_cases || [];

    let html = `
        <!-- Executive Institutional Aladdin Briefing -->
        <div class="aladdin-hero-card">
            <div class="aladdin-hero-top">
                <div class="aladdin-badge-group">
                    <span class="aladdin-tag"><i class="fa-solid fa-brain-circuit"></i> ALADDIN PORTFOLIO OPTIMIZATION</span>
                    <span class="aladdin-status-badge ${score < 50 ? 'status-critical' : 'status-healthy'}">
                        ${diag.health_status || 'ANALYSIS COMPLETE'}
                    </span>
                </div>
                <div class="aladdin-score-large">
                    <span class="score-number">${score}</span><span class="score-den">/100</span>
                    <div class="score-sub">Trend Alignment Score</div>
                </div>
            </div>

            <div class="aladdin-insight-box">
                <h4 class="insight-title"><i class="fa-solid fa-triangle-exclamation text-amber"></i> Root Cause Diagnosis: The "Buy Low & Wait" Value Trap</h4>
                <p class="insight-p">
                    You currently have <strong>₹${((dSumm.traps_invested || 0)).toLocaleString('en-IN')} (${dSumm.traps_pct || 0}% of your total capital)</strong> locked in <strong>${traps.length} Stage 4 downtrend stocks</strong> (ACC, DABUR, HUL, SBICARD, HDFCBANK, RELIANCE) with an open loss of <strong>-₹${Math.abs(dSumm.total_trapped_loss || 0).toLocaleString('en-IN')}</strong>.
                </p>
                <p class="insight-p">
                    While these are fundamentally great blue chips, <strong>price is trading below the Daily 50 EMA with Supertrend SELL signals</strong>. In quantitative finance, holding falling knives leads to massive <strong>Opportunity Cost (~₹${(dSumm.estimated_opportunity_cost_monthly || 0).toLocaleString('en-IN')}/month)</strong> while momentum market leaders gained 30% to 80%.
                </p>
                <div class="aladdin-callout">
                    <i class="fa-solid fa-lightbulb text-gold"></i>
                    <div>
                        <strong>The Aladdin Solution:</strong> Stop averaging down on falling knives. Execute <em>Capital Recycling</em>: redeploy trapped capital from dead Stage 4 stocks into top-scoring <strong>7/7 Elite Momentum BUY Setups</strong> to recover losses in 15–30 days instead of waiting 1–2 years for break-even.
                    </div>
                </div>
            </div>
        </div>

        <!-- The 3 Buckets Grid -->
        <div class="aladdin-buckets-grid">
            <!-- Bucket 1: Stage 2 Runners -->
            <div class="aladdin-bucket-card card-glass border-green">
                <div class="bucket-header bg-green-subtle">
                    <div class="bucket-title-group">
                        <span class="bucket-tag text-green"><i class="fa-solid fa-rocket"></i> BUCKET 1: STAGE 2 WINNERS</span>
                        <h3>Let Profits Run</h3>
                    </div>
                    <span class="bucket-badge bg-green">${runners.length} Stocks</span>
                </div>
                <div class="bucket-body">
                    <p class="bucket-desc">Secular institutional momentum. Price is above 50 EMA and Supertrend is Bullish Green.</p>
                    <div class="bucket-items-list">
                        ${runners.length > 0 ? runners.map(r => `
                            <div class="bucket-stock-item">
                                <div class="bsi-top">
                                    <span class="bsi-sym">${r.symbol}</span>
                                    <span class="bsi-pnl text-green">+${r.pnl_pct}% (+₹${r.unrealized_pnl.toLocaleString('en-IN')})</span>
                                </div>
                                <div class="bsi-plan text-cyan"><strong>Plan:</strong> ${r.rationale}</div>
                            </div>
                        `).join('') : '<div class="text-muted p-2">No active Stage 2 winners currently.</div>'}
                    </div>
                </div>
            </div>

            <!-- Bucket 2: Stage 1 Bases -->
            <div class="aladdin-bucket-card card-glass border-cyan">
                <div class="bucket-header bg-cyan-subtle">
                    <div class="bucket-title-group">
                        <span class="bucket-tag text-cyan"><i class="fa-solid fa-layer-group"></i> BUCKET 2: STAGE 1 BASING</span>
                        <h3>Patience at Support</h3>
                    </div>
                    <span class="bucket-badge bg-cyan">${bases.length} Stocks</span>
                </div>
                <div class="bucket-body">
                    <p class="bucket-desc">Supertrend has turned Green (early accumulation). Hold with trailing stop; DO NOT average down until 50 EMA breakout.</p>
                    <div class="bucket-items-list">
                        ${bases.length > 0 ? bases.map(b => `
                            <div class="bucket-stock-item">
                                <div class="bsi-top">
                                    <span class="bsi-sym">${b.symbol}</span>
                                    <span class="bsi-pnl ${b.pnl_pct >= 0 ? 'text-green' : 'text-amber'}">${b.pnl_pct >= 0 ? '+' : ''}${b.pnl_pct}%</span>
                                </div>
                                <div class="bsi-plan"><strong>Plan:</strong> ${b.rationale}</div>
                            </div>
                        `).join('') : '<div class="text-muted p-2">No active basing stocks currently.</div>'}
                    </div>
                </div>
            </div>

            <!-- Bucket 3: Stage 4 Traps -->
            <div class="aladdin-bucket-card card-glass border-critical">
                <div class="bucket-header bg-red-subtle">
                    <div class="bucket-title-group">
                        <span class="bucket-tag text-red"><i class="fa-solid fa-triangle-exclamation"></i> BUCKET 3: VALUE TRAPS</span>
                        <h3>Capital Recycling Needed</h3>
                    </div>
                    <span class="bucket-badge bg-red">${traps.length} Stocks</span>
                </div>
                <div class="bucket-body">
                    <p class="bucket-desc">Supertrend SELL & below Daily 50 EMA. Negative relative strength. Bleeding your capital through opportunity cost.</p>
                    <div class="bucket-items-list">
                        ${traps.length > 0 ? traps.map(t => `
                            <div class="bucket-stock-item">
                                <div class="bsi-top">
                                    <span class="bsi-sym">${t.symbol}</span>
                                    <span class="bsi-pnl text-red">${t.pnl_pct}% (-₹${Math.abs(t.unrealized_pnl).toLocaleString('en-IN')})</span>
                                </div>
                                <div class="bsi-plan text-amber"><strong>Relief Target:</strong> ₹${t.relief_exit_target} &bull; ${t.rationale}</div>
                            </div>
                        `).join('') : '<div class="text-muted p-2">Zero value traps in portfolio!</div>'}
                    </div>
                </div>
            </div>
        </div>

        <!-- Special Case: Suzlon Deep Dive -->
        ${special.length > 0 ? special.map(s => `
            <div class="aladdin-special-box card-glass">
                <div class="asb-header">
                    <span class="badge badge-warning"><i class="fa-solid fa-wind"></i> SPECIAL SITUATION: ${s.symbol}</span>
                    <span class="text-red font-bold">${s.pnl_pct}% (-₹${Math.abs(s.unrealized_pnl).toLocaleString('en-IN')})</span>
                </div>
                <div class="asb-body">
                    <p><strong>LTP:</strong> ₹${s.current_price} &bull; <strong>Buy Price:</strong> ₹${s.buy_price} &bull; <strong>Quantity:</strong> ${s.quantity} shares (₹${s.invested_capital.toLocaleString('en-IN')} invested)</p>
                    <p class="asb-rationale">${s.rationale}</p>
                </div>
            </div>
        `).join('') : ''}

        <!-- Interactive Capital Recycling Roadmap Table -->
        <div class="card-glass aladdin-roadmap-card">
            <div class="arm-header">
                <div>
                    <h3 class="arm-title"><i class="fa-solid fa-arrows-spin text-cyan"></i> Capital Recycling & Recovery Roadmap</h3>
                    <p class="arm-sub">How swapping dead Stage 4 capital into Long Momentum Swings (Price > 50 EMA & Supertrend Green) recovers losses rapidly</p>
                </div>
            </div>
            <div class="arm-table-wrapper">
                <table class="arm-table">
                    <thead>
                        <tr>
                            <th>Trapped Stock</th>
                            <th>Capital Locked</th>
                            <th>Current Loss</th>
                            <th>Breakdown Status</th>
                            <th>Recommended Action</th>
                            <th>Aladdin Swap Edge</th>
                            <th>Est. Recovery Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${traps.map(t => `
                            <tr>
                                <td><strong>${t.symbol}</strong><br><small class="text-muted">${t.name}</small></td>
                                <td>₹${t.invested_capital.toLocaleString('en-IN')}</td>
                                <td class="text-red font-bold">${t.pnl_pct}%<br><small>-₹${Math.abs(t.unrealized_pnl).toLocaleString('en-IN')}</small></td>
                                <td><span class="badge badge-danger">Supertrend SELL</span><br><small>Below 50 EMA</small></td>
                                <td>
                                    <strong>Exit on Relief (₹${t.relief_exit_target})</strong><br>
                                    <small>Or Recycle Capital</small>
                                </td>
                                <td>
                                    <span class="text-green font-bold">Swap into 7/7 Elite BUY</span><br>
                                    <small>Expected +8% to +12% target</small>
                                </td>
                                <td><span class="badge badge-success">15–25 Days</span></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

// Render Watchlist (Looking to Buy - Entry Signals Only)
function renderWatchlist() {
    const container = document.getElementById('watchlist-list-container');
    if (!container) return;

    if (portfolioState.watchlist.length === 0) {
        container.innerHTML = `
            <div class="empty-container">
                <i class="fa-solid fa-binoculars empty-icon"></i>
                <div class="empty-title">Watchlist is Empty</div>
                <div class="empty-desc">Enter any NSE stock above and select "Looking to Buy" to evaluate fresh breakout entry signals, exact stop-losses, and profit targets.</div>
            </div>
        `;
        return;
    }

    container.innerHTML = portfolioState.watchlist.map(w => {
        if (w.error) {
            return `
                <div class="watchlist-card border-critical">
                    <div class="p-card-top">
                        <span class="p-symbol">${w.symbol}</span>
                    </div>
                    <div class="text-red font-bold">${w.error}</div>
                    <div class="p-card-bottom">
                        <button class="btn btn-xs btn-danger btn-delete-item" data-type="watchlist" data-id="${w.id}" data-sym="${w.symbol}">
                            <i class="fa-solid fa-trash"></i> Delete
                        </button>
                    </div>
                </div>
            `;
        }

        const dayMovePos = (w.day_change_pct || 0) >= 0;

        return `
            <div class="watchlist-card">
                <div class="p-card-top">
                    <div class="p-symbol-group">
                        <span class="p-symbol">${w.symbol}</span>
                        <div>
                            <div class="p-name">${w.name}</div>
                            <span class="p-sector-badge">${w.sector}</span>
                        </div>
                    </div>
                    <div class="p-price-group">
                        <div class="p-ltp">₹${w.current_price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</div>
                        <div class="p-change ${dayMovePos ? 'text-green' : 'text-red'}">
                            ${dayMovePos ? '+' : ''}${w.day_change_pct}% Today
                        </div>
                    </div>
                </div>

                <!-- Technical Indicators Snapshot -->
                <div class="p-metrics-row">
                    <div class="p-metric-item">
                        <span class="p-m-lbl">50 EMA (Daily)</span>
                        <span class="p-m-val">₹${w.ema50}</span>
                    </div>
                    <div class="p-metric-item">
                        <span class="p-m-lbl">Distance from EMA</span>
                        <span class="p-m-val ${w.dist_from_ema50_pct > 0 ? 'text-green' : 'text-red'}">
                            ${w.dist_from_ema50_pct > 0 ? '+' : ''}${w.dist_from_ema50_pct}%
                        </span>
                    </div>
                    <div class="p-metric-item">
                        <span class="p-m-lbl">Supertrend (10,3)</span>
                        <span class="p-m-val ${w.supertrend_dir === 1 ? 'text-green' : 'text-red'}">
                            ₹${w.supertrend} (${w.supertrend_badge})
                        </span>
                    </div>
                    <div class="p-metric-item">
                        <span class="p-m-lbl">RSI (14)</span>
                        <span class="p-m-val">${w.rsi14}</span>
                    </div>
                    <div class="p-metric-item">
                        <span class="p-m-lbl">Supertrend SL</span>
                        <span class="p-m-val text-red">₹${w.suggested_sl} (-${w.risk_pct}%)</span>
                        <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:2px;">
                            <span style="color:var(--accent-gold); font-weight:700;"><i class="fa-solid fa-shield-halved"></i> 5% Rule SL:</span>
                            <strong style="color:#fff;">₹${((w.sl_5pct || (w.current_price * 0.95))).toLocaleString('en-IN', { maximumFractionDigits: 2 })}</strong>
                        </div>
                    </div>
                    <div class="p-metric-item highlight-box">
                        <span class="p-m-lbl">Target: PA High / ATH</span>
                        <span class="p-m-val text-green">₹${w.target_price_action_high || w.target1} / ₹${w.target_ath || w.target2}</span>
                    </div>
                    <div class="p-metric-item">
                        <span class="p-m-lbl">Position Size (₹2k risk)</span>
                        <span class="p-m-val text-cyan">${w.rec_shares_2k_risk} shares</span>
                    </div>
                </div>

                <!-- Pro Trade Plan & Targets (SL, T1, T2, T3, T4) -->
                ${renderTradePlanStrip(w.trade_plan, false)}

                <!-- Entry Verdict Box -->
                <div class="p-verdict-box verdict-${w.verdict_badge}">
                    <div class="p-verdict-title">
                        <i class="fa-solid fa-bullseye"></i> ${w.entry_verdict}
                    </div>
                    <div class="p-verdict-plan">
                        <strong>Action Plan:</strong> ${w.action_plan}
                    </div>
                    <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:0.25rem;">
                        <strong>Technical Reasons:</strong> ${(w.reasons || []).join(' ')}
                    </div>
                </div>

                <!-- Bottom Actions -->
                <div class="p-card-bottom">
                    <div class="p-notes-text">
                        ${w.notes ? `<i class="fa-solid fa-note-sticky"></i> "${w.notes}"` : ''}
                    </div>
                    <div class="p-actions-group">
                        <button class="btn btn-xs btn-outline btn-open-chart" data-sym="${w.symbol}">
                            <i class="fa-solid fa-chart-line"></i> Chart
                        </button>
                        <button class="btn btn-xs btn-success btn-convert-holding" data-sym="${w.symbol}" data-price="${w.current_price}">
                            <i class="fa-solid fa-cart-shopping"></i> Bought! Move to Holdings
                        </button>
                        <button class="btn btn-xs btn-outline btn-edit-item" data-type="watchlist" data-id="${w.id}">
                            <i class="fa-solid fa-pen"></i> Edit
                        </button>
                        <button class="btn btn-xs btn-danger btn-delete-item" data-type="watchlist" data-id="${w.id}" data-sym="${w.symbol}">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    bindPortfolioCardEvents();
}

// Render Allocation & Capital Weights Breakdown
function renderAllocationBreakdown() {
    const container = document.getElementById('allocation-breakdown-container');
    if (!container) return;

    const holdings = portfolioState.holdings || [];
    const summary = portfolioState.summary || {};
    const totalInvested = summary.total_invested || 0;
    const totalCapital = summary.total_capital || 500000;

    if (holdings.length === 0) {
        container.innerHTML = `
            <div class="empty-container">
                <i class="fa-solid fa-chart-pie empty-icon"></i>
                <div class="empty-title">No Active Holdings to Allocate</div>
                <div class="empty-desc">Add stocks to your active holdings to see individual percentage weights, concentration distribution, and capital deployment analysis.</div>
            </div>
        `;
        return;
    }

    // Sort holdings by invested capital descending
    const sorted = [...holdings].sort((a, b) => (b.invested_capital || 0) - (a.invested_capital || 0));

    // Sector breakdown calculation
    const sectorMap = {};
    sorted.forEach(h => {
        const sec = h.sector || 'Others';
        sectorMap[sec] = (sectorMap[sec] || 0) + (h.invested_capital || 0);
    });
    const sectorsSorted = Object.entries(sectorMap)
        .map(([name, inv]) => ({
            name,
            invested: inv,
            pct: totalInvested > 0 ? ((inv / totalInvested) * 100).toFixed(1) : 0
        }))
        .sort((a, b) => b.invested - a.invested);

    const colors = ['#06b6d4', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#3b82f6', '#14b8a6', '#f97316', '#6366f1', '#a855f7'];

    container.innerHTML = `
        <div class="card-glass" style="padding:1.5rem; margin-bottom:1.5rem; border-radius:12px;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem; margin-bottom:1.25rem;">
                <div>
                    <h3 style="margin:0; font-size:1.15rem; display:flex; align-items:center; gap:0.5rem;">
                        <i class="fa-solid fa-chart-pie text-cyan"></i> Portfolio Capital Allocation & Position Weights
                    </h3>
                    <p style="margin:0.25rem 0 0 0; font-size:0.8rem; color:var(--text-secondary);">
                        Total Deployed: <strong>₹${totalInvested.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</strong> (${summary.capital_deployed_pct || 0}% of ₹${(totalCapital/100000).toFixed(1)}L Capital) across <strong>${holdings.length} stocks</strong>
                    </p>
                </div>
                <div style="font-size:0.8rem; background:rgba(6, 182, 212, 0.1); border:1px solid rgba(6, 182, 212, 0.25); border-radius:8px; padding:0.4rem 0.8rem; color:var(--accent-cyan);">
                    <i class="fa-solid fa-shield-halved"></i> Recommended Max Per Stock: <strong>15% - 25%</strong>
                </div>
            </div>

            <!-- Multi-Color Segmented Allocation Bar -->
            <div style="display:flex; height:20px; width:100%; border-radius:10px; overflow:hidden; background:rgba(255,255,255,0.05); margin-bottom:1.5rem; border:1px solid rgba(255,255,255,0.1);">
                ${sorted.map((h, idx) => {
                    const color = colors[idx % colors.length];
                    const alloc = h.allocation_pct || (totalInvested > 0 ? ((h.invested_capital / totalInvested) * 100).toFixed(1) : 0);
                    if (alloc <= 0) return '';
                    return `<div style="width:${alloc}%; background:${color}; height:100%;" title="${h.symbol}: ${alloc}% (₹${Math.round(h.invested_capital).toLocaleString('en-IN')})"></div>`;
                }).join('')}
            </div>

            <!-- Stock Allocation Table -->
            <div class="history-table-wrapper">
                <table class="history-table">
                    <thead>
                        <tr>
                            <th>Stock</th>
                            <th>Sector</th>
                            <th>Invested Capital</th>
                            <th>Current Value</th>
                            <th>Portfolio Allocation %</th>
                            <th>Weight Visual</th>
                            <th>Concentration Risk</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${sorted.map((h, idx) => {
                            const alloc = parseFloat(h.allocation_pct || (totalInvested > 0 ? ((h.invested_capital / totalInvested) * 100).toFixed(2) : 0));
                            const color = colors[idx % colors.length];
                            let riskBadge = '<span class="badge badge-success">Balanced (&le;15%)</span>';
                            if (alloc > 25) {
                                riskBadge = '<span class="badge badge-danger">High Concentration (&gt;25%)</span>';
                            } else if (alloc > 15) {
                                riskBadge = '<span class="badge badge-warning">Moderate (15-25%)</span>';
                            }

                            return `
                                <tr>
                                    <td>
                                        <div style="display:flex; align-items:center; gap:0.5rem;">
                                            <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:${color};"></span>
                                            <strong>${h.symbol}</strong>
                                            <small style="color:var(--text-muted); font-size:0.75rem;">(${h.quantity} shs)</small>
                                        </div>
                                    </td>
                                    <td><small style="color:var(--text-secondary);">${h.sector}</small></td>
                                    <td>₹${h.invested_capital.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</td>
                                    <td class="${(h.unrealized_pnl || 0) >= 0 ? 'text-green' : 'text-red'} font-bold">
                                        ₹${h.current_value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                                    </td>
                                    <td style="font-weight:800; font-family:var(--font-mono); font-size:0.95rem; color:${color};">
                                        ${alloc.toFixed(2)}%
                                    </td>
                                    <td style="min-width:140px;">
                                        <div style="background:rgba(255,255,255,0.06); height:8px; border-radius:4px; overflow:hidden;">
                                            <div style="width:${Math.min(alloc, 100)}%; background:${color}; height:100%;"></div>
                                        </div>
                                    </td>
                                    <td>${riskBadge}</td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>

            <!-- Sector Breakdown Grid -->
            <div style="margin-top:2rem;">
                <h4 style="font-size:0.95rem; color:var(--text-secondary); margin-bottom:0.75rem; display:flex; align-items:center; gap:0.5rem;">
                    <i class="fa-solid fa-layer-group text-cyan"></i> Sector-Wise Capital Distribution
                </h4>
                <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(220px, 1fr)); gap:0.75rem;">
                    ${sectorsSorted.map(sec => `
                        <div class="card-glass" style="padding:0.75rem 1rem; border-radius:8px; border:1px solid rgba(255,255,255,0.06);">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.35rem;">
                                <strong style="font-size:0.85rem;">${sec.name}</strong>
                                <span style="font-weight:700; color:var(--accent-cyan); font-size:0.85rem;">${sec.pct}%</span>
                            </div>
                            <div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:0.4rem;">
                                ₹${Math.round(sec.invested).toLocaleString('en-IN')}
                            </div>
                            <div style="background:rgba(255,255,255,0.06); height:5px; border-radius:3px; overflow:hidden;">
                                <div style="width:${Math.min(sec.pct, 100)}%; background:var(--accent-cyan); height:100%;"></div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
}

// Render Historical Trade Journal
function renderHistory() {
    const container = document.getElementById('history-list-container');
    const kpiBar = document.getElementById('history-kpi-bar');
    if (!container) return;

    const exportBtn = document.getElementById('btn-export-history-csv');
    if (exportBtn) {
        exportBtn.href = `/api/portfolio/export_history_csv?portfolio_id=${encodeURIComponent(portfolioState.active_portfolio_id || 'default')}`;
        exportBtn.style.display = portfolioState.history.length > 0 ? 'inline-flex' : 'none';
    }

    if (portfolioState.history.length === 0) {
        if (kpiBar) kpiBar.innerHTML = '';
        container.innerHTML = `
            <div class="empty-container">
                <i class="fa-solid fa-book-bookmark empty-icon"></i>
                <div class="empty-title">Trade Journal is Empty</div>
                <div class="empty-desc">When you exit a holding, click "Exit Trade" and it will be recorded into this journal with realized P&L, hold duration, and exit rationale to help you refine your pro trading edge.</div>
            </div>
        `;
        return;
    }

    // Render History KPI Dashboard (XIRR, CAGR, Realized Profit, Win Rate, Duration)
    const hs = portfolioState.history_stats || {};
    if (kpiBar) {
        const hasXirr = hs.xirr_pct !== null && hs.xirr_pct !== undefined;
        const xirrFormatted = hasXirr ? `${hs.xirr_pct >= 0 ? '+' : ''}${hs.xirr_pct}%` : 'N/A';
        const xirrClass = hasXirr ? (hs.xirr_pct >= 0 ? 'text-green' : 'text-red') : 'text-muted';

        const cagrFormatted = hs.cagr_pct !== undefined && hs.cagr_pct !== null ? `${hs.cagr_pct >= 0 ? '+' : ''}${hs.cagr_pct}%` : 'N/A';
        const cagrClass = (hs.cagr_pct || 0) >= 0 ? 'text-green' : 'text-red';
        const spanDays = hs.cagr_span_days || hs.avg_hold_days || 0;
        const isCagrApplicable = hs.cagr_is_applicable;

        kpiBar.innerHTML = `
            <div class="history-kpi-card highlight-xirr">
                <div class="history-kpi-label">
                    <span><i class="fa-solid fa-bolt text-green"></i> XIRR Return</span>
                    <span class="metric-tag metric-tag-green" title="Applicable standard for irregular cash flows">Money-Weighted</span>
                </div>
                <div class="history-kpi-val ${xirrClass}">${xirrFormatted}</div>
                <div class="history-kpi-sub">
                    <strong>Primary Metric:</strong> Annualized rate accounting for cash timing across entries and exits.
                </div>
            </div>

            <div class="history-kpi-card highlight-cagr">
                <div class="history-kpi-label">
                    <span><i class="fa-solid fa-chart-line text-cyan"></i> Account CAGR</span>
                    <span class="metric-tag ${isCagrApplicable ? 'metric-tag-cyan' : 'metric-tag-muted'}">
                        ${isCagrApplicable ? 'Compounded' : 'Annualized (' + spanDays + 'd)'}
                    </span>
                </div>
                <div class="history-kpi-val ${cagrClass}">${cagrFormatted}</div>
                <div class="history-kpi-sub" title="${hs.cagr_note || ''}">
                    ${hs.cagr_note || ('Compounding pace of account capital across ' + spanDays + ' calendar days')}
                </div>
            </div>

            <div class="history-kpi-card">
                <div class="history-kpi-label">
                    <span><i class="fa-solid fa-sack-dollar text-gold"></i> Realized Profit</span>
                    <span class="metric-tag metric-tag-muted">${portfolioState.history.length} Trades</span>
                </div>
                <div class="history-kpi-val ${(hs.total_realized_pnl || 0) >= 0 ? 'text-gold' : 'text-red'}">
                    ${(hs.total_realized_pnl || 0) >= 0 ? '+' : ''}₹${(hs.total_realized_pnl || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                </div>
                <div class="history-kpi-sub">
                    Total net closed gains banked into account capital
                </div>
            </div>

            <div class="history-kpi-card">
                <div class="history-kpi-label">
                    <span><i class="fa-solid fa-bullseye text-purple"></i> Win Ratio</span>
                    <span class="metric-tag metric-tag-muted">PF: ${hs.profit_factor || 1.0}</span>
                </div>
                <div class="history-kpi-val text-cyan">${hs.win_rate || 0}%</div>
                <div class="history-kpi-sub">
                    ${hs.wins_count || 0} Wins &nbsp;|&nbsp; ${hs.losses_count || 0} Losses &nbsp;(Profit Factor: ${hs.profit_factor || 1.0})
                </div>
            </div>

            <div class="history-kpi-card">
                <div class="history-kpi-label">
                    <span><i class="fa-solid fa-clock-rotate-left"></i> Hold Horizon</span>
                    <span class="metric-tag metric-tag-muted">${spanDays}d Span</span>
                </div>
                <div class="history-kpi-val text-secondary">
                    ${hs.avg_hold_days || 0} <span style="font-size:0.95rem; font-weight:500;">Days Avg</span>
                </div>
                <div class="history-kpi-sub">
                    Average holding duration per closed swing position
                </div>
            </div>
        `;
    }

    container.innerHTML = `
        <table class="history-table">
            <thead>
                <tr>
                    <th>Stock</th>
                    <th>Buy Date &rarr; Exit Date</th>
                    <th>Duration</th>
                    <th>Buy &rarr; Exit Price</th>
                    <th>Quantity</th>
                    <th>Realized P&L</th>
                    <th>Return %</th>
                    <th>Annualized Return</th>
                    <th>Exit Reason</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${portfolioState.history.map(t => {
                    const isWin = (t.realized_pnl || 0) > 0;
                    const pnlSign = isWin ? '+' : '';
                    const annRet = t.ann_return_pct !== undefined ? t.ann_return_pct : (t.hold_days > 0 ? ((t.return_pct || 0) * 365 / t.hold_days).toFixed(1) : t.return_pct);
                    const annColor = annRet >= 0 ? 'text-green' : 'text-red';
                    const annSign = annRet >= 0 ? '+' : '';

                    return `
                        <tr>
                            <td>
                                <strong>${t.symbol}</strong><br>
                                <small style="color:var(--text-muted);">${t.name}</small>
                            </td>
                            <td>${t.buy_date} &rarr; ${t.exit_date}</td>
                            <td><strong>${t.hold_days} days</strong></td>
                            <td>₹${t.buy_price} &rarr; ₹${t.exit_price}</td>
                            <td>${t.quantity}</td>
                            <td class="${isWin ? 'text-green' : 'text-red'} font-bold">
                                ${pnlSign}₹${t.realized_pnl.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                            </td>
                            <td>
                                <span class="badge ${isWin ? 'badge-success' : 'badge-danger'}">
                                    ${pnlSign}${t.return_pct}%
                                </span>
                            </td>
                            <td>
                                <div style="display:flex; flex-direction:column;">
                                    <span class="${annColor} font-bold">
                                        ${annSign}${annRet}%
                                    </span>
                                    <small style="color:var(--text-muted); font-size:0.7rem;">p.a. (365d)</small>
                                </div>
                            </td>
                            <td>
                                <small style="color:var(--text-secondary);">${t.exit_reason}</small>
                            </td>
                            <td>
                                <button class="btn btn-xs btn-danger btn-delete-item" data-type="history" data-id="${t.id}" data-sym="${t.symbol}">
                                    <i class="fa-solid fa-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `;
                }).join('')}
            </tbody>
        </table>
    `;

    bindPortfolioCardEvents();
}

// Bind card button actions (Chart, Edit, Exit, Delete, Convert)
function bindPortfolioCardEvents() {
    // Chart buttons
    document.querySelectorAll('.btn-open-chart').forEach(btn => {
        btn.addEventListener('click', () => {
            const sym = btn.dataset.sym;
            if (typeof openChartModal === 'function') {
                openChartModal(sym);
            }
        });
    });

    // Delete buttons with confirmation modal
    document.querySelectorAll('.btn-delete-item').forEach(btn => {
        btn.addEventListener('click', () => {
            const type = btn.dataset.type;
            const id = btn.dataset.id;
            const sym = btn.dataset.sym;

            confirmModal(`Are you sure you want to delete <strong>${sym}</strong> from your ${type === 'holding' ? 'Active Holdings' : (type === 'watchlist' ? 'Watchlist' : 'Trade Journal')}?`, async () => {
                try {
                    const resp = await fetch(`/api/portfolio/item?type=${type}&id=${id}&portfolio_id=${portfolioState.activePortfolioId || ''}`, { method: 'DELETE' });
                    const res = await resp.json();
                    if (res.success) {
                        fetchPortfolioData(false);
                    } else {
                        alert(res.error || 'Failed to delete');
                    }
                } catch (e) {
                    console.error('Delete error:', e);
                }
            });
        });
    });

    // Edit buttons
    document.querySelectorAll('.btn-edit-item').forEach(btn => {
        btn.addEventListener('click', () => {
            const type = btn.dataset.type;
            const id = btn.dataset.id;
            openEditModal(type, id);
        });
    });

    // Exit Trade buttons
    document.querySelectorAll('.btn-open-exit').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.dataset.id;
            openExitModal(id);
        });
    });

    // Convert Watchlist item to Holding
    document.querySelectorAll('.btn-convert-holding').forEach(btn => {
        btn.addEventListener('click', () => {
            const sym = btn.dataset.sym;
            const price = btn.dataset.price;

            // Switch add form to holding mode with prefilled values
            document.getElementById('seg-btn-holding').click();
            document.getElementById('input-p-symbol').value = sym;
            document.getElementById('input-p-buyprice').value = price;
            document.getElementById('input-p-qty').value = '100';
            document.getElementById('input-p-symbol').scrollIntoView({ behavior: 'smooth' });
        });
    });
}

// Live Technical Analysis Preview
async function runQuickAnalysis() {
    const inputSymbol = document.getElementById('input-p-symbol');
    const previewContainer = document.getElementById('live-analysis-preview');
    if (!inputSymbol || !previewContainer) return;

    const sym = inputSymbol.value.trim().toUpperCase();
    if (!sym) {
        alert('Please enter a stock symbol first (e.g. RELIANCE, TATASTEEL, INFY).');
        inputSymbol.focus();
        return;
    }

    previewContainer.classList.remove('hidden');
    previewContainer.innerHTML = '<div class="text-cyan"><i class="fa-solid fa-spinner fa-spin"></i> Fetching real-time exchange data and calculating swing indicators...</div>';

    const isBought = portfolioState.addType === 'holding';
    const buyPrice = isBought ? (document.getElementById('input-p-buyprice').value || 0) : 0;
    const qty = isBought ? (document.getElementById('input-p-qty').value || 0) : 0;
    const buyDate = isBought ? document.getElementById('input-p-buydate').value : '';
    const initialSl = isBought ? document.getElementById('input-p-sl').value : '';

    try {
        const url = `/api/portfolio/analyze?symbol=${encodeURIComponent(sym)}&is_bought=${isBought}&buy_price=${buyPrice}&quantity=${qty}&buy_date=${buyDate}&initial_sl=${initialSl}`;
        const resp = await fetch(url);
        const data = await resp.json();

        if (data.error) {
            previewContainer.innerHTML = `<div class="text-red"><i class="fa-solid fa-triangle-exclamation"></i> ${data.error}</div>`;
            return;
        }

        const isGain = (data.unrealized_pnl || 0) >= 0;

        previewContainer.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border-color); padding-bottom:0.75rem;">
                <div>
                    <strong style="font-size:1.15rem; font-family:var(--font-mono);">${data.symbol}</strong>
                    <span style="color:var(--text-secondary); margin-left:0.5rem;">${data.name} &bull; ${data.sector}</span>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.2rem; font-weight:800; font-family:var(--font-mono);">₹${data.current_price}</div>
                    <small class="${data.day_change_pct >= 0 ? 'text-green' : 'text-red'} font-bold">
                        ${data.day_change_pct >= 0 ? '+' : ''}${data.day_change_pct}% Today
                    </small>
                </div>
            </div>

            <div class="preview-grid">
                <div class="preview-stat">
                    <div class="preview-stat-label">50 EMA</div>
                    <div class="preview-stat-val">₹${data.ema50}</div>
                </div>
                <div class="preview-stat">
                    <div class="preview-stat-label">Distance to 50 EMA</div>
                    <div class="preview-stat-val ${data.dist_from_ema50_pct >= 0 ? 'text-green' : 'text-red'}">
                        ${data.dist_from_ema50_pct >= 0 ? '+' : ''}${data.dist_from_ema50_pct}%
                    </div>
                </div>
                <div class="preview-stat">
                    <div class="preview-stat-label">Supertrend (10,3)</div>
                    <div class="preview-stat-val ${data.supertrend_dir === 1 ? 'text-green' : 'text-red'}">
                        ₹${data.supertrend} (${data.supertrend_badge})
                    </div>
                </div>
                <div class="preview-stat">
                    <div class="preview-stat-label">RSI 14</div>
                    <div class="preview-stat-val">${data.rsi14}</div>
                </div>
                <div class="preview-stat">
                    <div class="preview-stat-label">Volume Ratio</div>
                    <div class="preview-stat-val ${data.volume_surge_x >= 1.1 ? 'text-green' : ''}">
                        ${data.volume_surge_x}x 20d MA
                    </div>
                </div>
                <div class="preview-stat">
                    <div class="preview-stat-label">${isBought ? 'Supertrend Trailing SL' : 'Supertrend Suggested SL'}</div>
                    <div class="preview-stat-val text-red">₹${isBought ? data.trailing_sl : data.suggested_sl}</div>
                    <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:3px;">
                        <span style="color:var(--accent-gold); font-weight:700;"><i class="fa-solid fa-shield-halved"></i> 5% Rule SL:</span>
                        <strong style="color:#fff;">₹${((data.sl_5pct || (data.current_price * 0.95))).toFixed(2)}</strong>
                    </div>
                </div>
                <div class="preview-stat">
                    <div class="preview-stat-label">Price Action High</div>
                    <div class="preview-stat-val text-cyan">₹${data.price_action_high || data.target1} (${data.dist_to_swing_high_pct > 0 ? '+' : ''}${data.dist_to_swing_high_pct}%)</div>
                </div>
                <div class="preview-stat">
                    <div class="preview-stat-label">All-Time High (ATH)</div>
                    <div class="preview-stat-val text-gold">₹${data.high_52w || data.target2} (${data.dist_to_ath_pct > 0 ? '+' : ''}${data.dist_to_ath_pct}%)</div>
                </div>
            </div>

            <!-- Pro Trade Plan & Targets (SL, T1, T2, T3, T4) -->
            ${renderTradePlanStrip(data.trade_plan, isBought)}

            <div class="p-verdict-box verdict-${data.verdict_badge}">
                <div class="p-verdict-title">
                    <i class="fa-solid fa-crosshairs"></i> ${isBought ? data.exit_verdict : data.entry_verdict}
                </div>
                <div class="p-verdict-plan">
                    <strong>Action Plan:</strong> ${data.action_plan}
                </div>
                <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:0.25rem;">
                    <strong>Technical Reasoning:</strong> ${(data.reasons || []).join(' ')}
                </div>
            </div>
        `;
    } catch (e) {
        previewContainer.innerHTML = `<div class="text-red">Error analyzing stock: ${e.message}</div>`;
    }
}

// Add Stock to Portfolio or Watchlist
async function handlePortfolioAdd(e) {
    e.preventDefault();
    const sym = document.getElementById('input-p-symbol').value.trim().toUpperCase();
    if (!sym) return;

    const type = portfolioState.addType; // 'holding' | 'watchlist'
    const payload = {
        symbol: sym
    };

    if (type === 'holding') {
        const buyPrice = parseFloat(document.getElementById('input-p-buyprice').value);
        const qty = parseInt(document.getElementById('input-p-qty').value, 10);
        const buyDate = document.getElementById('input-p-buydate').value;
        const initialSl = parseFloat(document.getElementById('input-p-sl').value) || null;

        if (!buyPrice || buyPrice <= 0 || !qty || qty <= 0) {
            alert('Please provide a valid Buy Price and Quantity for your holding.');
            return;
        }

        payload.buy_price = buyPrice;
        payload.quantity = qty;
        payload.buy_date = buyDate;
        payload.initial_sl = initialSl;
    } else {
        const targetEntry = parseFloat(document.getElementById('input-p-target-entry').value) || null;
        const notes = document.getElementById('input-p-notes').value.trim();
        payload.target_entry_price = targetEntry;
        payload.notes = notes;
    }

    try {
        const resp = await fetch('/api/portfolio/item', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: type, data: payload, portfolio_id: portfolioState.activePortfolioId })
        });
        const res = await resp.json();

        if (res.error) {
            alert(res.error);
            return;
        }

        // Reset inputs and preview
        document.getElementById('input-p-symbol').value = '';
        if (type === 'holding') {
            document.getElementById('input-p-buyprice').value = '';
            document.getElementById('input-p-qty').value = '';
            document.getElementById('input-p-sl').value = '';
        } else {
            document.getElementById('input-p-target-entry').value = '';
            document.getElementById('input-p-notes').value = '';
        }
        document.getElementById('live-analysis-preview').classList.add('hidden');

        // Switch to relevant subtab and refresh
        if (type === 'holding') {
            document.getElementById('subtab-holdings').click();
        } else {
            document.getElementById('subtab-watchlist').click();
        }

        fetchPortfolioData(false);
    } catch (err) {
        console.error('Add Error:', err);
    }
}

// Open Edit Modal
function openEditModal(type, id) {
    const modal = document.getElementById('edit-item-modal');
    const form = document.getElementById('edit-item-form');
    if (!modal || !form) return;

    let item = null;
    if (type === 'holding') {
        item = portfolioState.holdings.find(h => h.id === id);
    } else {
        item = portfolioState.watchlist.find(w => w.id === id);
    }
    if (!item) return;

    document.getElementById('edit-item-id').value = id;
    document.getElementById('edit-item-type').value = type;
    document.getElementById('edit-symbol').value = item.symbol;
    document.getElementById('edit-notes').value = item.notes || '';

    const holdingFields = document.getElementById('edit-holding-fields');
    const watchlistFields = document.getElementById('edit-watchlist-fields');
    const groupBuyDate = document.getElementById('edit-group-buydate');

    if (type === 'holding') {
        holdingFields.classList.remove('hidden');
        watchlistFields.classList.add('hidden');
        groupBuyDate.classList.remove('hidden');

        document.getElementById('edit-buyprice').value = item.buy_price || '';
        document.getElementById('edit-quantity').value = item.quantity || '';
        document.getElementById('edit-buydate').value = item.buy_date || '';
        document.getElementById('edit-initial-sl').value = item.initial_sl || '';
        document.getElementById('edit-target1').value = item.target1 || '';
        document.getElementById('edit-target2').value = item.target2 || '';
        document.getElementById('edit-target3').value = item.target3 || '';
        document.getElementById('edit-target4').value = item.target4 || '';
    } else {
        holdingFields.classList.add('hidden');
        watchlistFields.classList.remove('hidden');
        groupBuyDate.classList.add('hidden');

        document.getElementById('edit-target-entry').value = item.target_entry_price || '';
    }

    modal.classList.remove('hidden');
}

// Save Edit
async function handleSaveEdit(e) {
    e.preventDefault();
    const id = document.getElementById('edit-item-id').value;
    const type = document.getElementById('edit-item-type').value;
    const modal = document.getElementById('edit-item-modal');

    const payload = {
        notes: document.getElementById('edit-notes').value.trim()
    };

    if (type === 'holding') {
        payload.buy_price = parseFloat(document.getElementById('edit-buyprice').value);
        payload.quantity = parseInt(document.getElementById('edit-quantity').value, 10);
        payload.buy_date = document.getElementById('edit-buydate').value;
        payload.initial_sl = parseFloat(document.getElementById('edit-initial-sl').value) || null;
        payload.target1 = parseFloat(document.getElementById('edit-target1').value) || null;
        payload.target2 = parseFloat(document.getElementById('edit-target2').value) || null;
        payload.target3 = parseFloat(document.getElementById('edit-target3').value) || null;
        payload.target4 = parseFloat(document.getElementById('edit-target4').value) || null;
    } else {
        payload.target_entry_price = parseFloat(document.getElementById('edit-target-entry').value) || null;
    }

    try {
        const resp = await fetch('/api/portfolio/item', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: type, id: id, data: payload, portfolio_id: portfolioState.activePortfolioId })
        });
        const res = await resp.json();

        if (res.error) {
            alert(res.error);
            return;
        }

        modal.classList.add('hidden');
        fetchPortfolioData(false);
    } catch (err) {
        console.error('Update Error:', err);
    }
}

// Open Exit Trade Modal
function openExitModal(id) {
    const modal = document.getElementById('close-trade-modal');
    if (!modal) return;

    const holding = portfolioState.holdings.find(h => h.id === id);
    if (!holding) return;

    const totalQty = parseInt(holding.quantity, 10) || 1;

    document.getElementById('exit-item-id').value = id;
    document.getElementById('exit-buy-price').value = holding.buy_price;
    document.getElementById('exit-qty').value = totalQty;

    document.getElementById('exit-symbol-label').textContent = holding.symbol;
    document.getElementById('exit-qty-label').textContent = `${totalQty} shares`;
    document.getElementById('exit-buy-label').textContent = `₹${holding.buy_price}`;

    const inputExitShares = document.getElementById('input-exit-shares');
    if (inputExitShares) {
        inputExitShares.max = totalQty;
        inputExitShares.value = totalQty; // Default to full exit
    }
    const hintEl = document.getElementById('exit-total-shares-hint');
    if (hintEl) hintEl.textContent = totalQty;

    document.getElementById('input-exit-price').value = holding.current_price;
    document.getElementById('input-exit-date').value = new Date().toISOString().split('T')[0];

    // Hold duration can be any number for history (auto-calculated from dates, or user specified)
    const holdDaysInput = document.getElementById('input-exit-hold-days');
    if (holdDaysInput) {
        holdDaysInput.value = (holding.hold_days !== undefined && holding.hold_days !== null) ? holding.hold_days : '';
    }

    updateExitPnlPreview();
    modal.classList.remove('hidden');
}

// Live calculation in Exit Modal (supports partial exit shares)
function updateExitPnlPreview() {
    const buyPrice = parseFloat(document.getElementById('exit-buy-price').value) || 0;
    const totalQty = parseInt(document.getElementById('exit-qty').value, 10) || 0;
    const inputShares = document.getElementById('input-exit-shares');
    let sellQty = inputShares ? parseInt(inputShares.value, 10) : totalQty;
    if (isNaN(sellQty) || sellQty <= 0) sellQty = totalQty;
    if (sellQty > totalQty) sellQty = totalQty;

    const exitPrice = parseFloat(document.getElementById('input-exit-price').value) || 0;

    const pnl = (exitPrice - buyPrice) * sellQty;
    const pnlPct = buyPrice > 0 ? ((exitPrice - buyPrice) / buyPrice) * 100 : 0;
    const isGain = pnl >= 0;

    const typeLabel = document.getElementById('exit-sell-type-label');
    if (typeLabel) {
        if (sellQty < totalQty) {
            typeLabel.textContent = `(Partial Exit: Selling ${sellQty}, Retaining ${totalQty - sellQty})`;
            typeLabel.className = 'text-amber font-bold';
        } else {
            typeLabel.textContent = `(Full Exit: Selling all ${totalQty})`;
            typeLabel.className = 'text-cyan font-bold';
        }
    }

    const display = document.getElementById('exit-pnl-display');
    if (display) {
        display.textContent = `${isGain ? '+' : ''}₹${pnl.toLocaleString('en-IN', { maximumFractionDigits: 2 })} (${isGain ? '+' : ''}${pnlPct.toFixed(2)}%) for ${sellQty} shs`;
        display.className = `exit-pnl-val ${isGain ? 'text-green' : 'text-red'}`;
    }
}

// Confirm Exit Trade & Move to Journal (supports partial exit)
async function handleConfirmExitTrade(e) {
    e.preventDefault();
    const id = document.getElementById('exit-item-id').value;
    const exitPrice = parseFloat(document.getElementById('input-exit-price').value);
    const exitDate = document.getElementById('input-exit-date').value;
    const reason = document.getElementById('select-exit-reason').value;
    const holdDaysInput = document.getElementById('input-exit-hold-days');
    const holdDays = (holdDaysInput && holdDaysInput.value.trim() !== '') ? parseInt(holdDaysInput.value, 10) : null;
    const totalQty = parseInt(document.getElementById('exit-qty').value, 10) || 1;
    const inputShares = document.getElementById('input-exit-shares');
    const exitQty = inputShares ? parseInt(inputShares.value, 10) : totalQty;
    const modal = document.getElementById('close-trade-modal');

    if (!exitPrice || exitPrice <= 0) {
        alert('Please enter a valid exit price.');
        return;
    }
    if (!exitQty || exitQty <= 0) {
        alert('Please enter a valid quantity to sell.');
        return;
    }
    if (exitQty > totalQty) {
        alert(`Cannot sell ${exitQty} shares. You only own ${totalQty} shares.`);
        return;
    }

    try {
        const resp = await fetch('/api/portfolio/close_trade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id: id,
                exit_price: exitPrice,
                exit_date: exitDate,
                exit_reason: reason,
                hold_days: holdDays,
                exit_qty: exitQty,
                portfolio_id: portfolioState.activePortfolioId
            })
        });
        const res = await resp.json();

        if (res.error) {
            alert(res.error);
            return;
        }

        modal.classList.add('hidden');
        if (typeof showNotification === 'function') {
            showNotification(res.message || 'Exit trade recorded successfully!', 'success');
        }
        if (res.is_partial) {
            document.getElementById('subtab-holdings').click();
        } else {
            document.getElementById('subtab-history').click();
        }
        fetchPortfolioData(false);
    } catch (err) {
        console.error('Exit Trade Error:', err);
    }
}

// Generic Confirmation Modal
function confirmModal(message, onConfirm) {
    const modal = document.getElementById('confirm-modal');
    const msgEl = document.getElementById('confirm-modal-message');
    if (!modal || !msgEl) return;

    msgEl.innerHTML = message;
    portfolioState.pendingConfirmAction = onConfirm;
    modal.classList.remove('hidden');
}

