"""UPI merchant insights for underwriter UI."""

from __future__ import annotations


def upi_momentum(volume: list[float]) -> str:
    if len(volume) < 3:
        return "Stable"
    recent = sum(volume[-3:]) / 3
    prior = sum(volume[-6:-3]) / 3 if len(volume) >= 6 else volume[0]
    if prior <= 0:
        return "Stable"
    change = (recent - prior) / prior * 100
    if change > 5:
        return f"Accelerating (+{change:.0f}% vs prior quarter)"
    if change < -5:
        return f"Slowing ({change:.0f}% vs prior quarter)"
    return "Stable"
