import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api.strategies import registry
from backtest_engine import BacktestEngine
from data_loader import DataLoader

class StrategyDashboard:
    def __init__(self):
        self.backtester = BacktestEngine()
        self.data_loader = DataLoader()
    
    def generate_dashboard(self, asset: str, days: int, initial_capital: float = 10000) -> Dict[str, Any]:
        """Generate strategy performance dashboard"""
        
        # ДІАГНОСТИКА REGISTRY - ПЕРЕД ТЕСТУВАННЯМ СТРАТЕГІЙ
        print(f"\n--- CHECKING STRATEGY REGISTRY ---")
        try:
            from api.strategies import registry
            print(f"Registry type: {type(registry)}")
            print(f"Available strategies: {list(registry._strategies.keys())}")
            
            # Перевіримо метод get_strategy
            print(f"get_strategy method: {hasattr(registry, 'get_strategy')}")
            
            # Спробуємо отримати стратегію з параметрами за замовчуванням
            try:
                strategy = registry.get_strategy("vwap_ib", {})
                print(f"✅ vwap_ib strategy loaded with empty params: {type(strategy)}")
            except Exception as e:
                print(f"❌ Error loading vwap_ib with empty params: {e}")
                
            # Спробуємо отримати стратегію без параметрів
            try:
                strategy = registry.get_strategy("vwap_ib")
                print(f"✅ vwap_ib strategy loaded without params: {type(strategy)}")
            except Exception as e:
                print(f"❌ Error loading vwap_ib without params: {e}")
                
        except Exception as e:
            print(f"❌ Error checking registry: {e}")
        
        print(f"=== DASHBOARD GENERATION STARTED ===")
        print(f"Asset: {asset}, Days: {days}, Capital: {initial_capital}")
        
        # Load data
        assets_data = self.data_loader.load_all_assets()
        if asset not in assets_data:
            raise ValueError(f"Asset {asset} not found")
        
        data = assets_data[asset]
        print(f"Original data shape: {data.shape}")
        
        if days > 0:
            data = data.tail(min(len(data), int(days * 288)))
            print(f"Filtered data shape: {data.shape}")
        
        # Strategies to compare
        strategies = ["vwap_ib", "sma_crossover", "rsi_oversold"]
        
        results = {}
        all_trades = {}
        
        # Run backtests for all strategies
        for strategy_id in strategies:
            try:
                print(f"\n--- Testing strategy: {strategy_id} ---")
                self.backtester.initial_capital = initial_capital
                
                # ВИПРАВЛЕННЯ: Викликаємо run_backtest БЕЗ strategy_params
                result = self.backtester.run_backtest(strategy_id, data, asset)
                
                if "error" not in result:
                    results[strategy_id] = result
                    trades = result.get("trades", [])
                    all_trades[strategy_id] = trades
                    
                    print(f"✅ {strategy_id}: {len(trades)} trades, Return: {result.get('total_return', 0)*100:.2f}%")
                    
                    if trades:
                        print(f"   First trade: {trades[0]}")
                    else:
                        print(f"   ❌ NO TRADES GENERATED")
                        
                else:
                    print(f"❌ {strategy_id}: Error - {result.get('error')}")
                    
            except Exception as e:
                print(f"❌ {strategy_id}: Exception - {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n=== SUMMARY ===")
        print(f"Strategies with trades: {[k for k, v in all_trades.items() if v]}")
        print(f"Total strategies tested: {len(results)}")
        
        # Generate charts and metrics
        charts = self._create_dashboard_charts(results, all_trades, strategies)
        metrics = self._calculate_dashboard_metrics(results, strategies)
        insights = self._generate_dashboard_insights(metrics)
        
        final_result = {
            "charts": charts,
            "metrics": metrics,
            "insights": insights,
            "strategies_tested": list(results.keys()),
            "asset": asset,
            "period_days": days,
            "initial_capital": initial_capital
        }
        
        print(f"=== DASHBOARD GENERATION COMPLETED ===")
        print(f"Charts generated: {list(charts.keys())}")
        print(f"Metrics generated for: {list(metrics.keys())}")
        
        return final_result
    
    def _create_dashboard_charts(self, results: Dict, all_trades: Dict, strategies: List[str]):
        """Create dashboard charts"""
        charts = {}
        
        print(f"\n--- CREATING CHARTS ---")
        print(f"Available trades data: { {k: len(v) for k, v in all_trades.items()} }")
        
        # 1. Equity Curve Comparison
        equity_fig = go.Figure()
        
        colors = {
            "vwap_ib": "blue",
            "vwap_ml_validated": "green", 
            "sma_crossover": "orange",
            "rsi_oversold": "red"
        }
        
        strategies_with_trades = []
        
        for strategy_id in strategies:
            if strategy_id in all_trades and all_trades[strategy_id]:
                trades = all_trades[strategy_id]
                times = [trade["exit_time"] for trade in trades]
                equity = [trade["capital"] for trade in trades]
                
                print(f"📊 {strategy_id}: {len(trades)} trades, {len(times)} time points")
                
                # ВИПРАВЛЕННЯ: Використовуємо простий спосіб отримання імені
                display_name = strategy_id.replace('_', ' ').title()
                
                equity_fig.add_trace(go.Scatter(
                    x=times,
                    y=equity,
                    name=display_name,
                    line=dict(color=colors.get(strategy_id, "gray"), width=3),
                    hovertemplate="<b>%{x}</b><br>Equity: $%{y:,.2f}<extra></extra>"
                ))
                
                strategies_with_trades.append(strategy_id)
        
        if strategies_with_trades:
            equity_fig.update_layout(
                title="Strategy Performance Comparison - Equity Curve",
                xaxis_title="Time",
                yaxis_title="Portfolio Value ($)",
                hovermode="x unified",
                height=500,
                showlegend=True
            )
            
            charts["equity_curve"] = equity_fig.to_dict()
            print(f"✅ Equity curve created with {len(strategies_with_trades)} strategies")
        else:
            # Створюємо порожній графік з повідомленням
            equity_fig.add_annotation(
                text="No trading activity detected<br>Try increasing analysis period or changing parameters",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False,
                font=dict(size=16, color="red")
            )
            equity_fig.update_layout(
                title="No Trading Activity Detected",
                xaxis_title="Time",
                yaxis_title="Portfolio Value ($)",
                height=500
            )
            
            charts["equity_curve"] = equity_fig.to_dict()
            print("❌ No strategies with trades for equity curve")
        
        # 2. Performance Metrics Comparison
        metrics_data = []
        for strategy_id in strategies:
            if strategy_id in results:
                result = results[strategy_id]
                # ВИПРАВЛЕННЯ: Використовуємо простий спосіб отримання імені
                display_name = strategy_id.replace('_', ' ').title()
                
                # Calculate additional metrics
                trades = result.get("trades", [])
                if trades:
                    trades_df = pd.DataFrame(trades)
                    winning_trades = trades_df[trades_df["pnl"] > 0]
                    win_rate = len(winning_trades) / len(trades) * 100 if len(trades) > 0 else 0
                    
                    metrics_data.append({
                        "Strategy": display_name,
                        "Total Return (%)": result.get("total_return", 0) * 100,
                        "Win Rate (%)": win_rate,
                        "Total Trades": len(trades),
                        "Final Capital ($)": result.get("final_capital", 0)
                    })
        
        if metrics_data:
            metrics_df = pd.DataFrame(metrics_data)
            
            # Returns bar chart
            returns_fig = px.bar(
                metrics_df, 
                x="Strategy", 
                y="Total Return (%)",
                title="Total Returns by Strategy",
                color="Total Return (%)",
                color_continuous_scale="RdYlGn",
                text="Total Return (%)"
            )
            returns_fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            returns_fig.update_layout(height=400, showlegend=False)
            charts["returns_chart"] = returns_fig.to_dict()
            
            # Win rate bar chart
            winrate_fig = px.bar(
                metrics_df,
                x="Strategy",
                y="Win Rate (%)", 
                title="Win Rate by Strategy",
                color="Win Rate (%)",
                color_continuous_scale="RdYlGn",
                text="Win Rate (%)"
            )
            winrate_fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            winrate_fig.update_layout(height=400, showlegend=False)
            charts["winrate_chart"] = winrate_fig.to_dict()
            
            print(f"✅ Performance charts created with {len(metrics_data)} strategies")
        else:
            print("❌ No metrics data for performance charts")
        
        return charts
    
    def _calculate_dashboard_metrics(self, results: Dict, strategies: List[str]):
        """Calculate performance metrics for dashboard"""
        metrics = {}
        
        for strategy_id in strategies:
            if strategy_id in results:
                result = results[strategy_id]
                # ВИПРАВЛЕННЯ: Використовуємо простий спосіб отримання імені
                display_name = strategy_id.replace('_', ' ').title()
                
                # Calculate metrics from trades
                trades = result.get("trades", [])
                if trades:
                    trades_df = pd.DataFrame(trades)
                    winning_trades = trades_df[trades_df["pnl"] > 0]
                    losing_trades = trades_df[trades_df["pnl"] < 0]
                    
                    win_rate = len(winning_trades) / len(trades) * 100 if len(trades) > 0 else 0
                    avg_win = winning_trades["pnl"].mean() if len(winning_trades) > 0 else 0
                    avg_loss = losing_trades["pnl"].mean() if len(losing_trades) > 0 else 0
                    profit_factor = abs(winning_trades["pnl"].sum() / losing_trades["pnl"].sum()) if len(losing_trades) > 0 and losing_trades["pnl"].sum() != 0 else float('inf')
                    
                    # Calculate max drawdown
                    equity_curve = trades_df["capital"]
                    rolling_max = equity_curve.expanding().max()
                    drawdown = (equity_curve - rolling_max) / rolling_max
                    max_drawdown = drawdown.min() * 100
                    
                else:
                    win_rate = avg_win = avg_loss = max_drawdown = profit_factor = 0
                
                metrics[strategy_id] = {
                    "name": display_name,
                    "total_return": round(result.get("total_return", 0) * 100, 2),
                    "total_trades": result.get("total_trades", 0),
                    "win_rate": round(win_rate, 2),
                    "avg_win": round(avg_win, 2),
                    "avg_loss": round(avg_loss, 2),
                    "max_drawdown": round(max_drawdown, 2),
                    "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else "∞",
                    "final_capital": round(result.get("final_capital", 0), 2)
                }
        
        return metrics
    
    def _generate_dashboard_insights(self, metrics: Dict):
        """Generate insights from dashboard metrics"""
        insights = []
        
        # Find best performing strategy
        strategies_with_returns = {
            k: v for k, v in metrics.items() 
            if v["total_trades"] > 0 and "ml_validated" not in k
        }
        
        if strategies_with_returns:
            best_strategy = max(strategies_with_returns.items(), key=lambda x: x[1]["total_return"])
            best_ml_strategy = None
            
            # Check ML validated version
            ml_strategy_id = f"{best_strategy[0]}_ml_validated"
            if ml_strategy_id in metrics and metrics[ml_strategy_id]["total_trades"] > 0:
                best_ml_strategy = metrics[ml_strategy_id]
                
                # Compare ML vs original
                original_return = best_strategy[1]["total_return"]
                ml_return = best_ml_strategy["total_return"]
                improvement = ml_return - original_return
                
                if improvement > 0:
                    insights.append({
                        "type": "success",
                        "title": "ML Enhancement Working",
                        "message": f"ML validation improved {best_strategy[1]['name']} by {improvement:.1f}% (from {original_return:.1f}% to {ml_return:.1f}%)"
                    })
                else:
                    insights.append({
                        "type": "warning",
                        "title": "ML Needs Tuning", 
                        "message": f"ML validation decreased {best_strategy[1]['name']} performance by {abs(improvement):.1f}%"
                    })
            
            # Overall best strategy
            all_valid_strategies = {k: v for k, v in metrics.items() if v["total_trades"] > 0}
            if all_valid_strategies:
                overall_best = max(all_valid_strategies.items(), key=lambda x: x[1]["total_return"])
                insights.append({
                    "type": "info",
                    "title": "Best Performing Strategy",
                    "message": f"{overall_best[1]['name']} achieved {overall_best[1]['total_return']:.1f}% return with {overall_best[1]['win_rate']:.1f}% win rate"
                })
        
        return insights