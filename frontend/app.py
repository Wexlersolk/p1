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
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .parameter-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 3px solid #28a745;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Базовий URL API
API_BASE_URL = "http://localhost:8080"

# Заголовок
st.markdown('<h1 class="main-header">🎯 Trading Analytics Dashboard</h1>', unsafe_allow_html=True)

# Бічна панель для налаштувань
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Навігація
    page = st.selectbox(
        "Select Page:",
        ["Market Overview", "Strategy Dashboard", "Asset Analysis", "Backtesting", "Asset Comparison", "Strategy Library"]
    )
    
    # Отримуємо список доступних активів
    @st.cache_data(ttl=3600)
    def fetch_available_assets():
        try:
            response = requests.get(f"{API_BASE_URL}/", timeout=30)
            response.raise_for_status()
            return response.json()
        except:
            return ["Binance_Spot_XRP_1d", "Binance_Spot_BTC_1h", "Coinbase_Spot_ETH_1d"]
    
    available_assets = fetch_available_assets()
    
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
    
    if page in ["Backtesting", "Asset Comparison", "Strategy Library"]:
        # Отримуємо список стратегій
        @st.cache_data(ttl=3600)
        def fetch_all_strategies():
            try:
                response = requests.get(f"{API_BASE_URL}/api/v1/strategies/", timeout=30)
                response.raise_for_status()
                data = response.json()
                return list(data.get('strategies', {}).keys())
            except:
                return ["vwap_ib", "sma_crossover", "rsi_oversold"]
        
        all_strategies = fetch_all_strategies()
        strategy_id = st.selectbox("Strategy:", all_strategies, index=0)
    
    if st.button("🔄 Refresh Data"):
        st.rerun()

# Функції для Strategies API
@st.cache_data(ttl=3600)
def fetch_all_strategies():
    """Get all available strategies"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/strategies/", timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching strategies: {e}")
        return None

@st.cache_data(ttl=3600)
def fetch_strategy_info(strategy_id):
    """Get detailed information about a specific strategy"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/strategies/{strategy_id}", timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
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
            f"{API_BASE_URL}/api/v1/strategies/train/{strategy_id}",
            params={"asset": asset},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error training strategy model: {e}")
        return None

# Функції для API ендпоінтів
@st.cache_data(ttl=300)
def fetch_asset_data(asset, limit=100):
    """Get OHLCV data for a specific asset"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/{asset}/data",
            params={"limit": limit},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching asset data: {e}")
        return None

@st.cache_data(ttl=300)
def fetch_asset_info(asset):
    """Get general information about an asset"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/{asset}/info",
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching asset info: {e}")
        return None

@st.cache_data(ttl=3600)
def fetch_exchanges():
    """List all available exchanges"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/exchanges",
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching exchanges: {e}")
        return None

@st.cache_data(ttl=3600)
def fetch_timeframes():
    """List all available timeframes"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/timeframes",
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching timeframes: {e}")
        return None

@st.cache_data(ttl=300)
def fetch_asset_comparison(lookback=100, strategy_id="vwap_ib"):
    """Compare assets"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/compare",
            params={"lookback": lookback, "strategy_id": strategy_id},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching asset comparison: {e}")
        return None

@st.cache_data(ttl=300)
def run_backtest(asset, lookback=100, initial_capital=10000, strategy_id="vwap_ib"):
    """Run backtest for a specific asset"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/{asset}",
            params={"lookback": lookback, "initial_capital": initial_capital, "strategy_id": strategy_id},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error running backtest: {e}")
        return None

@st.cache_data(ttl=300)
def fetch_metrics(asset, lookback=100):
    """Get performance metrics for a specific asset"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/metrics/{asset}",
            params={"lookback": lookback},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching metrics: {e}")
        return None

# Існуючі функції для visualization endpoints
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

# Сторінка Strategy Library
def show_strategy_library_page():
    st.markdown("## 📚 Strategy Library")
    
    # Отримуємо всі стратегії
    with st.spinner("Loading strategies..."):
        strategies_data = fetch_all_strategies()
    
    if not strategies_data:
        st.error("Failed to load strategies data.")
        return
    
    tab1, tab2, tab3 = st.tabs(["All Strategies", "Strategy Details", "ML Training"])
    
    with tab1:
        st.markdown("### 📊 All Available Strategies")
        
        # Відображаємо стратегії по категоріях
        categories = strategies_data.get('categories', {})
        
        for category_name, category_strategies in categories.items():
            st.markdown(f"#### 🏷️ {category_name.replace('_', ' ').title()}")
            
            for strategy_id, strategy_info in category_strategies.items():
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
                        if st.button(f"View Details", key=f"view_{strategy_id}"):
                            st.session_state.selected_strategy = strategy_id
    
    with tab2:
        st.markdown("### 🔍 Strategy Details")
        
        # Вибір стратегії для детального перегляду
        selected_strategy = st.selectbox(
            "Select Strategy for Detailed View:",
            options=list(strategies_data.get('strategies', {}).keys()),
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
                test_lookback = st.slider("Lookback Period", 100, 1000, 100, key=f"test_{selected_strategy}")
                
                if st.button("Get Strategy Signals", key=f"signals_{selected_strategy}"):
                    with st.spinner("Fetching strategy signals..."):
                        signals = fetch_strategy_signals(selected_strategy, asset, test_lookback)
                        if signals:
                            st.json(signals)
    
    with tab3:
        st.markdown("### 🤖 ML Model Training")
        
        st.info("""
        **ML-Validated Strategies** use machine learning to filter trading signals based on historical performance patterns.
        Train ML models to improve strategy accuracy and reduce false signals.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            ml_strategy = st.selectbox(
                "Select ML Strategy to Train:",
                options=[s for s in all_strategies if 'ml' in s.lower()],
                key="ml_training_strategy"
            )
            
            training_asset = st.selectbox(
                "Training Asset:",
                options=available_assets,
                key="training_asset"
            )
        
        with col2:
            st.markdown("#### Training Information")
            st.write("ML training uses historical data to learn which signals are most likely to be profitable.")
            st.write("Training process is asynchronous and may take several minutes.")
        
        if st.button("🚀 Train ML Model", type="primary", key="train_ml_model"):
            with st.spinner("Initiating ML model training..."):
                training_result = train_strategy_model(ml_strategy, training_asset)
                if training_result:
                    st.success(f"✅ {training_result.get('message', 'Training initiated successfully!')}")
                    st.info("Training is running in the background. Check back later for results.")

# Сторінка Market Overview
def show_market_overview_page():
    st.markdown("## 📈 Market Overview")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Asset Data", "Asset Info", "Exchanges", "Timeframes", "Available Assets"])
    
    with tab1:
        st.markdown("### 📊 OHLCV Data")
        if st.button("Load Asset Data", key="load_asset_data"):
            with st.spinner("Loading asset data..."):
                asset_data = fetch_asset_data(asset, data_limit)
                if asset_data:
                    if isinstance(asset_data, list):
                        df = pd.DataFrame(asset_data)
                        st.dataframe(df, use_container_width=True)
                        
                        # Candlestick chart
                        if all(col in df.columns for col in ['open', 'high', 'low', 'close', 'timestamp']):
                            fig = go.Figure(data=[go.Candlestick(
                                x=df['timestamp'],
                                open=df['open'],
                                high=df['high'],
                                low=df['low'],
                                close=df['close'],
                                name=asset
                            )])
                            fig.update_layout(
                                title=f"{asset} Price Chart",
                                xaxis_title="Time",
                                yaxis_title="Price",
                                height=500
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Line chart for close price
                            fig_line = px.line(df, x='timestamp', y='close', title=f"{asset} Close Price")
                            fig_line.update_layout(height=400)
                            st.plotly_chart(fig_line, use_container_width=True)
                    else:
                        st.write("Data format:", asset_data)
    
    with tab2:
        st.markdown("### ℹ️ Asset Information")
        if st.button("Load Asset Info", key="load_asset_info"):
            with st.spinner("Loading asset information..."):
                asset_info = fetch_asset_info(asset)
                if asset_info:
                    st.json(asset_info)
                    
                    # Display key metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Rows", asset_info.get('rows', 0))
                    with col2:
                        st.metric("Mean Price", f"${asset_info.get('mean_price', 0):.4f}")
                    with col3:
                        st.metric("Min Price", f"${asset_info.get('min_price', 0):.4f}")
                    with col4:
                        st.metric("Max Price", f"${asset_info.get('max_price', 0):.4f}")
    
    with tab3:
        st.markdown("### 🏢 Exchanges")
        if st.button("Load Exchanges", key="load_exchanges"):
            with st.spinner("Loading exchanges..."):
                exchanges = fetch_exchanges()
                if exchanges:
                    if isinstance(exchanges, list):
                        st.dataframe(pd.DataFrame(exchanges, columns=["Exchange"]), use_container_width=True)
                    else:
                        st.write(exchanges)
    
    with tab4:
        st.markdown("### ⏰ Timeframes")
        if st.button("Load Timeframes", key="load_timeframes"):
            with st.spinner("Loading timeframes..."):
                timeframes = fetch_timeframes()
                if timeframes:
                    if isinstance(timeframes, list):
                        st.dataframe(pd.DataFrame(timeframes, columns=["Timeframe"]), use_container_width=True)
                    else:
                        st.write(timeframes)
    
    with tab5:
        st.markdown("### 📋 Available Assets")
        st.write(f"Total available assets: {len(available_assets)}")
        st.dataframe(pd.DataFrame(available_assets, columns=["Asset"]), use_container_width=True)

# Сторінка Asset Analysis
def show_asset_analysis_page():
    st.markdown("## 🔍 Asset Analysis")
    
    tab1, tab2 = st.tabs(["Backtesting", "Performance Metrics"])
    
    with tab1:
        st.markdown("### 🤖 Backtesting")
        lookback = st.slider("Lookback Period", 100, 1000, 100, key="backtest_lookback")
        strategy_select = st.selectbox("Select Strategy", all_strategies, key="backtest_strategy")
        
        if st.button("Run Backtest", key="run_backtest"):
            with st.spinner("Running backtest..."):
                backtest_results = run_backtest(asset, lookback, 10000, strategy_select)
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
                    
                    # Detailed results
                    with st.expander("Detailed Backtest Results"):
                        st.json(backtest_results)
    
    with tab2:
        st.markdown("### 📊 Performance Metrics")
        lookback = st.slider("Lookback Period", 100, 1000, 100, key="metrics_lookback")
        
        if st.button("Load Metrics", key="load_metrics"):
            with st.spinner("Loading performance metrics..."):
                metrics = fetch_metrics(asset, lookback)
                if metrics:
                    st.json(metrics)

# Сторінка Strategy Dashboard
def show_strategy_dashboard_page():
    with st.spinner("🔄 Loading dashboard data..."):
        dashboard_data = fetch_dashboard_data(asset, days, initial_capital)

    if not dashboard_data:
        st.error("Failed to load dashboard data. Please check if the API server is running.")
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
        
        try:
            equity_data = dashboard_data['charts']['equity_curve']
            
            if isinstance(equity_data, str):
                equity_data = json.loads(equity_data)
            
            fig = go.Figure()
            
            # Додаємо кожну стратегію на графік
            for trace in equity_data.get('data', []):
                fig.add_trace(go.Scatter(
                    x=trace.get('x', []),
                    y=trace.get('y', []),
                    mode='lines',
                    name=trace.get('name', 'Unknown'),
                    line=dict(width=3),
                    hovertemplate=trace.get('hovertemplate', '')
                ))
            
            fig.update_layout(
                title="Strategy Performance - Equity Curve",
                xaxis_title="Time",
                yaxis_title="Portfolio Value ($)",
                hovermode="x unified",
                height=500,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error rendering equity curve: {e}")

    # Returns Comparison
    if 'charts' in dashboard_data and 'returns_chart' in dashboard_data['charts']:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Total Returns")
            try:
                returns_data = dashboard_data['charts']['returns_chart']
                
                if isinstance(returns_data, str):
                    returns_data = json.loads(returns_data)
                
                # Створюємо бар chart для доходностей
                strategies = []
                returns = []
                
                if 'metrics' in dashboard_data:
                    for strategy_id, metrics in dashboard_data['metrics'].items():
                        strategies.append(metrics.get('name', strategy_id))
                        returns.append(metrics.get('total_return', 0))
                
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
                    
            except Exception as e:
                st.error(f"Error rendering returns chart: {e}")
        
        with col2:
            st.markdown("### 🎯 Win Rate")
            try:
                # Аналогічно для Win Rate
                strategies = []
                win_rates = []
                
                if 'metrics' in dashboard_data:
                    for strategy_id, metrics in dashboard_data['metrics'].items():
                        strategies.append(metrics.get('name', strategy_id))
                        win_rates.append(metrics.get('win_rate', 0))
                
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
                    
            except Exception as e:
                st.error(f"Error rendering win rate chart: {e}")

    # Детальні метрики стратегій
    st.markdown("## 🔍 Detailed Strategy Metrics")

    if 'metrics' in dashboard_data:
        metrics_df_data = []
        
        for strategy_id, metrics in dashboard_data['metrics'].items():
            metrics_df_data.append({
                'Strategy': metrics.get('name', strategy_id),
                'Total Return (%)': metrics.get('total_return', 0),
                'Win Rate (%)': metrics.get('win_rate', 0),
                'Max Drawdown (%)': metrics.get('max_drawdown', 0),
                'Total Trades': metrics.get('total_trades', 0),
                'Avg Win (%)': metrics.get('avg_win', 0),
                'Avg Loss (%)': metrics.get('avg_loss', 0),
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

    # ML Signal Timeline
    st.markdown("---")
    st.markdown("## 📈 ML Signal Timeline")
    
    selected_strategy = st.selectbox(
        "Select Strategy for Signal Analysis:",
        options=dashboard_data.get('strategies_tested', []) if dashboard_data else [],
        key="signal_strategy_select"
    )

    if st.button("🔄 Load Signal Timeline", key="load_signals"):
        with st.spinner("Loading ML signal timeline..."):
            signal_data = fetch_signal_timeline(selected_strategy, asset, days)
            if signal_data:
                display_signal_timeline(signal_data, selected_strategy, asset)

# Сторінка Backtesting
def show_backtesting_page():
    st.markdown("## 🤖 Backtesting Engine")
    
    col1, col2 = st.columns(2)
    
    with col1:
        lookback = st.slider("Lookback Period", 100, 10000, 1000, key="backtest_main")
        strategy_select = st.selectbox("Select Strategy", all_strategies, key="backtest_strategy_main")
    
    with col2:
        capital = st.number_input("Initial Capital", 1000, 100000, 10000, key="backtest_capital")
        risk_per_trade = st.slider("Risk per Trade %", 1.0, 10.0, 2.0, key="backtest_risk")
    
    if st.button("🚀 Run Comprehensive Backtest", type="primary", key="run_comprehensive_backtest"):
        with st.spinner("Running comprehensive backtest..."):
            # Виконання backtest через різні API
            backtest_results = run_backtest(asset, lookback, capital, strategy_select)
            
            if backtest_results:
                st.success("Backtest completed successfully!")
                
                # Відображення результатів
                col1, col2, col3, col4 = st.columns(4)
                
                if 'performance_metrics' in backtest_results:
                    metrics = backtest_results['performance_metrics']
                    with col1:
                        st.metric("Total Return", f"{metrics.get('total_return', 0)*100:.2f}%")
                    with col2:
                        st.metric("Win Rate", f"{metrics.get('win_rate', 0)*100:.2f}%")
                    with col3:
                        st.metric("Max Drawdown", f"{metrics.get('max_drawdown', 0)*100:.2f}%")
                    with col4:
                        st.metric("Total Trades", backtest_results.get('total_trades', 0))
                
                # Детальна інформація
                with st.expander("Detailed Backtest Results"):
                    st.json(backtest_results)

# Сторінка Asset Comparison
def show_asset_comparison_page():
    st.markdown("## 📊 Asset Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        lookback = st.slider("Lookback Period", 100, 1000, 100, key="comparison_lookback")
    
    with col2:
        comparison_strategy = st.selectbox("Strategy for Comparison", all_strategies, key="comparison_strategy")
    
    if st.button("Compare Assets", key="compare_assets"):
        with st.spinner("Loading asset comparison..."):
            comparison_data = fetch_asset_comparison(lookback, comparison_strategy)
            if comparison_data and isinstance(comparison_data, list):
                # Convert to DataFrame for better display
                comparison_df = pd.DataFrame(comparison_data)
                
                # Display summary statistics
                st.markdown("### 📈 Comparison Summary")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Assets", len(comparison_df))
                with col2:
                    positive_returns = len(comparison_df[comparison_df['total_return'] > 0])
                    st.metric("Profitable Assets", positive_returns)
                with col3:
                    avg_win_rate = comparison_df['win_rate'].mean() * 100
                    st.metric("Avg Win Rate", f"{avg_win_rate:.1f}%")
                with col4:
                    best_return = comparison_df['total_return'].max()
                    st.metric("Best Return", f"{best_return:.2f}%")
                
                # Display comparison table
                st.markdown("### 📋 Detailed Comparison")
                st.dataframe(comparison_df, use_container_width=True)
                
                # Top performers
                st.markdown("### 🏆 Top Performers")
                top_performers = comparison_df.nlargest(5, 'total_return')[['asset', 'total_return', 'win_rate', 'total_trades']]
                st.dataframe(top_performers, use_container_width=True)
            else:
                st.error("No comparison data available")

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