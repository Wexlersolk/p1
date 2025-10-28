from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
import traceback
from src.visualisation.strategy_dashboard import StrategyDashboard
from src.visualisation.confidence_analysis import ConfidenceAnalysis
from src.visualisation.signal_timeline import SignalTimeline
import pandas as pd
import json

router = APIRouter(prefix="/api/v1/visualization", tags=["visualization"])
import pprint

def deep_inspect(obj, path="root"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            deep_inspect(v, f"{path}.{k}")
    elif isinstance(obj, list):
        if obj:
            print(f"{path}: list, first element type: {type(obj[0])}")
            if isinstance(obj[0], list):
                print(f"  {path}: ⚠️ first element is a list of length {len(obj[0])}")
            elif isinstance(obj[0], dict):
                print(f"  {path}: first element keys: {list(obj[0].keys())}")
            else:
                print(f"  {path}: first element value: {obj[0]}")
        else:
            print(f"{path}: empty list")
    else:
        print(f"{path}: {type(obj)}")


def sanitize_for_json(obj):
    import pandas as pd
    import numpy as np
    from datetime import datetime, date

    # Базові типи, які можна повернути як є
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    
    # NumPy типи
    elif isinstance(obj, (np.integer, np.int32, np.int64, np.int8, np.int16)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float32, np.float64, np.float16)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    
    # datetime
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    
    # Pandas
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    
    # Словники
    elif isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    
    # Списки, кортежі та інші ітератори
    elif isinstance(obj, (list, tuple, set)):
        return [sanitize_for_json(item) for item in obj]
    
    # NumPy arrays
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    
    # Plotly специфічні об'єкти (якщо є)
    elif hasattr(obj, '__class__') and 'plotly' in str(obj.__class__):
        # Для plotly об'єктів намагаємося отримати їх словникове представлення
        try:
            if hasattr(obj, 'to_plotly_json'):
                return obj.to_plotly_json()
            elif hasattr(obj, 'to_dict'):
                return obj.to_dict()
        except:
            pass
    
    # Спробуємо отримати словникове представлення для інших об'єктів
    try:
        if hasattr(obj, 'to_dict'):
            return sanitize_for_json(obj.to_dict())
        elif hasattr(obj, 'dict'):
            return sanitize_for_json(obj.dict())
    except:
        pass
    
    # Якщо нічого не спрацювало, спробуємо repr або str
    try:
        return str(obj)
    except:
        return f"Unserializable object: {type(obj)}"
    
def improved_sanitize_for_json(obj, max_depth=10, current_depth=0):
    """
    Покращена версія з обмеженням глибини рекурсії
    """
    if current_depth > max_depth:
        return "Max depth exceeded"
    
    import pandas as pd
    import numpy as np
    from datetime import datetime, date
    import decimal

    # Базові типи
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    
    # Decimal
    elif isinstance(obj, decimal.Decimal):
        return float(obj)
    
    # NumPy типи
    elif isinstance(obj, (np.integer, np.int32, np.int64, np.int8, np.int16)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float32, np.float64, np.float16)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    
    # datetime
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    
    # Pandas
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    
    # Словники
    elif isinstance(obj, dict):
        return {
            str(k): improved_sanitize_for_json(v, max_depth, current_depth + 1) 
            for k, v in obj.items()
        }
    
    # Списки, кортежі та інші ітератори
    elif isinstance(obj, (list, tuple, set)):
        return [
            improved_sanitize_for_json(item, max_depth, current_depth + 1) 
            for item in obj
        ]
    
    # Специфічні об'єкти Plotly
    elif hasattr(obj, '__class__') and any(x in str(obj.__class__) for x in ['plotly', 'graph_objs']):
        try:
            if hasattr(obj, 'to_plotly_json'):
                result = obj.to_plotly_json()
                return improved_sanitize_for_json(result, max_depth, current_depth + 1)
            elif hasattr(obj, 'to_dict'):
                result = obj.to_dict()
                return improved_sanitize_for_json(result, max_depth, current_depth + 1)
        except Exception as e:
            return f"Plotly object conversion failed: {str(e)}"
    
    # Спробуємо отримати словникове представлення
    try:
        if hasattr(obj, 'to_dict'):
            result = obj.to_dict()
            return improved_sanitize_for_json(result, max_depth, current_depth + 1)
        elif hasattr(obj, 'dict'):
            result = obj.dict()
            return improved_sanitize_for_json(result, max_depth, current_depth + 1)
        elif hasattr(obj, '__dict__'):
            result = obj.__dict__
            return improved_sanitize_for_json(result, max_depth, current_depth + 1)
    except Exception as e:
        pass
    
    # Якщо нічого не спрацювало, спробуємо repr
    try:
        return str(obj)
    except:
        return f"Unserializable object of type: {type(obj)}"
    
@router.get("/strategy-dashboard/{asset}")
async def get_strategy_dashboard(
    asset: str,
    days: int = Query(30, description="Number of days to analyze"),
    initial_capital: float = Query(10000, description="Initial capital for backtesting")
):
    """Get comprehensive strategy performance dashboard"""
    try:
        dashboard = StrategyDashboard()
        result = dashboard.generate_dashboard(asset, days, initial_capital)
        
        print("=== DASHBOARD RESULT TYPE ===", type(result))
        if isinstance(result, dict):
            for k, v in result.items():
                print(f"KEY: {k}, TYPE: {type(v)}")
                if isinstance(v, list):
                    print(f"  First element type: {type(v[0]) if v else 'empty'}")
        
        # Використовуємо покращену функцію
        sanitized_result = improved_sanitize_for_json(result)
        
        # Додаткова перевірка
        import json
        try:
            # Спробуємо серіалізувати для перевірки
            json.dumps(sanitized_result)
            print("✅ Sanitization successful - result is JSON serializable")
        except Exception as e:
            print(f"❌ Sanitization failed: {e}")
            # Якщо не вдалося, повертаємо спрощену версію
            return {
                "asset": asset,
                "period_days": days,
                "initial_capital": initial_capital,
                "error": "Could not serialize full dashboard data",
                "available_strategies": list(result.get('metrics', {}).keys()) if isinstance(result, dict) else []
            }
        
        return sanitized_result
        
    except Exception as e:
        print("❌ Error in get_strategy_dashboard:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating dashboard: {str(e)}")

@router.get("/available-strategies")
async def get_available_strategies():
    """Get list of available strategies with ML support"""
    try:
        # Створюємо тестовий дашборд для перевірки
        dashboard = StrategyDashboard()
        result = dashboard.generate_dashboard("XAUUSD", 7, 10000)
        
        available_strategies = []
        
        if 'metrics' in result:
            for strategy_id in result['metrics'].keys():
                # Перевіряємо чи є ML метрики для кожної стратегії
                strategy_metrics = result['metrics'][strategy_id]
                has_ml = any('ml' in key.lower() for key in strategy_metrics.keys())
                
                available_strategies.append({
                    'strategy_id': strategy_id,
                    'has_ml_data': has_ml,
                    'metrics_available': list(strategy_metrics.keys())
                })
        
        return {
            "available_strategies": available_strategies,
            "total_strategies": len(available_strategies)
        }
        
    except Exception as e:
        return {"error": str(e)}

@router.get("/confidence-analysis/{strategy_id}/{asset}")
async def get_confidence_analysis(
    strategy_id: str,
    asset: str,
    days: int = Query(30, description="Number of days to analyze")
):
    """Get ML confidence analysis for a specific strategy"""
    try:
           analysis = ConfidenceAnalysis()
           result = analysis.generate_analysis(strategy_id, asset, days)
           return sanitize_for_json(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating confidence analysis: {str(e)}")

@router.get("/debug-ml-data/{strategy_id}/{asset}")
async def debug_ml_data(
    strategy_id: str,
    asset: str,
    days: int = Query(7, description="Number of days to analyze")
):
    """Debug endpoint to inspect ML data structure"""
    try:
        analysis = ConfidenceAnalysis()
        result = analysis.generate_analysis(strategy_id, asset, days)
        
        # Аналізуємо структуру даних
        debug_info = {
            "result_type": type(result).__name__,
            "result_keys": list(result.keys()) if isinstance(result, dict) else "Not a dict",
            "charts_keys": list(result.get('charts', {}).keys()) if isinstance(result, dict) and 'charts' in result else "No charts",
            "metrics_keys": list(result.get('metrics', {}).keys()) if isinstance(result, dict) and 'metrics' in result else "No metrics",
            "ml_metrics": result.get('ml_model_metrics', {}) if isinstance(result, dict) else "No ML metrics"
        }
        
        # Перевіряємо проблемні типи даних
        def find_complex_types(obj, path="root"):
            complex_types = []
            
            if isinstance(obj, dict):
                for k, v in obj.items():
                    complex_types.extend(find_complex_types(v, f"{path}.{k}"))
            elif isinstance(obj, (list, tuple)):
                for i, item in enumerate(obj[:3]):  # Перевіряємо тільки перші 3 елементи
                    complex_types.extend(find_complex_types(item, f"{path}[{i}]"))
            else:
                # Знаходимо складні типи
                if hasattr(obj, '__dict__') or hasattr(obj, 'to_dict') or hasattr(obj, 'to_plotly_json'):
                    complex_types.append(f"{path}: {type(obj)}")
            
            return complex_types
        
        complex_types = find_complex_types(result)
        
        return {
            "debug_info": debug_info,
            "complex_types_found": complex_types[:10],  # Перші 10 складних типів
            "total_complex_types": len(complex_types),
            "sample_sanitized": improved_sanitize_for_json(result) if len(complex_types) > 0 else "No complex types"
        }
        
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

@router.get("/signal-timeline/{strategy_id}/{asset}")
async def get_signal_timeline(
    strategy_id: str,
    asset: str,
    days: int = Query(30, description="Number of days to analyze")
):
    """Get price chart with ML-validated signals overlay"""
    try:
        print(f"📈 Generating signal timeline for {strategy_id} on {asset}")
        
        timeline = SignalTimeline()
        result = timeline.generate_timeline(strategy_id, asset, days)
        
        print(f"✅ Signal timeline generated, sanitizing for JSON...")
        
        # ВИПРАВЛЕННЯ: Використовуємо нашу функцію sanitize_for_json
        sanitized_result = improved_sanitize_for_json(result)
        
        # Додаткова перевірка
        try:
            json.dumps(sanitized_result)
            print("✅ Sanitization successful")
        except Exception as json_error:
            print(f"❌ JSON serialization failed: {json_error}")
            # Повертаємо спрощену версію
            return {
                "strategy_id": strategy_id,
                "asset": asset,
                "period_days": days,
                "error": "Could not serialize timeline data",
                "available_data": list(result.keys()) if isinstance(result, dict) else "Not a dict"
            }
        
        return sanitized_result
        
    except Exception as e:
        print(f"❌ Error in signal timeline: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating signal timeline: {str(e)}")


@router.get("/test-serialization/{asset}")
async def test_serialization(asset: str):
    """Test endpoint to check what data types are causing issues"""
    try:
        dashboard = StrategyDashboard()
        result = dashboard.generate_dashboard(asset, 7, 10000)  # Менше днів для швидшого тесту
        
        def find_problematic_types(obj, path="root"):
            problematic = []
            
            if isinstance(obj, dict):
                for k, v in obj.items():
                    problematic.extend(find_problematic_types(v, f"{path}.{k}"))
            elif isinstance(obj, (list, tuple)):
                for i, item in enumerate(obj[:5]):  # Перевіряємо тільки перші 5 елементів
                    problematic.extend(find_problematic_types(item, f"{path}[{i}]"))
            else:
                # Перевіряємо, чи можна серіалізувати цей об'єкт
                try:
                    json.dumps(obj)
                except:
                    problematic.append(f"{path}: {type(obj)} - {str(obj)[:100]}")
            
            return problematic
        
        issues = find_problematic_types(result)
        
        return {
            "asset": asset,
            "total_issues": len(issues),
            "issues": issues[:10],  # Повертаємо тільки перші 10 проблем
            "result_keys": list(result.keys()) if isinstance(result, dict) else "Not a dict"
        }
        
    except Exception as e:
        return {"error": str(e)}
