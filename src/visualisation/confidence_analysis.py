import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any
import sys
import os

# Add src to path for imports
# sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api.strategies import registry
from backtest_engine import BacktestEngine
from data_loader import DataLoader

class ConfidenceAnalysis:
    def __init__(self):
        self.backtester = BacktestEngine()
        self.data_loader = DataLoader()
    
    def generate_analysis(self, strategy_id: str, asset: str, days: int) -> Dict[str, Any]:
        """Generate ML confidence analysis"""
        
        # Load data
        assets_data = self.data_loader.load_all_assets()
        if asset not in assets_data:
            raise ValueError(f"Asset {asset} not found")
        
        data = assets_data[asset]
        if days > 0:
            data = data.tail(min(len(data), int(days * 288)))
        
        # Run backtest
        self.backtester.initial_capital = 10000
        result = self.backtester.run_backtest(strategy_id, data, asset)
        
        if "error" in result:
            raise ValueError(f"Backtest error: {result['error']}")
        
        if "trades" not in result or not result["trades"]:
            raise ValueError(f"No trades generated for {strategy_id}")
        
        trades_df = pd.DataFrame(result["trades"])
        
        # Check if ML confidence data exists
        if "ml_confidence" not in trades_df.columns:
            # Return basic analysis WITHOUT throwing error
            return self._generate_basic_analysis(trades_df, strategy_id, asset, days)
    
        # Generate analysis
        charts = self._create_confidence_charts(trades_df, strategy_id)
        metrics = self._calculate_confidence_metrics(trades_df)
        insights = self._generate_confidence_insights(metrics, strategy_id)
        
        return {
            "charts": charts,
            "metrics": metrics,
            "insights": insights,
            "strategy": strategy_id,
            "asset": asset,
            "total_trades": len(trades_df),
            "period_days": days
        }
    
    def _create_confidence_charts(self, trades_df: pd.DataFrame, strategy_id: str):
        """Create confidence analysis charts"""
        charts = {}
        
        # 1. Confidence vs PnL Scatter Plot
        trades_df = trades_df.copy()
        trades_df["is_win"] = trades_df["pnl"] > 0
        trades_df["pnl_pct"] = trades_df["pnl_pct"] * 100
        trades_df["ml_confidence_pct"] = trades_df["ml_confidence"] * 100
        
        scatter_fig = px.scatter(
            trades_df,
            x="ml_confidence_pct",
            y="pnl_pct",
            color="is_win",
            color_discrete_map={True: "green", False: "red"},
            title="ML Confidence vs Trade Performance",
            labels={
                "ml_confidence_pct": "ML Confidence Score (%)",
                "pnl_pct": "Trade P&L (%)",
                "is_win": "Winning Trade"
            },
            hover_data=["entry_time", "exit_reason"],
            size_max=10
        )
        
        # Add reference lines
        scatter_fig.add_hline(y=0, line_dash="dash", line_color="black")
        scatter_fig.add_vline(x=70, line_dash="dash", line_color="orange", 
                             annotation_text="70% Confidence")
        
        scatter_fig.update_layout(
            height=500,
            xaxis_range=[0, 100],
            showlegend=True
        )
        
        charts["confidence_scatter"] = scatter_fig.to_dict()
        
        # 2. Confidence Distribution by Win/Loss
        hist_fig = px.histogram(
            trades_df,
            x="ml_confidence_pct",
            color="is_win",
            nbins=20,
            title="Confidence Distribution by Trade Outcome",
            labels={
                "ml_confidence_pct": "ML Confidence Score (%)", 
                "count": "Number of Trades"
            },
            color_discrete_map={True: "green", False: "red"}
        )
        hist_fig.update_layout(height=400, bargap=0.1, showlegend=True)
        charts["confidence_histogram"] = hist_fig.to_dict()
        
        # 3. Performance by Confidence Buckets
        bucket_metrics = self._calculate_confidence_buckets(trades_df)
        if bucket_metrics:
            bucket_df = pd.DataFrame(bucket_metrics)
            
            # Win rate by confidence bucket
            winrate_fig = px.bar(
                bucket_df,
                x="confidence_range",
                y="win_rate",
                title="Win Rate by Confidence Level",
                color="win_rate",
                color_continuous_scale="RdYlGn",
                text="win_rate"
            )
            winrate_fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            winrate_fig.update_layout(
                height=400, 
                showlegend=False,
                xaxis_title="Confidence Range",
                yaxis_title="Win Rate (%)"
            )
            charts["winrate_by_confidence"] = winrate_fig.to_dict()
        
        return charts
    
    def _calculate_confidence_metrics(self, trades_df: pd.DataFrame):
        """Calculate confidence performance metrics"""
        metrics = {}
        
        # Overall performance
        total_trades = len(trades_df)
        winning_trades = trades_df[trades_df["pnl"] > 0]
        losing_trades = trades_df[trades_df["pnl"] < 0]
        
        metrics["overall"] = {
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": len(winning_trades) / total_trades * 100 if total_trades > 0 else 0,
            "avg_pnl": trades_df["pnl"].mean(),
            "avg_confidence": trades_df["ml_confidence"].mean() * 100
        }
        
        # High confidence performance (>= 70%)
        high_conf_trades = trades_df[trades_df["ml_confidence"] >= 0.7]
        if len(high_conf_trades) > 0:
            high_conf_wins = high_conf_trades[high_conf_trades["pnl"] > 0]
            metrics["high_confidence"] = {
                "trades_count": len(high_conf_trades),
                "win_rate": len(high_conf_wins) / len(high_conf_trades) * 100 if len(high_conf_trades) > 0 else 0,
                "avg_pnl": high_conf_trades["pnl"].mean(),
                "avg_confidence": high_conf_trades["ml_confidence"].mean() * 100
            }
        
        # Low confidence performance (< 70%)
        low_conf_trades = trades_df[trades_df["ml_confidence"] < 0.7]
        if len(low_conf_trades) > 0:
            low_conf_wins = low_conf_trades[low_conf_trades["pnl"] > 0]
            metrics["low_confidence"] = {
                "trades_count": len(low_conf_trades),
                "win_rate": len(low_conf_wins) / len(low_conf_trades) * 100 if len(low_conf_trades) > 0 else 0,
                "avg_pnl": low_conf_trades["pnl"].mean(),
                "avg_confidence": low_conf_trades["ml_confidence"].mean() * 100
            }
        
        return metrics
    
    def _calculate_confidence_buckets(self, trades_df: pd.DataFrame):
        """Calculate performance metrics for confidence buckets"""
        buckets = [
            (0.0, 0.3, "0-30%"),
            (0.3, 0.5, "30-50%"), 
            (0.5, 0.7, "50-70%"),
            (0.7, 0.85, "70-85%"),
            (0.85, 1.0, "85-100%")
        ]
        
        bucket_metrics = []
        
        for low, high, label in buckets:
            bucket_trades = trades_df[
                (trades_df["ml_confidence"] >= low) & 
                (trades_df["ml_confidence"] < high)
            ]
            
            if len(bucket_trades) > 0:
                winning_trades = bucket_trades[bucket_trades["pnl"] > 0]
                
                bucket_metrics.append({
                    "confidence_range": label,
                    "trades_count": len(bucket_trades),
                    "win_rate": len(winning_trades) / len(bucket_trades) * 100,
                    "avg_pnl": bucket_trades["pnl"].mean(),
                    "avg_confidence": bucket_trades["ml_confidence"].mean() * 100
                })
        
        return bucket_metrics
    def _generate_basic_analysis(self, trades_df: pd.DataFrame, strategy_id: str, asset: str, days: int) -> Dict[str, Any]:
        """Generate basic analysis for strategies without ML data"""
        
        return {
            "has_ml_data": False,
            "charts": {},
            "metrics": {
                "overall": {
                    "total_trades": len(trades_df),
                    "win_rate": len(trades_df[trades_df["pnl"] > 0]) / len(trades_df) * 100
                }
            },
            "insights": [{
                "type": "info",
                "title": "No ML Data",
                "message": f"Strategy '{strategy_id}' does not generate ML confidence scores"
            }],
            "strategy": strategy_id,
            "asset": asset,
            "total_trades": len(trades_df),
            "period_days": days
        }
    def _generate_confidence_insights(self, metrics: Dict, strategy_id: str):
        """Generate insights from confidence analysis"""
        insights = []
        
        overall = metrics.get("overall", {})
        high_conf = metrics.get("high_confidence", {})
        low_conf = metrics.get("low_confidence", {})
        
        if high_conf and low_conf:
            # High confidence performance
            win_rate_diff = high_conf["win_rate"] - low_conf["win_rate"]
            
            if win_rate_diff > 15:
                insights.append({
                    "type": "success",
                    "title": "Excellent ML Filter",
                    "message": f"High confidence trades have {win_rate_diff:.1f}% higher win rate ({high_conf['win_rate']:.1f}% vs {low_conf['win_rate']:.1f}%)"
                })
            elif win_rate_diff > 5:
                insights.append({
                    "type": "positive",
                    "title": "Good ML Filter",
                    "message": f"High confidence trades perform better by {win_rate_diff:.1f}% win rate"
                })
            else:
                insights.append({
                    "type": "warning", 
                    "title": "ML Filter Needs Improvement",
                    "message": f"Minimal difference between high and low confidence trades ({win_rate_diff:.1f}% win rate difference)"
                })
            
            # Recommended confidence threshold
            if high_conf["win_rate"] > 70:
                insights.append({
                    "type": "recommendation",
                    "title": "Set High Confidence Threshold",
                    "message": f"Use 70%+ confidence threshold for {high_conf['trades_count']} high-quality trades with {high_conf['win_rate']:.1f}% win rate"
                })
        
        # Overall ML effectiveness
        if overall["win_rate"] > 60:
            insights.append({
                "type": "success",
                "title": "Strong Overall Performance",
                "message": f"Strategy achieves {overall['win_rate']:.1f}% win rate with ML filtering across {overall['total_trades']} trades"
            })
        
        strategy_info = registry.get_strategy_info(strategy_id)
        strategy_name = strategy_info["name"] if strategy_info else strategy_id
        
        insights.append({
            "type": "info",
            "title": "Analysis Summary",
            "message": f"Analyzed {overall['total_trades']} trades from {strategy_name}. Average confidence: {overall['avg_confidence']:.1f}%"
        })
        
        return insights
