import sys
import os

# Test basic imports
try:
    # Add src to path
    sys.path.append('src')
    
    from api.strategies import registry
    print("✅ Strategy registry imported successfully!")
    
    # List available strategies
    strategies = registry.list_strategies()
    print(f"🎯 Found {len(strategies)} strategies:")
    for strategy_id in strategies.keys():
        print(f"   - {strategy_id}")
        
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
