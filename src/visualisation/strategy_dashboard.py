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
        
        # Load data
        assets_data = self.data_loader.load_all_assets()
        if asset not in assets_data:
            raise ValueError(f"Asset {asset} not found")
        
        data = assets_data[asset]
        if days > 0:
            # Approximate 5-min bars per day (288 = 24 hours * 12 five-minute bars)
            data = data.tail(min(len(data), int(days * 288)))
        
        # Strategies to compare
        strategies = ["vwap_ib", "vwap_ml_validated", "sma_crossover", "rsi_oversold"]
        
        results = {}
        all_trades = {}
        
        # Run backtests for all strategies
        for strategy_id in strategies:
            try:
                self.backtester.initial_capital = initial_capital
                result = self.backtester.run_backtest(strategy_id, data, asset)
                
                if "error" not in result:
                    results[strategy_id] = result
                    all_trades[strategy_id] = result.get("trades", [])
                    
            except Exception as e:
                print(f"Warning: Could not backtest {strategy_id}: {e}")
        
        # Generate charts and metrics
        charts = self._create_dashboard_charts(results, all_trades, strategies)
        metrics = self._calculate_dashboard_metrics(results, strategies)
        insights = self._generate_dashboard_insights(metrics)
        
        return {
            "charts": charts,
            "metrics": metrics,
            "insights": insights,
            "strategies_tested": list(results.keys()),
            "asset": asset,
            "period_days": days,
            "initial_capital": initial_capital
        }
    
    def _create_dashboard_charts(self, results: Dict, all_trades: Dict, strategies: List[str]):
        """Create dashboard charts"""
        charts = {}
        
        # 1. Equity Curve Comparison
        equity_fig = go.Figure()
        
        colors = {
            "vwap_ib": "blue",
            "vwap_ml_validated": "green", 
            "sma_crossover": "orange",
            "rsi_oversold": "red"
        }
        
        for strategy_id in strategies:
            if strategy_id in all_trades and all_trades[strategy_id]:
                trades = all_trades[strategy_id]
                times = [trade["exit_time"] for trade in trades]
                equity = [trade["capital"] for trade in trades]
                
                strategy_info = registry.get_strategy_info(strategy_id)
                display_name = strategy_info["name"] if strategy_info else strategy_id
                
                equity_fig.add_trace(go.Scatter(
                    x=times,
                    y=equity,
                    name=display_name,
                    line=dict(color=colors.get(strategy_id, "gray"), width=3),
                    hovertemplate="<b>%{x}</b><br>Equity: $%{y:,.2f}<extra></extra>"
                ))
        
        equity_fig.update_layout(
            title="Strategy Performance Comparison - Equity Curve",
            xaxis_title="Time",
            yaxis_title="Portfolio Value ($)",
            hovermode="x unified",
            height=500,
            showlegend=True
        )
        
        charts["equity_curve"] = equity_fig.to_dict()
        
        # 2. Performance Metrics Comparison
        metrics_data = []
        for strategy_id in strategies:
            if strategy_id in results:
                result = results[strategy_id]
                strategy_info = registry.get_strategy_info(strategy_id)
                display_name = strategy_info["name"] if strategy_info else strategy_id
                
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
        
        return charts
    
    def _calculate_dashboard_metrics(self, results: Dict, strategies: List[str]):
        """Calculate performance metrics for dashboard"""
        metrics = {}
        
        for strategy_id in strategies:
            if strategy_id in results:
                result = results[strategy_id]
                strategy_info = registry.get_strategy_info(strategy_id)
                display_name = strategy_info["name"] if strategy_info else strategy_id
                
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
