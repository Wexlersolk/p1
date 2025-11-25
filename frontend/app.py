# app.py
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import plotly.express as px
import base64
import numpy as np
from datetime import datetime, timedelta
import os

# Конфігурація сторінки
st.set_page_config(
    page_title="Trading Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS для покращеного вигляду
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    .strategy-card {

        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .parameter-card {
        padding: 1rem;
        border-radius: 8px;
        border-left: 3px solid #28a745;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Базовий URL API
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")

# Глобальні змінні
available_assets = []
all_strategies = []

# Заголовок
st.markdown('<h1 class="main-header">🎯 Trading Analytics Dashboard</h1>', unsafe_allow_html=True)

# Функції для отримання даних
@st.cache_data(ttl=3600)
def fetch_available_assets():
    """Get available assets"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=30)
        response.raise_for_status()
        return response.json()
    except:
        return ["Binance_Spot_XRP_1d", "Binance_Spot_BTC_1h", "Coinbase_Spot_ETH_1d"]

@st.cache_data(ttl=3600)
def fetch_all_strategies():
    """Get all available strategies"""
    try:
        response = requests.get(f"{API_BASE_URL}/backtest/strategies/available", timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('strategies', ["vwap_ib", "sma_crossover", "rsi_oversold"])
    except:
        return ["vwap_ib", "sma_crossover", "rsi_oversold"]

# Ініціалізація глобальних змінних
available_assets = fetch_available_assets()
all_strategies = fetch_all_strategies()

# Бічна панель для налаштувань
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Навігація
    page = st.selectbox(
        "Select Page:",
        ["Market Overview", "Strategy Dashboard", "Asset Analysis", "Backtesting", "Asset Comparison", "Strategy Library"]
    )
    
    asset = st.selectbox(
        "Select Asset:",
        available_assets,
        index=0
    )
    
    if page in ["Strategy Dashboard", "Backtesting", "Asset Analysis"]:
        days = st.slider(
            "Analysis Period (days):",
            min_value=7,
            max_value=90,
            value=30
        )
        
        initial_capital = st.number_input(
            "Initial Capital:",
            min_value=1000,
            max_value=50000,
            value=10000,
            step=1000
        )
    
    if page in ["Market Overview", "Asset Comparison"]:
        data_limit = st.slider(
            "Data Points Limit:",
            min_value=100,
            max_value=1000,
            value=100,
            step=100
        )
    
    # Вибір стратегії для сторінок, де він потрібен
    if page in ["Backtesting", "Asset Comparison", "Strategy Library", "Asset Analysis"]:
        selected_strategy = st.selectbox("Strategy:", all_strategies, index=0, key="sidebar_strategy")
    
    # AI налаштування для backtesting
    if page == "Backtesting":
        st.markdown("---")
        st.subheader("🤖 AI Settings")
        use_ai = st.checkbox("Use AI Signal Filtering", value=True)
        min_confidence = st.slider("Minimum AI Confidence", 0.0, 1.0, 0.6, 0.1)
    
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# Функції для Strategies API - використовуємо робочі ендпоінти
@st.cache_data(ttl=3600)
def fetch_all_strategies_detailed():
    """Get all available strategies - використовуємо робочий ендпоінт"""
    try:
        # Використовуємо робочий ендпоінт замість /api/v1/strategies/
        response = requests.get(f"{API_BASE_URL}/backtest/strategies/available", timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Створюємо базову структуру для сумісності
        strategies_data = {
            'strategies': {}
        }
        
        # Додаємо базову інформацію про кожну стратегію
        for strategy_id in data.get('strategies', []):
            strategies_data['strategies'][strategy_id] = {
                'name': strategy_id.replace('_', ' ').title(),
                'description': f'{strategy_id} trading strategy',
                'parameters': {
                    'lookback': {'default': 100, 'description': 'Lookback period'},
                    'initial_capital': {'default': 10000, 'description': 'Initial capital'}
                }
            }
        
        return strategies_data
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching strategies: {e}")
        return None

@st.cache_data(ttl=3600)
def fetch_strategy_info(strategy_id):
    """Get basic information about a specific strategy"""
    try:
        # Оскільки /api/v1/strategies/{strategy_id} не працює, повертаємо базову інформацію
        strategy_info = {
            'name': strategy_id.replace('_', ' ').title(),
            'description': f'{strategy_id} trading strategy with AI support',
            'parameters': {
                'lookback': {
                    'type': 'integer',
                    'default': 100,
                    'description': 'Number of historical periods to analyze'
                },
                'initial_capital': {
                    'type': 'number', 
                    'default': 10000,
                    'description': 'Initial trading capital'
                },
                'use_ai': {
                    'type': 'boolean',
                    'default': True,
                    'description': 'Enable AI signal filtering'
                }
            }
        }
        return strategy_info
    except Exception as e:
        st.error(f"❌ Error fetching strategy info: {e}")
        return None

@st.cache_data(ttl=300)
def fetch_strategy_signals(strategy_id, asset, lookback=100):
    """Get signals for a specific strategy and asset"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/strategies/{strategy_id}/signals/{asset}",
            params={"lookback": lookback},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching strategy signals: {e}")
        return None

def train_strategy_model(strategy_id, asset):
    """Train ML model for a strategy"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/strategies/train/{strategy_id}/{asset}", timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error training strategy model: {e}")
        return None

# Функції для Backtest API
@st.cache_data(ttl=300)
def run_backtest(asset, lookback=100, initial_capital=10000, strategy_id="vwap_ib", use_ai=True, min_confidence=0.6):
    """Run backtest for a specific asset"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/backtest/{asset}",
            params={
                "lookback": lookback, 
                "initial_capital": initial_capital, 
                "strategy_id": strategy_id,
                "use_ai": use_ai,
                "min_confidence": min_confidence
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error running backtest: {e}")
        return None

@st.cache_data(ttl=300)
def check_ai_status():
    """Check AI model status"""
    try:
        response = requests.get(f"{API_BASE_URL}/backtest/debug/ai-status", timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error checking AI status: {e}")
        return None

# Функції для Visualization API
@st.cache_data(ttl=300)
def fetch_dashboard_data(asset, days, initial_capital):
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/visualization/strategy-dashboard/{asset}",
            params={"days": days, "initial_capital": initial_capital},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching dashboard data: {e}")
        return None

@st.cache_data(ttl=300)
def fetch_signal_timeline(strategy_id, asset, days):
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/visualization/signal-timeline/{strategy_id}/{asset}",
            params={"days": days},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching signal timeline: {e}")
        return None

@st.cache_data(ttl=300)
def fetch_confidence_analysis(strategy_id, asset, days=30):
    """Get ML confidence analysis for a specific strategy"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/visualization/confidence-analysis/{strategy_id}/{asset}",
            params={"days": days},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching confidence analysis: {e}")
        return None

@st.cache_data(ttl=300)
def fetch_available_ml_strategies(asset):
    """Get list of available strategies with ML support"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/visualization/available-strategies",
            params={"asset": asset},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching ML strategies: {e}")
        return None

# Допоміжні функції
def decode_binary_data(bdata_str):
    """Декодує base64 бінарні дані з Plotly"""
    try:
        if isinstance(bdata_str, str) and len(bdata_str) > 0:
            decoded = base64.b64decode(bdata_str)
            return np.frombuffer(decoded, dtype=np.float64)
    except Exception as e:
        st.error(f"Error decoding binary data: {e}")
    return None

def display_signal_timeline(signal_data, strategy, asset):
    """Відображає графік цін з ML-сигналами"""
    st.markdown(f"### 🎯 {strategy.upper()} - ML Trading Signals for {asset}")
    
    if 'signal_stats' in signal_data:
        stats = signal_data['signal_stats']
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Signals", stats.get('total_signals', 0))
        with col2:
            st.metric("Buy Signals", stats.get('buy_signals', 0))
        with col3:
            st.metric("Sell Signals", stats.get('sell_signals', 0))
        with col4:
            st.metric("Win Rate", f"{stats.get('win_rate', 0):.1f}%")
    
    if 'chart' in signal_data:
        chart_data = signal_data['chart']
        try:
            if 'data' in chart_data and 'layout' in chart_data:
                fig = go.Figure(data=chart_data['data'], layout=chart_data['layout'])
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error rendering signal chart: {e}")

# Покращена функція для відображення графіків
def render_equity_curve(equity_data):
    """Покращена функція для відображення графіка Equity Curve"""
    try:
        # Діагностика: показуємо структуру даних
        with st.expander("🔍 Debug Equity Curve Data"):
            st.write("Data type:", type(equity_data))
            if isinstance(equity_data, dict):
                st.write("Data keys:", list(equity_data.keys()))
                if 'data' in equity_data:
                    st.write("Number of traces:", len(equity_data['data']))
                    for i, trace in enumerate(equity_data['data']):
                        st.write(f"Trace {i} keys:", list(trace.keys()) if isinstance(trace, dict) else type(trace))
        
        # Якщо дані у форматі JSON string
        if isinstance(equity_data, str):
            try:
                equity_data = json.loads(equity_data)
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON format in equity curve data")
                return
        
        # Якщо дані у форматі словника з ключем 'data'
        if isinstance(equity_data, dict) and 'data' in equity_data:
            fig = go.Figure()
            
            for trace in equity_data['data']:
                if isinstance(trace, dict):
                    x_data = trace.get('x', [])
                    y_data = trace.get('y', [])
                    name = trace.get('name', 'Unknown')
                    
                    # Перевіряємо, чи є дані для відображення
                    if x_data and y_data and len(x_data) == len(y_data):
                        fig.add_trace(go.Scatter(
                            x=x_data,
                            y=y_data,
                            mode='lines',
                            name=name,
                            line=dict(width=3),
                            hovertemplate=trace.get('hovertemplate', f'{name}<br>Time: %{{x}}<br>Value: %{{y}}<extra></extra>')
                        ))
                    else:
                        st.warning(f"⚠️ No valid data for trace: {name}")
            
            if len(fig.data) > 0:
                fig.update_layout(
                    title="Strategy Performance - Equity Curve",
                    xaxis_title="Time",
                    yaxis_title="Portfolio Value ($)",
                    hovermode="x unified",
                    height=500,
                    showlegend=True
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("📊 No valid data to display in equity curve")
        
        else:
            st.warning("📊 Equity curve data format not recognized")
            
    except Exception as e:
        st.error(f"❌ Error rendering equity curve: {str(e)}")

def render_returns_chart(dashboard_data):
    """Покращена функція для відображення графіка доходностей"""
    try:
        # Якщо є метрики в dashboard_data, використовуємо їх
        if 'metrics' in dashboard_data and dashboard_data['metrics']:
            strategies = []
            returns = []
            
            for strategy_id, metrics in dashboard_data['metrics'].items():
                strategy_name = metrics.get('name', strategy_id)
                total_return = metrics.get('total_return', 0) * 100  # Конвертуємо у відсотки
                
                strategies.append(strategy_name)
                returns.append(total_return)
            
            if strategies and returns:
                fig = px.bar(
                    x=strategies,
                    y=returns,
                    title="Total Returns by Strategy",
                    labels={'x': 'Strategy', 'y': 'Return (%)'},
                    color=returns,
                    color_continuous_scale=['red', 'yellow', 'green']
                )
                
                fig.update_traces(
                    hovertemplate="<b>%{x}</b><br>Return: %{y:.2f}%<extra></extra>",
                    texttemplate="%{y:.2f}%",
                    textposition="outside"
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("📊 No strategy metrics available for returns chart")
        else:
            st.warning("📊 No metrics data available for returns chart")
            
    except Exception as e:
        st.error(f"❌ Error rendering returns chart: {str(e)}")

def render_win_rate_chart(dashboard_data):
    """Покращена функція для відображення графіка Win Rate"""
    try:
        if 'metrics' in dashboard_data and dashboard_data['metrics']:
            strategies = []
            win_rates = []
            
            for strategy_id, metrics in dashboard_data['metrics'].items():
                strategy_name = metrics.get('name', strategy_id)
                win_rate = metrics.get('win_rate', 0) * 100  # Конвертуємо у відсотки
                
                strategies.append(strategy_name)
                win_rates.append(win_rate)
            
            if strategies and win_rates:
                fig = px.bar(
                    x=strategies,
                    y=win_rates,
                    title="Win Rate by Strategy",
                    labels={'x': 'Strategy', 'y': 'Win Rate (%)'},
                    color=win_rates,
                    color_continuous_scale=['red', 'yellow', 'green']
                )
                
                fig.update_traces(
                    hovertemplate="<b>%{x}</b><br>Win Rate: %{y:.2f}%<extra></extra>",
                    texttemplate="%{y:.2f}%",
                    textposition="outside"
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("📊 No win rate data available")
        else:
            st.warning("📊 No metrics data available for win rate chart")
            
    except Exception as e:
        st.error(f"❌ Error rendering win rate chart: {str(e)}")

# Сторінка Strategy Library - ВИПРАВЛЕНА ВЕРСІЯ
def show_strategy_library_page():
    st.markdown("## 📚 Strategy Library")
    
    # Використовуємо робочий ендпоінт замість /api/v1/strategies/
    with st.spinner("Loading strategies..."):
        strategies_data = fetch_all_strategies_detailed()
    
    if not strategies_data:
        st.error("Failed to load strategies data. Using basic strategy list.")
        # Використовуємо базовий список стратегій
        strategies_data = {
            'strategies': {}
        }
        for strategy_id in all_strategies:
            strategies_data['strategies'][strategy_id] = {
                'name': strategy_id.replace('_', ' ').title(),
                'description': f'{strategy_id} trading strategy',
                'parameters': {
                    'lookback': {'default': 100, 'description': 'Lookback period'},
                    'initial_capital': {'default': 10000, 'description': 'Initial capital'}
                }
            }
    
    tab1, tab2, tab3 = st.tabs(["All Strategies", "Strategy Details", "ML Training"])
    
    with tab1:
        st.markdown("### 📊 All Available Strategies")
        
        if 'strategies' in strategies_data and strategies_data['strategies']:
            for i, (strategy_id, strategy_info) in enumerate(strategies_data['strategies'].items()):
                with st.expander(f"**{strategy_info.get('name', strategy_id)}** - {strategy_info.get('description', '')}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**ID:** `{strategy_id}`")
                        st.write(f"**Description:** {strategy_info.get('description', 'No description')}")
                        
                        # Параметри
                        parameters = strategy_info.get('parameters', {})
                        if parameters:
                            st.write("**Parameters:**")
                            for param_name, param_config in parameters.items():
                                st.write(f"- `{param_name}`: {param_config.get('description', '')} (default: {param_config.get('default', 'N/A')})")
                    
                    with col2:
                        # Використовуємо унікальний ключ з індексом
                        if st.button(f"Test Strategy", key=f"test_{strategy_id}_{i}"):
                            st.session_state.selected_strategy = strategy_id
                            st.success(f"Selected {strategy_id} for testing")
        else:
            st.warning("No strategies data available")
            # Показуємо базовий список
            st.markdown("#### Basic Strategy List")
            for strategy_id in all_strategies:
                st.write(f"- **{strategy_id}**")
    
    with tab2:
        st.markdown("### 🔍 Strategy Details")
        
        # Вибір стратегії для детального перегляду
        selected_strategy = st.selectbox(
            "Select Strategy for Detailed View:",
            options=list(strategies_data.get('strategies', {}).keys()) if strategies_data and strategies_data.get('strategies') else all_strategies,
            key="strategy_details_select"
        )
        
        if selected_strategy:
            strategy_info = fetch_strategy_info(selected_strategy)
            if strategy_info:
                st.markdown(f"#### {strategy_info.get('name', selected_strategy)}")
                st.write(f"**Description:** {strategy_info.get('description', '')}")
                
                # Параметри
                parameters = strategy_info.get('parameters', {})
                if parameters:
                    st.markdown("##### ⚙️ Parameters")
                    for param_name, param_config in parameters.items():
                        with st.container():
                            st.markdown(f"""
                            <div class="parameter-card">
                                <strong>{param_name}</strong><br>
                                Type: {param_config.get('type', 'unknown')}<br>
                                Default: {param_config.get('default', 'N/A')}<br>
                                Description: {param_config.get('description', '')}
                            </div>
                            """, unsafe_allow_html=True)
                
                # Тестування стратегії
                st.markdown("##### 🧪 Test Strategy")
                # Використовуємо унікальний ключ для слайдера
                test_lookback = st.slider("Lookback Period", 100, 1000, 100, key=f"test_lookback_{selected_strategy}")
                
                # Використовуємо унікальний ключ для кнопки
                if st.button("Get Strategy Signals", key=f"signals_{selected_strategy}"):
                    with st.spinner("Fetching strategy signals..."):
                        signals = fetch_strategy_signals(selected_strategy, asset, test_lookback)
                        if signals:
                            st.json(signals)
                        else:
                            st.error("Failed to fetch strategy signals")
    
    with tab3:
        st.markdown("### 🤖 ML Model Training")
        
        st.info("""
        **ML-Validated Strategies** use machine learning to filter trading signals based on historical performance patterns.
        Train ML models to improve strategy accuracy and reduce false signals.
        """)
        
        # Перевірка статусу AI
        if st.button("Check AI Status", key="check_ai_status_library"):
            with st.spinner("Checking AI status..."):
                ai_status = check_ai_status()
                if ai_status:
                    st.success(f"✅ AI System Status: {ai_status.get('status', 'Unknown')}")
                    if 'models_loaded' in ai_status:
                        st.write(f"Models loaded: {ai_status['models_loaded']}")
                else:
                    st.error("Failed to check AI status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            ml_strategies = fetch_available_ml_strategies(asset)
            if ml_strategies:
                ml_strategy = st.selectbox(
                    "Select ML Strategy to Train:",
                    options=ml_strategies.get('strategies', all_strategies),
                    key="ml_training_strategy_library"
                )
            else:
                ml_strategy = st.selectbox(
                    "Select ML Strategy to Train:",
                    options=all_strategies,
                    key="ml_training_strategy_library"
                )
            
            training_asset = st.selectbox(
                "Training Asset:",
                options=available_assets,
                key="training_asset_library"
            )
        
        with col2:
            st.markdown("#### Training Information")
            st.write("ML training uses historical data to learn which signals are most likely to be profitable.")
            st.write("Training process is asynchronous and may take several minutes.")
        
        if st.button("🚀 Train ML Model", type="primary", key="train_ml_model_library"):
            with st.spinner("Initiating ML model training..."):
                training_result = train_strategy_model(ml_strategy, training_asset)
                if training_result:
                    st.success(f"✅ {training_result.get('message', 'Training initiated successfully!')}")
                    st.info("Training is running in the background. Check back later for results.")
                else:
                    st.error("Failed to initiate ML model training")

# Сторінка Strategy Dashboard - ВИПРАВЛЕНА ВЕРСІЯ
def show_strategy_dashboard_page():
    with st.spinner("🔄 Loading dashboard data..."):
        dashboard_data = fetch_dashboard_data(asset, days, initial_capital)

    if not dashboard_data:
        st.error("Failed to load dashboard data. Please check if the API server is running.")
        
        # Показуємо альтернативний контент
        st.markdown("## 📈 Performance Overview")
        st.warning("Dashboard data is currently unavailable. Please try the following:")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Run Quick Backtest Instead"):
                st.session_state.show_quick_backtest = True
        
        if st.session_state.get('show_quick_backtest', False):
            st.markdown("### 🤖 Quick Backtest")
            quick_strategy = st.selectbox("Select Strategy", all_strategies, key="quick_dashboard_strategy")
            if st.button("Run Backtest"):
                with st.spinner("Running backtest..."):
                    result = run_backtest(asset, 100, initial_capital, quick_strategy)
                    if result:
                        st.success("Backtest completed!")
                        if 'performance_metrics' in result:
                            metrics = result['performance_metrics']
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Return", f"{metrics.get('total_return', 0)*100:.2f}%")
                            with col2:
                                st.metric("Win Rate", f"{metrics.get('win_rate', 0)*100:.2f}%")
                            with col3:
                                st.metric("Total Trades", result.get('total_trades', 0))
        return

    # Основний контент Strategy Dashboard
    st.markdown("## 📈 Performance Overview")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Asset", dashboard_data.get('asset', 'N/A'))
    with col2:
        st.metric("Analysis Period", f"{dashboard_data.get('period_days', 0)} days")
    with col3:
        st.metric("Initial Capital", f"${dashboard_data.get('initial_capital', 0):,}")
    with col4:
        strategies_tested = len(dashboard_data.get('strategies_tested', []))
        st.metric("Strategies Tested", strategies_tested)

    # Інсайти
    if 'insights' in dashboard_data and dashboard_data['insights']:
        st.markdown("## 💡 Key Insights")
        for insight in dashboard_data['insights']:
            if insight.get('type') == 'info':
                st.info(f"**{insight.get('title', '')}**: {insight.get('message', '')}")
            elif insight.get('type') == 'warning':
                st.warning(f"**{insight.get('title', '')}**: {insight.get('message', '')}")
            elif insight.get('type') == 'success':
                st.success(f"**{insight.get('title', '')}**: {insight.get('message', '')}")
            else:
                st.write(f"**{insight.get('title', '')}**: {insight.get('message', '')}")

    # Графіки продуктивності
    st.markdown("## 📊 Performance Charts")

    # Equity Curve
    if 'charts' in dashboard_data and 'equity_curve' in dashboard_data['charts']:
        st.markdown("### 📈 Equity Curve Comparison")
        render_equity_curve(dashboard_data['charts']['equity_curve'])

    # Returns Comparison
    if 'charts' in dashboard_data and 'returns_chart' in dashboard_data['charts']:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Total Returns")
            render_returns_chart(dashboard_data)
        
        with col2:
            st.markdown("### 🎯 Win Rate")
            render_win_rate_chart(dashboard_data)

    # Детальні метрики стратегій
    st.markdown("## 🔍 Detailed Strategy Metrics")

    if 'metrics' in dashboard_data and dashboard_data['metrics']:
        metrics_df_data = []
        
        for strategy_id, metrics in dashboard_data['metrics'].items():
            metrics_df_data.append({
                'Strategy': metrics.get('name', strategy_id),
                'Total Return (%)': metrics.get('total_return', 0) * 100,
                'Win Rate (%)': metrics.get('win_rate', 0) * 100,
                'Max Drawdown (%)': metrics.get('max_drawdown', 0) * 100,
                'Total Trades': metrics.get('total_trades', 0),
                'Avg Win (%)': metrics.get('avg_win', 0) * 100,
                'Avg Loss (%)': metrics.get('avg_loss', 0) * 100,
                'Profit Factor': metrics.get('profit_factor', 0),
                'Final Capital': metrics.get('final_capital', 0)
            })
        
        if metrics_df_data:
            metrics_df = pd.DataFrame(metrics_df_data)
            
            # Сортування за найкращою доходністю
            metrics_df = metrics_df.sort_values('Total Return (%)', ascending=False)
            
            # Відображення таблиці
            st.dataframe(
                metrics_df,
                use_container_width=True,
                hide_index=True
            )
    else:
        st.warning("No detailed metrics available")

    # ML Signal Timeline
    st.markdown("---")
    st.markdown("## 📈 ML Signal Timeline")
    
    # Використовуємо стратегії з dashboard_data або глобальний список
    available_strategies_for_signals = []
    if dashboard_data and 'strategies_tested' in dashboard_data and dashboard_data['strategies_tested']:
        available_strategies_for_signals = dashboard_data['strategies_tested']
    else:
        available_strategies_for_signals = all_strategies
    
    if not available_strategies_for_signals:
        st.warning("No strategies available for signal analysis.")
        return
    
    selected_strategy = st.selectbox(
        "Select Strategy for Signal Analysis:",
        options=available_strategies_for_signals,
        key="signal_strategy_select"
    )

    if st.button("🔄 Load Signal Timeline", key="load_signals"):
        if not selected_strategy or selected_strategy == "None":
            st.error("Please select a valid strategy.")
            return
            
        with st.spinner("Loading ML signal timeline..."):
            signal_data = fetch_signal_timeline(selected_strategy, asset, days)
            if signal_data:
                display_signal_timeline(signal_data, selected_strategy, asset)
            else:
                st.error("Failed to load signal timeline data.")

# Сторінка Market Overview
def show_market_overview_page():
    st.markdown("## 📈 Market Overview")
    
    # Отримуємо базову інформацію про доступні дані
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Available Assets", len(available_assets))
    
    with col2:
        st.metric("Selected Asset", asset)
    
    with col3:
        if st.button("🔄 Refresh Assets"):
            st.cache_data.clear()
            st.rerun()
    
    tab1, tab2, tab3 = st.tabs(["Asset Data", "Strategy Performance", "AI Analysis"])
    
    with tab1:
        st.markdown("### 📊 Quick Asset Analysis")
        
        # Швидкий backtest для обраного активу
        st.markdown("#### ⚡ Quick Backtest")
        quick_strategy = st.selectbox("Strategy", all_strategies, key="quick_strategy")
        quick_lookback = st.slider("Lookback", 100, 1000, 100, key="quick_lookback")
        
        if st.button("Run Quick Backtest", key="quick_backtest"):
            with st.spinner("Running quick backtest..."):
                result = run_backtest(asset, quick_lookback, 10000, quick_strategy)
                if result and 'performance_metrics' in result:
                    metrics = result['performance_metrics']
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Return", f"{metrics.get('total_return', 0)*100:.2f}%")
                    with col2:
                        st.metric("Win Rate", f"{metrics.get('win_rate', 0)*100:.2f}%")
                    with col3:
                        st.metric("Total Trades", result.get('total_trades', 0))
                    with col4:
                        st.metric("Final Capital", f"${result.get('final_capital', 0):.2f}")
    
    with tab2:
        st.markdown("### 📈 Strategy Comparison")
        
        # Порівняння стратегій для обраного активу
        comparison_strategies = st.multiselect(
            "Select strategies to compare:",
            all_strategies,
            default=all_strategies[:3] if len(all_strategies) >= 3 else all_strategies
        )
        
        if st.button("Compare Strategies", key="compare_strategies"):
            with st.spinner("Comparing strategies..."):
                comparison_data = []
                for strategy in comparison_strategies:
                    result = run_backtest(asset, 100, 10000, strategy)
                    if result and 'performance_metrics' in result:
                        metrics = result['performance_metrics']
                        comparison_data.append({
                            'Strategy': strategy,
                            'Total Return (%)': metrics.get('total_return', 0) * 100,
                            'Win Rate (%)': metrics.get('win_rate', 0) * 100,
                            'Total Trades': result.get('total_trades', 0),
                            'Final Capital': result.get('final_capital', 0)
                        })
                
                if comparison_data:
                    df = pd.DataFrame(comparison_data)
                    st.dataframe(df, use_container_width=True)
                    
                    # Графік порівняння
                    fig = px.bar(df, x='Strategy', y='Total Return (%)', 
                                title="Strategy Performance Comparison")
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("### 🤖 AI Confidence Analysis")
        
        analysis_strategy = st.selectbox("Select Strategy", all_strategies, key="analysis_strategy")
        analysis_days = st.slider("Analysis Days", 7, 90, 30, key="analysis_days")
        
        if st.button("Run Confidence Analysis", key="run_analysis"):
            with st.spinner("Analyzing confidence levels..."):
                confidence_data = fetch_confidence_analysis(analysis_strategy, asset, analysis_days)
                if confidence_data:
                    st.json(confidence_data)

# Сторінка Backtesting - ВИПРАВЛЕНА ВЕРСІЯ
def show_backtesting_page():
    st.markdown("## 🤖 Backtesting Engine")
    
    col1, col2 = st.columns(2)
    
    with col1:
        lookback = st.slider("Lookback Period", 100, 10000, 1000, key="backtest_main")
        strategy_select = st.selectbox("Select Strategy", all_strategies, key="backtest_strategy_main")
    
    with col2:
        capital = st.number_input("Initial Capital", 1000, 100000, 10000, key="backtest_capital")
        use_ai = st.checkbox("Use AI Filtering", value=True, key="backtest_use_ai")
        min_confidence = st.slider("Min Confidence", 0.0, 1.0, 0.6, 0.1, key="backtest_confidence")
    
    if st.button("🚀 Run Comprehensive Backtest", type="primary", key="run_comprehensive_backtest"):
        if not strategy_select or strategy_select == "None":
            st.error("Please select a valid strategy.")
            return
            
        with st.spinner("Running comprehensive backtest..."):
            # Виконання backtest через різні API
            backtest_results = run_backtest(
                asset, lookback, capital, strategy_select, use_ai, min_confidence
            )
            
            if backtest_results:
                st.success("Backtest completed successfully!")
                
                # Відображення результатів
                col1, col2, col3, col4 = st.columns(4)
                
                # Основні метрики
                with col1:
                    st.metric("Total Return", f"{backtest_results.get('total_return_percent', 0):.2f}%")
                with col2:
                    st.metric("Win Rate", f"{backtest_results.get('win_rate', 0)*100:.1f}%")
                with col3:
                    st.metric("Total Trades", backtest_results.get('total_trades', 0))
                with col4:
                    st.metric("Final Capital", f"${backtest_results.get('final_capital', 0):.2f}")
                
                # Додаткові метрики AI - ВИПРАВЛЕНА ВЕРСІЯ
                if use_ai and 'ai_metrics' in backtest_results:
                    st.markdown("### 🤖 AI Performance Metrics")
                    ai_metrics = backtest_results['ai_metrics']
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # Відображаємо фільтрацію сигналів
                        original_signals = ai_metrics.get('original_signals', 0)
                        filtered_signals = ai_metrics.get('filtered_signals', 0)
                        filter_ratio = ai_metrics.get('filter_ratio', 0) * 100
                        st.metric("Signals Filtered", f"{filter_ratio:.1f}%")
                    
                    with col2:
                        # Показуємо кількість відфільтрованих сигналів
                        signals_passed = original_signals - filtered_signals
                        st.metric("Signals Passed", f"{signals_passed}/{original_signals}")
                    
                    with col3:
                        # Показуємо мінімальну впевненість
                        min_conf = ai_metrics.get('min_confidence', 0) * 100
                        st.metric("Min Confidence", f"{min_conf:.1f}%")
                
                # Детальна інформація
                with st.expander("Detailed Backtest Results"):
                    st.json(backtest_results)
                
                # Історія торгів
                if 'trades' in backtest_results and backtest_results['trades']:
                    st.markdown("### 📋 Trade History")
                    trades_df = pd.DataFrame(backtest_results['trades'])
                    
                    # Додаємо AI confidence до таблиці, якщо є
                    if 'ai_confidence' in trades_df.columns:
                        # Відображаємо тільки ключові колонки
                        display_columns = ['entry_time', 'entry_price', 'type', 'exit_price', 'pnl', 'ai_confidence']
                        available_columns = [col for col in display_columns if col in trades_df.columns]
                        st.dataframe(trades_df[available_columns], use_container_width=True)
                    else:
                        st.dataframe(trades_df, use_container_width=True)
                
                # Portfolio Values Chart
                if 'portfolio_values' in backtest_results and backtest_results['portfolio_values']:
                    st.markdown("### 📈 Portfolio Value Over Time")
                    portfolio_df = pd.DataFrame(backtest_results['portfolio_values'])
                    
                    if not portfolio_df.empty and 'timestamp' in portfolio_df.columns and 'value' in portfolio_df.columns:
                        fig = px.line(portfolio_df, x='timestamp', y='value', 
                                    title="Portfolio Value Over Time",
                                    labels={'value': 'Portfolio Value ($)', 'timestamp': 'Time'})
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)

# Сторінка Asset Analysis
def show_asset_analysis_page():
    st.markdown("## 🔍 Asset Analysis")
    
    tab1, tab2 = st.tabs(["Backtesting", "AI Analysis"])
    
    with tab1:
        st.markdown("### 🤖 Backtesting Analysis")
        lookback = st.slider("Lookback Period", 100, 1000, 100, key="asset_backtest_lookback")
        strategy_select = st.selectbox("Select Strategy", all_strategies, key="asset_backtest_strategy")
        
        if st.button("Run Backtest", key="asset_run_backtest"):
            if not strategy_select or strategy_select == "None":
                st.error("Please select a valid strategy.")
                return
                
            with st.spinner("Running backtest..."):
                backtest_results = run_backtest(asset, lookback, initial_capital, strategy_select)
                if backtest_results:
                    # Display summary metrics
                    if 'performance_metrics' in backtest_results:
                        metrics = backtest_results['performance_metrics']
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Return", f"{metrics.get('total_return', 0)*100:.2f}%")
                        with col2:
                            st.metric("Win Rate", f"{metrics.get('win_rate', 0)*100:.2f}%")
                        with col3:
                            st.metric("Total Trades", backtest_results.get('total_trades', 0))
                        with col4:
                            st.metric("Final Capital", f"${backtest_results.get('final_capital', 0):.2f}")
                    
                    # Display trades table
                    if 'trades' in backtest_results and backtest_results['trades']:
                        st.markdown("### 📋 Trade History")
                        trades_df = pd.DataFrame(backtest_results['trades'])
                        st.dataframe(trades_df, use_container_width=True)
    
    with tab2:
        st.markdown("### 🤖 AI Confidence Analysis")
        
        analysis_strategy = st.selectbox("Select Strategy", all_strategies, key="asset_analysis_strategy")
        
        if st.button("Run Confidence Analysis", key="asset_run_analysis"):
            if not analysis_strategy or analysis_strategy == "None":
                st.error("Please select a valid strategy.")
                return
                
            with st.spinner("Analyzing confidence levels..."):
                confidence_data = fetch_confidence_analysis(analysis_strategy, asset, days)
                if confidence_data:
                    st.json(confidence_data)

# Сторінка Asset Comparison
# Сторінка Asset Comparison - ВИПРАВЛЕНА ВЕРСІЯ
def show_asset_comparison_page():
    st.markdown("## 📊 Asset Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_assets = st.multiselect(
            "Select Assets to Compare:",
            available_assets,
            default=available_assets[:3] if len(available_assets) >= 3 else available_assets
        )
        lookback = st.slider("Lookback Period", 100, 1000, 100, key="comparison_lookback")
    
    with col2:
        comparison_strategy = st.selectbox("Strategy for Comparison", all_strategies, key="comparison_strategy")
        use_ai = st.checkbox("Use AI for Comparison", value=True, key="comparison_ai")
    
    if st.button("Compare Assets", key="compare_assets"):
        if not selected_assets:
            st.warning("Please select at least one asset for comparison.")
            return
        
        if not comparison_strategy or comparison_strategy == "None":
            st.error("Please select a valid strategy.")
            return
            
        with st.spinner("Comparing assets..."):
            comparison_data = []
            
            for comp_asset in selected_assets:
                result = run_backtest(comp_asset, lookback, 10000, comparison_strategy, use_ai)
                
                if result and "error" not in result:
                    # ВИПРАВЛЕННЯ: Використовуємо правильні поля з відповіді API
                    total_return = result.get('total_return_percent', 0)
                    win_rate = result.get('win_rate', 0) * 100  # Конвертуємо у відсотки
                    total_trades = result.get('total_trades', 0)
                    final_capital = result.get('final_capital', 0)
                    total_pnl = result.get('total_pnl', 0)
                    
                    # Додаємо AI метрики, якщо доступні
                    ai_metrics = result.get('ai_metrics', {})
                    
                    comparison_data.append({
                        'Asset': comp_asset,
                        'Total Return (%)': total_return,
                        'Win Rate (%)': win_rate,
                        'Total Trades': total_trades,
                        'Final Capital': final_capital,
                        'Total PnL': total_pnl,
                        'AI Filter Ratio (%)': ai_metrics.get('filter_ratio', 0) * 100
                    })
            
            if comparison_data:
                comparison_df = pd.DataFrame(comparison_data)
                
                # Display summary statistics
                st.markdown("### 📈 Comparison Summary")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Assets", len(comparison_df))
                with col2:
                    positive_returns = len(comparison_df[comparison_df['Total Return (%)'] > 0])
                    st.metric("Profitable Assets", positive_returns)
                with col3:
                    avg_win_rate = comparison_df['Win Rate (%)'].mean()
                    st.metric("Avg Win Rate", f"{avg_win_rate:.1f}%")
                with col4:
                    best_return = comparison_df['Total Return (%)'].max()
                    st.metric("Best Return", f"{best_return:.2f}%")
                
                # Display comparison table
                st.markdown("### 📋 Detailed Comparison")
                st.dataframe(comparison_df, use_container_width=True)
                
                # Top performers
                st.markdown("### 🏆 Top Performers by Return")
                top_performers = comparison_df.nlargest(5, 'Total Return (%)')[['Asset', 'Total Return (%)', 'Win Rate (%)', 'Total Trades']]
                st.dataframe(top_performers, use_container_width=True)
                
                # Графік порівняння
                fig = px.bar(comparison_df, x='Asset', y='Total Return (%)', 
                            title="Asset Performance Comparison",
                            color='Total Return (%)',
                            color_continuous_scale='RdYlGn')
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
                
                # Додаткові графіки
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_winrate = px.bar(comparison_df, x='Asset', y='Win Rate (%)',
                                       title="Win Rate Comparison",
                                       color='Win Rate (%)',
                                       color_continuous_scale='RdYlGn')
                    fig_winrate.update_layout(height=400)
                    st.plotly_chart(fig_winrate, use_container_width=True)
                
                with col2:
                    fig_trades = px.bar(comparison_df, x='Asset', y='Total Trades',
                                      title="Trading Activity",
                                      color='Total Trades',
                                      color_continuous_scale='Blues')
                    fig_trades.update_layout(height=400)
                    st.plotly_chart(fig_trades, use_container_width=True)
                    
            else:
                st.error("No comparison data available. Possible reasons:")
                st.write("- API server is not running")
                st.write("- Selected assets don't have data")
                st.write("- Backtest returned errors")
                
                # Додаємо діагностику
                with st.expander("🔍 Debug Information"):
                    for comp_asset in selected_assets:
                        result = run_backtest(comp_asset, lookback, 10000, comparison_strategy, use_ai)
                        st.write(f"**{comp_asset}**: {result}")

# Головна навігація
if page == "Market Overview":
    show_market_overview_page()
elif page == "Strategy Dashboard":
    show_strategy_dashboard_page()
elif page == "Asset Analysis":
    show_asset_analysis_page()
elif page == "Backtesting":
    show_backtesting_page()
elif page == "Asset Comparison":
    show_asset_comparison_page()
elif page == "Strategy Library":
    show_strategy_library_page()

# Загальна інформація про оновлення
st.markdown("---")
st.markdown(f"*Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*")
st.markdown(f"*API Base URL: {API_BASE_URL}*")