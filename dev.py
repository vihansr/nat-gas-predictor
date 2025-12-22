from data import get_storage_data

def evaluate_ng_storage_model(storage: dict, regime: str = "neutral") -> dict:
    """
    Deviation-based natural gas price reaction model
    """

    actual = storage["net_change"]          
    expected = storage["exp_change"]        

    current = storage["current"]
    yr_ago = storage["yr_ago"]
    five_yr = storage["5_yr_avg"]

    weekly_deviation = actual - expected  

    yoy_tightness = (current - yr_ago) / yr_ago if yr_ago != 0 else 0
    five_year_cushion = (current - five_yr) / five_yr if five_yr != 0 else 0

    alpha = 0.0025   
    beta = 0.50      
    gamma = 0.30     

    price_change = (
        -alpha * (weekly_deviation / 10)
        - beta * yoy_tightness
        - gamma * five_year_cushion
    )

    regime_multiplier = {
        "cold": 1.5,
        "neutral": 1.0,
        "warm": 0.6
    }.get(regime.lower(), 1.0)

    adjusted_price_change = price_change * regime_multiplier

    signal_strength = abs(weekly_deviation) * (1 + abs(yoy_tightness)) / (1 + five_year_cushion)
    if adjusted_price_change > 0.02:
        bias = "Strong Bullish"
    elif adjusted_price_change > 0.005:
        bias = "Moderately Bullish"
    elif adjusted_price_change < -0.02:
        bias = "Strong Bearish"
    elif adjusted_price_change < -0.005:
        bias = "Moderately Bearish"
    else:
        bias = "Neutral"

    return {
        "actual_change_bcf": actual,
        "expected_change_bcf": expected,
        "weekly_deviation_bcf": round(weekly_deviation, 2),
        "yoy_tightness_pct": round(yoy_tightness * 100, 2),
        "five_year_cushion_pct": round(five_year_cushion * 100, 2),
        "expected_price_move_pct": round(adjusted_price_change * 100, 2),
        "signal_strength": round(signal_strength, 2),
        "trade_bias": bias
    }


if __name__ == "__main__":
    storage = get_storage_data()
    model_output = evaluate_ng_storage_model(storage, regime="cold")
    print("Model Output:")
    for m in model_output:
        print(f"{m}: {model_output[m]}")
