import pandas as pd

def analyze_trades_detailed(trades_df):
    """Detailed analysis of trading performance"""
    if trades_df.empty:
        return {}
    
    df = trades_df.copy()
    
    # Basic metrics
    total_trades = len(df)
    winning_trades = df[df['pnl'] > 0]
    losing_trades = df[df['pnl'] < 0]
    
    win_rate = len(winning_trades) / total_trades
    avg_win = winning_trades['pnl'].mean() if not winning_trades.empty else 0
    avg_loss = losing_trades['pnl'].mean() if not losing_trades.empty else 0
    profit_factor = abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if not losing_trades.empty else float('inf')
    
    # Risk-adjusted metrics
    expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
    risk_reward_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
    
    # Drawdown analysis
    df['cumulative_max'] = df['capital'].cummax()
    df['drawdown'] = (df['cumulative_max'] - df['capital']) / df['cumulative_max']
    max_drawdown = df['drawdown'].max()
    
    # Exit reason analysis
    exit_reasons = df['exit_reason'].value_counts()
    
    return {
        'total_trades': total_trades,
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
        'expectancy': expectancy,
        'risk_reward_ratio': risk_reward_ratio,
        'max_drawdown': max_drawdown,
        'total_return': (df['capital'].iloc[-1] - df['capital'].iloc[0]) / df['capital'].iloc[0],
        'best_trade': df['pnl'].max(),
        'worst_trade': df['pnl'].min(),
        'exit_reasons': exit_reasons.to_dict(),
        'avg_trade_duration': (df['exit_time'] - df['entry_time']).mean(),
    }

def print_detailed_report(metrics, asset):
    """Print a detailed performance report"""
    print(f"\n📊 DETAILED ANALYSIS - {asset}")
    print("="*50)
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Win Rate: {metrics['win_rate']:.1%}")
    print(f"Expectancy: ${metrics['expectancy']:.2f} per trade")
    print(f"Risk/Reward: {metrics['risk_reward_ratio']:.2f}")
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"Max Drawdown: {metrics['max_drawdown']:.1%}")
    print(f"Total Return: {metrics['total_return']:.1%}")
    print(f"Best Trade: ${metrics['best_trade']:.2f}")
    print(f"Worst Trade: ${metrics['worst_trade']:.2f}")
    print(f"Average Trade Duration: {metrics['avg_trade_duration']}")
    
    print(f"\nExit Reasons:")
    for reason, count in metrics['exit_reasons'].items():
        print(f"  {reason}: {count} trades")
    
    # Strategy assessment
    if metrics['expectancy'] > 0 and metrics['profit_factor'] > 1.2:
        print("🎯 STRATEGY ASSESSMENT: POTENTIALLY PROFITABLE")
    elif metrics['expectancy'] > 0:
        print("⚠️  STRATEGY ASSESSMENT: NEEDS OPTIMIZATION")
    else:
        print("❌ STRATEGY ASSESSMENT: NOT PROFITABLE")
