import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any, List
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api.strategies import registry
from data_loader import DataLoader
from backtest_engine import BacktestEngine

class SignalTimeline:
    def __init__(self):
        self.data_loader = DataLoader()
        self.backtester = BacktestEngine()
    
    def generate_timeline(self, strategy_id: str, asset: str, days: int) -> Dict[str, Any]:
        """Generate price chart with ML-validated signals"""
        
        # Load data
        assets_data = self.data_loader.load_all_assets()
        if asset not in assets_data:
            raise ValueError(f"Asset {asset} not found")
        
        data = assets_data[asset]
        if days > 0:
            data = data.tail(min(len(data), int(days * 288)))
        
        # Get strategy and generate signals
        strategy = registry.get_strategy(strategy_id)
        signals = strategy.generate_signals(data, asset)
        
        # Run backtest to get trade results
        self.backtester.initial_capital = 10000
        backtest_result = self.backtester.run_backtest(strategy_id, data, asset)
        trades = backtest_result.get("trades", []) if "error" not in backtest_result else []
        
        # Generate timeline chart
        chart = self._create_timeline_chart(data, signals, trades, strategy_id, asset)
        
        # Calculate signal statistics
        signal_stats = self._calculate_signal_stats(signals, trades)
        
        return {
            "chart": chart,
            "signal_stats": signal_stats,
            "strategy": strategy_id,
            "asset": asset,
            "period_days": days,
            "total_signals": len(signals) if not signals.empty else 0,
            "total_trades": len(trades)
        }
    
    def _create_timeline_chart(self, data: pd.DataFrame, signals: pd.DataFrame, trades: List, strategy_id: str, asset: str):
        """Create price timeline with signals overlay"""
        
        # Create subplots
        fig = make_subplots(
            rows=2, 
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=(f"{asset} Price with ML Signals", "ML Confidence Over Time"),
            row_heights=[0.7, 0.3]
        )
        
        # 1. Price candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close'],
                name="Price"
            ),
            row=1, col=1
        )
        
        # 2. Add signals to price chart
        if not signals.empty:
            # Separate buy and sell signals
            buy_signals = signals[signals['signal'] == 'LONG']
            sell_signals = signals[signals['signal'] == 'SHORT']
            
            # Add buy signals
            if not buy_signals.empty:
                fig.add_trace(
                    go.Scatter(
                        x=buy_signals['timestamp'],
                        y=buy_signals['price'],
                        mode='markers+text',
                        marker=dict(
                            symbol='triangle-up',
                            size=15,
                            color='green',
                            line=dict(width=2, color='darkgreen')
                        ),
                        name='ML Buy Signal',
                        hovertemplate=(
                            "<b>BUY SIGNAL</b><br>" +
                            "Time: %{x}<br>" +
                            "Price: %{y:.2f}<br>" +
                            "Confidence: %{customdata:.1%}<extra></extra>"
                        ),
                        customdata=buy_signals.get('ml_confidence', [0] * len(buy_signals))
                    ),
                    row=1, col=1
                )
            
            # Add sell signals
            if not sell_signals.empty:
                fig.add_trace(
                    go.Scatter(
                        x=sell_signals['timestamp'],
                        y=sell_signals['price'],
                        mode='markers+text',
                        marker=dict(
                            symbol='triangle-down',
                            size=15,
                            color='red', 
                            line=dict(width=2, color='darkred')
                        ),
                        name='ML Sell Signal',
                        hovertemplate=(
                            "<b>SELL SIGNAL</b><br>" +
                            "Time: %{x}<br>" +
                            "Price: %{y:.2f}<br>" +
                            "Confidence: %{customdata:.1%}<extra></extra>"
                        ),
                        customdata=sell_signals.get('ml_confidence', [0] * len(sell_signals))
                    ),
                    row=1, col=1
                )
        
        # 3. Add actual trade entries from backtest
        if trades:
            trade_entries = []
            trade_exits = []
            
            for trade in trades:
                trade_entries.append({
                    'time': trade['entry_time'],
                    'price': trade['entry_price'],
                    'type': trade['signal']
                })
                trade_exits.append({
                    'time': trade['exit_time'], 
                    'price': trade['exit_price'],
                    'type': trade['signal']
                })
            
            # Add trade entry markers
            entry_df = pd.DataFrame(trade_entries)
            if not entry_df.empty:
                fig.add_trace(
                    go.Scatter(
                        x=entry_df['time'],
                        y=entry_df['price'],
                        mode='markers',
                        marker=dict(
                            symbol='circle',
                            size=8,
                            color='blue',
                            line=dict(width=2, color='white')
                        ),
                        name='Trade Entry',
                        hovertemplate="<b>TRADE ENTRY</b><br>Time: %{x}<br>Price: %{y:.2f}<extra></extra>"
                    ),
                    row=1, col=1
                )
        
        # 4. ML Confidence timeline (if available)
        if not signals.empty and 'ml_confidence' in signals.columns:
            # Create confidence timeline
            confidence_data = signals[['timestamp', 'ml_confidence']].copy()
            confidence_data = confidence_data.set_index('timestamp')
            confidence_data = confidence_data.sort_index()
            
            fig.add_trace(
                go.Scatter(
                    x=confidence_data.index,
                    y=confidence_data['ml_confidence'] * 100,  # Convert to percentage
                    mode='lines+markers',
                    line=dict(color='purple', width=2),
                    marker=dict(size=4),
                    name='ML Confidence',
                    hovertemplate="Confidence: %{y:.1f}%<extra></extra>"
                ),
                row=2, col=1
            )
            
            # Add confidence threshold line
            fig.add_hline(
                y=70, 
                line_dash="dash", 
                line_color="orange",
                annotation_text="70% Threshold",
                row=2, col=1
            )
        
        # Update layout
        strategy_info = registry.get_strategy_info(strategy_id)
        strategy_name = strategy_info["name"] if strategy_info else strategy_id
        
        fig.update_layout(
            title=f"{asset} - {strategy_name} Trading Signals",
            height=600,
            showlegend=True,
            xaxis_rangeslider_visible=False
        )
        
        # Update y-axes labels
        fig.update_yaxes(title_text="Price", row=1, col=1)
        fig.update_yaxes(title_text="Confidence (%)", range=[0, 100], row=2, col=1)
        
        return fig.to_dict()
    
    def _calculate_signal_stats(self, signals: pd.DataFrame, trades: List):
        """Calculate signal statistics"""
        stats = {}
        
        if not signals.empty:
            stats["total_signals"] = len(signals)
            stats["buy_signals"] = len(signals[signals['signal'] == 'LONG'])
            stats["sell_signals"] = len(signals[signals['signal'] == 'SHORT'])
            
            if 'ml_confidence' in signals.columns:
                stats["avg_confidence"] = signals['ml_confidence'].mean() * 100
                stats["high_confidence_signals"] = len(signals[signals['ml_confidence'] >= 0.7])
        
        if trades:
            stats["total_trades"] = len(trades)
            winning_trades = [t for t in trades if t['pnl'] > 0]
            stats["winning_trades"] = len(winning_trades)
            stats["win_rate"] = len(winning_trades) / len(trades) * 100 if trades else 0
        
        return stats
