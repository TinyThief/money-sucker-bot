from log_setup import logger


def validate_inputs(capital: float, risk_pct: float, entry_price: float, stop_loss_price: float) -> None:
    if capital <= 0 or risk_pct <= 0 or risk_pct > 1:
        msg = "Invalid capital or risk percent."
        raise ValueError(msg)
    if entry_price <= 0 or stop_loss_price <= 0:
        msg = "Invalid entry or stop loss price."
        raise ValueError(msg)
    if abs(entry_price - stop_loss_price) == 0:
        msg = "Stop loss is equal to entry price."
        raise ValueError(msg)


def calculate_position_size(
    capital: float,
    risk_pct: float,
    entry_price: float,
    stop_loss_price: float,
) -> float:
    """Calculates position size based on capital, risk percent and stop-loss distance."""
    try:
        validate_inputs(capital, risk_pct, entry_price, stop_loss_price)
        risk_amount = capital * risk_pct
        sl_distance = abs(entry_price - stop_loss_price)
        position_size = risk_amount / sl_distance
        return round(position_size, 4)

    except ValueError as e:
        logger.error("❌ Error calculating position size: %s", str(e))
        return 0.0
