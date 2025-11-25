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

def compute_performance_metrics(trades, initial_capital):
    """Обчислює метрики продуктивності з історії торгів"""
    if not trades:
        return {}
    
    total_trades = len(trades)
    total_pnl = sum(trade.get('pnl', 0) for trade in trades)
    total_return_percent = (total_pnl / initial_capital) * 100
    final_capital = initial_capital + total_pnl
    
    # Обчислюємо win rate
    winning_trades = sum(1 for trade in trades if trade.get('pnl', 0) > 0)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    # Обчислюємо середній прибуток та збитки
    winning_pnls = [trade.get('pnl', 0) for trade in trades if trade.get('pnl', 0) > 0]
    losing_pnls = [trade.get('pnl', 0) for trade in trades if trade.get('pnl', 0) < 0]
    
    avg_win = np.mean(winning_pnls) if winning_pnls else 0
    avg_loss = np.mean(losing_pnls) if losing_pnls else 0
    
    # Обчислюємо максимальну просадку
    cumulative_pnl = 0
    peak = initial_capital
    max_drawdown = 0
    
    for trade in trades:
        cumulative_pnl += trade.get('pnl', 0)
        current_capital = initial_capital + cumulative_pnl
        if current_capital > peak:
            peak = current_capital
        drawdown = (peak - current_capital) / peak * 100
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    return {
        'total_trades': total_trades,
        'total_pnl': total_pnl,
        'total_return_percent': total_return_percent,
        'final_capital': final_capital,
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'max_drawdown': max_drawdown
    }

def create_equity_curve(trades, initial_capital):
    """Створює криву капіталу з історії торгів"""
    if not trades:
        return pd.DataFrame()
    
    # Сортуємо угоди за часом виходу
    sorted_trades = sorted(trades, key=lambda x: x.get('exit_time', ''))
    
    equity_data = []
    current_capital = initial_capital
    
    for trade in sorted_trades:
        current_capital += trade.get('pnl', 0)
        equity_data.append({
            'timestamp': trade.get('exit_time', ''),
            'value': current_capital
        })
    
    return pd.DataFrame(equity_data)

# Сторінка Market Overview - ВИПРАВЛЕНА ВЕРСІЯ
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
        col1, col2 = st.columns(2)
        
        with col1:
            quick_strategy = st.selectbox("Strategy", all_strategies, key="quick_strategy")
            quick_lookback = st.slider("Lookback", 100, 1000, 100, key="quick_lookback")
        
        with col2:
            quick_capital = st.number_input("Initial Capital", 1000, 50000, 10000, key="quick_capital")
            use_ai = st.checkbox("Use AI Filtering", value=True, key="quick_ai")
            min_confidence = st.slider("Min Confidence", 0.0, 1.0, 0.6, 0.1, key="quick_confidence")
        
        if st.button("Run Quick Backtest", key="quick_backtest"):
            with st.spinner("Running quick backtest..."):
                result = run_backtest(asset, quick_lookback, quick_capital, quick_strategy, use_ai, min_confidence)
                if result:
                    # ВИПРАВЛЕННЯ: Використовуємо правильні поля з відповіді API
                    total_trades = len(result.get('trades', []))
                    
                    # Обчислюємо загальний PnL з усіх угод
                    total_pnl = sum(trade.get('pnl', 0) for trade in result.get('trades', []))
                    total_return_percent = (total_pnl / quick_capital) * 100
                    
                    # Обчислюємо win rate
                    winning_trades = sum(1 for trade in result.get('trades', []) if trade.get('pnl', 0) > 0)
                    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                    
                    final_capital = quick_capital + total_pnl
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Return", f"{total_return_percent:.2f}%")
                    with col2:
                        st.metric("Win Rate", f"{win_rate:.1f}%")
                    with col3:
                        st.metric("Total Trades", total_trades)
                    with col4:
                        st.metric("Final Capital", f"${final_capital:.2f}")
                    
                    # Показуємо історію торгів
                    if result.get('trades'):
                        st.markdown("#### 📋 Recent Trades")
                        trades_df = pd.DataFrame(result['trades'])
                        
                        # Відображаємо тільки ключові колонки
                        display_cols = ['entry_time', 'entry_price', 'type', 'exit_price', 'pnl']
                        if 'ai_confidence' in trades_df.columns:
                            display_cols.append('ai_confidence')
                        
                        available_cols = [col for col in display_cols if col in trades_df.columns]
                        st.dataframe(trades_df[available_cols].head(10), use_container_width=True)
                else:
                    st.error("Failed to run backtest. Please check if the API server is running.")
    
    with tab2:
        st.markdown("### 📈 Strategy Comparison")
        
        # Порівняння стратегій для обраного активу
        comparison_strategies = st.multiselect(
            "Select strategies to compare:",
            all_strategies,
            default=all_strategies[:3] if len(all_strategies) >= 3 else all_strategies,
            key="comparison_strategies_market"
        )
        
        comparison_lookback = st.slider("Lookback Period", 100, 1000, 100, key="comparison_lookback_market")
        comparison_capital = st.number_input("Initial Capital", 1000, 50000, 10000, key="comparison_capital_market")
        
        if st.button("Compare Strategies", key="compare_strategies_market"):
            if not comparison_strategies:
                st.warning("Please select at least one strategy for comparison.")
            else:
                with st.spinner("Comparing strategies..."):
                    comparison_data = []
                    for strategy in comparison_strategies:
                        result = run_backtest(asset, comparison_lookback, comparison_capital, strategy)
                        if result:
                            trades = result.get('trades', [])
                            total_trades = len(trades)
                            
                            if total_trades > 0:
                                total_pnl = sum(trade.get('pnl', 0) for trade in trades)
                                winning_trades = sum(1 for trade in trades if trade.get('pnl', 0) > 0)
                                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                                total_return_percent = (total_pnl / comparison_capital) * 100
                                final_capital = comparison_capital + total_pnl
                                
                                comparison_data.append({
                                    'Strategy': strategy,
                                    'Total Return (%)': total_return_percent,
                                    'Win Rate (%)': win_rate,
                                    'Total Trades': total_trades,
                                    'Final Capital': final_capital,
                                    'Total PnL': total_pnl
                                })
                    
                    if comparison_data:
                        df = pd.DataFrame(comparison_data)
                        
                        # Сортування за найкращою доходністю
                        df = df.sort_values('Total Return (%)', ascending=False)
                        
                        st.dataframe(df, use_container_width=True)
                        
                        # Графік порівняння
                        fig = px.bar(df, x='Strategy', y='Total Return (%)', 
                                    title="Strategy Performance Comparison",
                                    color='Total Return (%)',
                                    color_continuous_scale='RdYlGn')
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Додаткові графіки
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fig_winrate = px.bar(df, x='Strategy', y='Win Rate (%)',
                                               title="Win Rate Comparison",
                                               color='Win Rate (%)',
                                               color_continuous_scale='Viridis')
                            st.plotly_chart(fig_winrate, use_container_width=True)
                        
                        with col2:
                            fig_trades = px.bar(df, x='Strategy', y='Total Trades',
                                              title="Trading Activity",
                                              color='Total Trades',
                                              color_continuous_scale='Blues')
                            st.plotly_chart(fig_trades, use_container_width=True)
                    else:
                        st.error("No valid backtest results to compare.")
    
    with tab3:
        st.markdown("### 🤖 AI Confidence Analysis")
        
        st.info("""
        AI Confidence Analysis shows how machine learning models filter trading signals based on historical patterns.
        Higher confidence thresholds typically result in fewer but more reliable trades.
        """)
        
        # Швидкий аналіз AI впевненості
        col1, col2 = st.columns(2)
        
        with col1:
            analysis_strategy = st.selectbox("Select Strategy", all_strategies, key="analysis_strategy_market")
            confidence_levels = st.multiselect(
                "Confidence Levels to Test:",
                [0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
                default=[0.5, 0.6, 0.7],
                key="confidence_levels_market"
            )
        
        with col2:
            analysis_lookback = st.slider("Lookback Period", 100, 1000, 200, key="analysis_lookback_market")
            analysis_capital = st.number_input("Initial Capital", 1000, 50000, 10000, key="analysis_capital_market")
        
        if st.button("Run Confidence Analysis", key="run_analysis_market"):
            if not confidence_levels:
                st.warning("Please select at least one confidence level.")
            else:
                with st.spinner("Analyzing confidence impact..."):
                    confidence_data = []
                    
                    for confidence in confidence_levels:
                        result = run_backtest(asset, analysis_lookback, analysis_capital, 
                                            analysis_strategy, use_ai=True, min_confidence=confidence)
                        
                        if result:
                            trades = result.get('trades', [])
                            total_trades = len(trades)
                            
                            if total_trades > 0:
                                total_pnl = sum(trade.get('pnl', 0) for trade in trades)
                                winning_trades = sum(1 for trade in trades if trade.get('pnl', 0) > 0)
                                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                                total_return_percent = (total_pnl / analysis_capital) * 100
                                
                                # Обчислюємо середню впевненість
                                avg_confidence = np.mean([trade.get('ai_confidence', 0) for trade in trades]) if trades else 0
                                
                                confidence_data.append({
                                    'Confidence Level': confidence,
                                    'Total Trades': total_trades,
                                    'Win Rate (%)': win_rate,
                                    'Total Return (%)': total_return_percent,
                                    'Avg Confidence': avg_confidence
                                })
                    
                    if confidence_data:
                        df = pd.DataFrame(confidence_data)
                        st.dataframe(df, use_container_width=True)
                        
                        # Графік впливу рівня впевненості
                        fig = px.line(df, x='Confidence Level', y='Total Return (%)',
                                    title="Impact of Confidence Level on Returns",
                                    markers=True)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fig_trades = px.bar(df, x='Confidence Level', y='Total Trades',
                                              title="Trades vs Confidence Level")
                            st.plotly_chart(fig_trades, use_container_width=True)
                        
                        with col2:
                            fig_winrate = px.bar(df, x='Confidence Level', y='Win Rate (%)',
                                               title="Win Rate vs Confidence Level")
                            st.plotly_chart(fig_winrate, use_container_width=True)
                    else:
                        st.error("No data available for confidence analysis.")

# Сторінка Strategy Dashboard - ВИПРАВЛЕНА ВЕРСІЯ
def show_strategy_dashboard_page():
    st.markdown("## 📈 Strategy Dashboard")
    
    # Швидкий доступ до backtesting
    col1, col2, col3 = st.columns(3)
    
    with col1:
        dashboard_strategy = st.selectbox("Select Strategy", all_strategies, key="dashboard_strategy")
    
    with col2:
        dashboard_lookback = st.slider("Lookback Period", 100, 1000, 500, key="dashboard_lookback")
    
    with col3:
        dashboard_capital = st.number_input("Initial Capital", 1000, 50000, initial_capital, key="dashboard_capital")
    
    if st.button("🚀 Run Strategy Analysis", key="run_dashboard_analysis"):
        with st.spinner("Running comprehensive strategy analysis..."):
            # Виконуємо backtest для обраної стратегії
            result = run_backtest(asset, dashboard_lookback, dashboard_capital, dashboard_strategy)
            
            if result:
                st.success("Strategy analysis completed!")
                
                # Обчислюємо метрики продуктивності
                trades = result.get('trades', [])
                metrics = compute_performance_metrics(trades, dashboard_capital)
                
                # Відображаємо основні метрики
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Return", f"{metrics.get('total_return_percent', 0):.2f}%")
                with col2:
                    st.metric("Win Rate", f"{metrics.get('win_rate', 0):.1f}%")
                with col3:
                    st.metric("Total Trades", metrics.get('total_trades', 0))
                with col4:
                    st.metric("Final Capital", f"${metrics.get('final_capital', 0):.2f}")
                
                # Додаткові метрики
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total PnL", f"${metrics.get('total_pnl', 0):.2f}")
                with col2:
                    st.metric("Avg Win", f"${metrics.get('avg_win', 0):.2f}")
                with col3:
                    st.metric("Avg Loss", f"${metrics.get('avg_loss', 0):.2f}")
                with col4:
                    st.metric("Max Drawdown", f"{metrics.get('max_drawdown', 0):.2f}%")
                
                # Крива капіталу
                st.markdown("### 📈 Equity Curve")
                equity_df = create_equity_curve(trades, dashboard_capital)
                
                if not equity_df.empty:
                    fig = px.line(equity_df, x='timestamp', y='value',
                                title="Portfolio Value Over Time",
                                labels={'value': 'Portfolio Value ($)', 'timestamp': 'Time'})
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Історія торгів
                st.markdown("### 📋 Trade History")
                if trades:
                    trades_df = pd.DataFrame(trades)
                    
                    # Відображаємо ключові колонки
                    display_cols = ['entry_time', 'entry_price', 'type', 'exit_price', 'pnl', 'pnl_percent']
                    if 'ai_confidence' in trades_df.columns:
                        display_cols.append('ai_confidence')
                    
                    available_cols = [col for col in display_cols if col in trades_df.columns]
                    st.dataframe(trades_df[available_cols], use_container_width=True)
                    
                    # Аналіз PnL
                    st.markdown("### 📊 PnL Distribution")
                    fig = px.histogram(trades_df, x='pnl', nbins=20, 
                                     title="Distribution of PnL per Trade")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No trades executed for this strategy and parameters.")
            else:
                st.error("Failed to run strategy analysis. Please check the API connection.")

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
                
                # Обчислюємо метрики
                trades = backtest_results.get('trades', [])
                metrics = compute_performance_metrics(trades, capital)
                
                # Відображення результатів
                col1, col2, col3, col4 = st.columns(4)
                
                # Основні метрики
                with col1:
                    st.metric("Total Return", f"{metrics.get('total_return_percent', 0):.2f}%")
                with col2:
                    st.metric("Win Rate", f"{metrics.get('win_rate', 0):.1f}%")
                with col3:
                    st.metric("Total Trades", metrics.get('total_trades', 0))
                with col4:
                    st.metric("Final Capital", f"${metrics.get('final_capital', 0):.2f}")
                
                # Додаткові метрики
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total PnL", f"${metrics.get('total_pnl', 0):.2f}")
                with col2:
                    st.metric("Avg Win", f"${metrics.get('avg_win', 0):.2f}")
                with col3:
                    st.metric("Avg Loss", f"${metrics.get('avg_loss', 0):.2f}")
                with col4:
                    st.metric("Max Drawdown", f"{metrics.get('max_drawdown', 0):.2f}%")
                
                # AI Metrics
                if use_ai and trades:
                    st.markdown("### 🤖 AI Performance Metrics")
                    
                    # Обчислюємо AI метрики
                    ai_confidences = [trade.get('ai_confidence', 0) for trade in trades if 'ai_confidence' in trade]
                    avg_ai_confidence = np.mean(ai_confidences) if ai_confidences else 0
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Avg AI Confidence", f"{avg_ai_confidence:.3f}")
                    
                    with col2:
                        high_confidence_trades = sum(1 for conf in ai_confidences if conf >= min_confidence)
                        st.metric("High Confidence Trades", high_confidence_trades)
                    
                    with col3:
                        st.metric("Min Confidence Threshold", f"{min_confidence:.1f}")
                
                # Детальна інформація
                with st.expander("Detailed Backtest Results"):
                    st.json(backtest_results)
                
                # Історія торгів
                if trades:
                    st.markdown("### 📋 Trade History")
                    trades_df = pd.DataFrame(trades)
                    
                    # Відображаємо ключові колонки
                    display_cols = ['entry_time', 'entry_price', 'type', 'exit_price', 'pnl', 'pnl_percent']
                    if 'ai_confidence' in trades_df.columns:
                        display_cols.append('ai_confidence')
                    
                    available_cols = [col for col in display_cols if col in trades_df.columns]
                    st.dataframe(trades_df[available_cols], use_container_width=True)
                
                # Крива капіталу
                st.markdown("### 📈 Portfolio Value Over Time")
                equity_df = create_equity_curve(trades, capital)
                
                if not equity_df.empty:
                    fig = px.line(equity_df, x='timestamp', y='value',
                                title="Portfolio Value Over Time",
                                labels={'value': 'Portfolio Value ($)', 'timestamp': 'Time'})
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Додаткові графіки
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # PnL distribution
                        fig_pnl = px.histogram(trades_df, x='pnl', nbins=20,
                                             title="PnL Distribution")
                        st.plotly_chart(fig_pnl, use_container_width=True)
                    
                    with col2:
                        # Win/Loss pie chart
                        win_loss_data = {
                            'Result': ['Winning Trades', 'Losing Trades'],
                            'Count': [
                                sum(1 for trade in trades if trade.get('pnl', 0) > 0),
                                sum(1 for trade in trades if trade.get('pnl', 0) < 0)
                            ]
                        }
                        fig_pie = px.pie(win_loss_data, values='Count', names='Result',
                                       title="Win/Loss Distribution")
                        st.plotly_chart(fig_pie, use_container_width=True)

# Сторінка Asset Analysis - ВИПРАВЛЕНА ВЕРСІЯ
def show_asset_analysis_page():
    st.markdown("## 🔍 Asset Analysis")
    
    tab1, tab2 = st.tabs(["Backtesting", "AI Analysis"])
    
    with tab1:
        st.markdown("### 🤖 Backtesting Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            lookback = st.slider("Lookback Period", 100, 1000, 100, key="asset_backtest_lookback")
            strategy_select = st.selectbox("Select Strategy", all_strategies, key="asset_backtest_strategy")
        
        with col2:
            capital = st.number_input("Initial Capital", 1000, 50000, initial_capital, key="asset_backtest_capital")
            use_ai = st.checkbox("Use AI Filtering", value=True, key="asset_backtest_ai")
            min_confidence = st.slider("Min Confidence", 0.0, 1.0, 0.6, 0.1, key="asset_backtest_confidence")
        
        if st.button("Run Backtest", key="asset_run_backtest"):
            if not strategy_select or strategy_select == "None":
                st.error("Please select a valid strategy.")
                return
                
            with st.spinner("Running backtest..."):
                backtest_results = run_backtest(asset, lookback, capital, strategy_select, use_ai, min_confidence)
                if backtest_results:
                    # Обчислюємо метрики
                    trades = backtest_results.get('trades', [])
                    metrics = compute_performance_metrics(trades, capital)
                    
                    # Display summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Return", f"{metrics.get('total_return_percent', 0):.2f}%")
                    with col2:
                        st.metric("Win Rate", f"{metrics.get('win_rate', 0):.1f}%")
                    with col3:
                        st.metric("Total Trades", metrics.get('total_trades', 0))
                    with col4:
                        st.metric("Final Capital", f"${metrics.get('final_capital', 0):.2f}")
                    
                    # Display trades table
                    if trades:
                        st.markdown("### 📋 Trade History")
                        trades_df = pd.DataFrame(trades)
                        
                        # Відображаємо ключові колонки
                        display_cols = ['entry_time', 'entry_price', 'type', 'exit_price', 'pnl']
                        if 'ai_confidence' in trades_df.columns:
                            display_cols.append('ai_confidence')
                        
                        available_cols = [col for col in display_cols if col in trades_df.columns]
                        st.dataframe(trades_df[available_cols], use_container_width=True)
    
    with tab2:
        st.markdown("### 🤖 AI Confidence Analysis")
        
        st.info("Analyze how AI confidence levels affect trading performance for this asset.")
        
        analysis_strategy = st.selectbox("Select Strategy", all_strategies, key="asset_analysis_strategy")
        confidence_thresholds = st.slider("Confidence Thresholds to Analyze", 0.0, 1.0, (0.4, 0.8), 0.1, key="asset_confidence_range")
        
        if st.button("Run Confidence Analysis", key="asset_run_analysis"):
            if not analysis_strategy or analysis_strategy == "None":
                st.error("Please select a valid strategy.")
                return
                
            with st.spinner("Analyzing confidence levels..."):
                # Тестуємо різні рівні впевненості
                confidence_levels = [round(x, 1) for x in np.arange(confidence_thresholds[0], confidence_thresholds[1] + 0.1, 0.1)]
                analysis_data = []
                
                for conf_level in confidence_levels:
                    result = run_backtest(asset, 200, 10000, analysis_strategy, use_ai=True, min_confidence=conf_level)
                    
                    if result:
                        trades = result.get('trades', [])
                        total_trades = len(trades)
                        
                        if total_trades > 0:
                            total_pnl = sum(trade.get('pnl', 0) for trade in trades)
                            winning_trades = sum(1 for trade in trades if trade.get('pnl', 0) > 0)
                            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                            total_return = (total_pnl / 10000) * 100
                            
                            analysis_data.append({
                                'Confidence Level': conf_level,
                                'Total Trades': total_trades,
                                'Win Rate (%)': win_rate,
                                'Total Return (%)': total_return
                            })
                
                if analysis_data:
                    df = pd.DataFrame(analysis_data)
                    st.dataframe(df, use_container_width=True)
                    
                    # Графіки аналізу
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig = px.line(df, x='Confidence Level', y='Total Return (%)',
                                    title="Returns vs Confidence Level",
                                    markers=True)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        fig = px.line(df, x='Confidence Level', y='Total Trades',
                                    title="Number of Trades vs Confidence Level",
                                    markers=True)
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("No data available for confidence analysis.")

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
        min_confidence = st.slider("Min Confidence", 0.0, 1.0, 0.6, 0.1, key="comparison_confidence")
    
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
                result = run_backtest(comp_asset, lookback, 10000, comparison_strategy, use_ai, min_confidence)
                
                if result:
                    trades = result.get('trades', [])
                    metrics = compute_performance_metrics(trades, 10000)
                    
                    comparison_data.append({
                        'Asset': comp_asset,
                        'Total Return (%)': metrics.get('total_return_percent', 0),
                        'Win Rate (%)': metrics.get('win_rate', 0),
                        'Total Trades': metrics.get('total_trades', 0),
                        'Final Capital': metrics.get('final_capital', 0),
                        'Total PnL': metrics.get('total_pnl', 0),
                        'Max Drawdown (%)': metrics.get('max_drawdown', 0)
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
                st.error("No comparison data available. Please check if the API server is running.")

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
