from data import get_storage_data

def evaluate_ng_storage_model(storage: dict, regime: str = "neutral") -> dict:
    """
    Deviation-based natural gas price reaction model
    """

    # -------------------------
    # Extract values
    # -------------------------
    actual = storage["net_change"]          # Bcf
    expected = storage["exp_change"]        # Bcf

    current = storage["current"]
    yr_ago = storage["yr_ago"]
    five_yr = storage["5_yr_avg"]

    # -------------------------
    # Deviations
    # -------------------------
    weekly_deviation = actual - expected     # negative = bullish

    yoy_tightness = (current - yr_ago) / yr_ago if yr_ago != 0 else 0
    five_year_cushion = (current - five_yr) / five_yr if five_yr != 0 else 0

    # -------------------------
    # Model parameters (Refined for realism)
    # -------------------------
    alpha = 0.0025   # 0.25% per 10 Bcf surprise
    beta = 0.50      # YoY amplification (was 6.0, which was too high)
    gamma = 0.30     # Structural cushion penalty (was 4.0)

    # -------------------------
    # Core price reaction
    # -------------------------
    # Sign Fix: Positive deviation (actual > expected) is BEARISH (negative price move)
    # Sign Fix: Positive YoY/Cushion (more storage than last yr/avg) is BEARISH
    price_change = (
        -alpha * (weekly_deviation / 10)
        - beta * yoy_tightness
        - gamma * five_year_cushion
    )

    # -------------------------
    # Regime filter
    # -------------------------
    regime_multiplier = {
        "cold": 1.5,
        "neutral": 1.0,
        "warm": 0.6
    }.get(regime.lower(), 1.0)

    adjusted_price_change = price_change * regime_multiplier

    # -------------------------
    # Signal strength
    # -------------------------
    signal_strength = abs(weekly_deviation) * (1 + abs(yoy_tightness)) / (1 + five_year_cushion)

    # -------------------------
    # Trade bias
    # -------------------------
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

    # -------------------------
    # Output
    # -------------------------
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
