"""Deterministic, validated safety logic for CiviSentry 360.
This module deliberately does not use an LLM for emergency classification.
"""
from dataclasses import dataclass
from typing import Any

RANGES = {
    'temperature_c': (-20.0, 60.0),
    'humidity_pct': (0.0, 100.0),
    'tilt_deg': (0.0, 180.0),
    'acceleration_g': (0.0, 10.0),
    'work_duration_min': (0.0, 720.0),
}

@dataclass
class RiskResult:
    score: int
    level: str
    event: str
    reasons: list[str]


def number(value: Any, name: str) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError):
        raise ValueError(f'{name} must be numeric')
    if name in RANGES:
        lo, hi = RANGES[name]
        if not lo <= x <= hi:
            raise ValueError(f'{name} must be between {lo} and {hi}')
    return x


def classify(temperature_c: Any, humidity_pct: Any, tilt_deg: Any,
             acceleration_g: Any, work_duration_min: Any,
             movement: str = 'normal', harness: str = 'yes',
             waterlogging: str = 'no') -> RiskResult:
    t = number(temperature_c, 'temperature_c')
    h = number(humidity_pct, 'humidity_pct')
    tilt = number(tilt_deg, 'tilt_deg')
    acc = number(acceleration_g, 'acceleration_g')
    duration = number(work_duration_min, 'work_duration_min')
    movement = str(movement).lower().strip()
    harness = str(harness).lower().strip()
    waterlogging = str(waterlogging).lower().strip()

    reasons = []
    # Safety override: fall always wins over environmental conditions.
    if tilt >= 60 or acc >= 2.5:
        reasons.append('abnormal tilt or impact acceleration')
        if movement in ('low', 'very_low', 'very low', 'none'):
            reasons.append('reduced post-event movement')
        return RiskResult(96 if movement in ('low','very_low','very low','none') else 90, 'CRITICAL', 'possible_fall', reasons)

    heat_index_proxy = t + 0.1 * h
    if heat_index_proxy >= 44 or (t >= 38 and duration >= 75):
        reasons.append('high heat exposure')
        if duration >= 75: reasons.append('prolonged work duration')
        if movement in ('low', 'very_low', 'very low'): reasons.append('reduced movement')
        return RiskResult(78, 'HIGH', 'heat_stress', reasons)

    if harness == 'no':
        reasons.append('required harness not confirmed')
        return RiskResult(68, 'HIGH', 'ppe_gap', reasons)

    if waterlogging == 'yes':
        reasons.append('standing water in or near active zone')
        return RiskResult(64, 'HIGH', 'waterlogging', reasons)

    if t >= 35 or duration >= 75 or movement in ('low', 'very_low', 'very low'):
        reasons.append('monitoring condition requires attention')
        return RiskResult(54, 'MODERATE', 'monitor', reasons)

    return RiskResult(14, 'LOW', 'normal', ['no threshold exceeded'])


def scenario(name: str) -> dict:
    scenarios = {
        'normal': dict(temperature_c=30, humidity_pct=65, tilt_deg=4, acceleration_g=1.0, work_duration_min=22, movement='normal', harness='yes', waterlogging='no'),
        'heat': dict(temperature_c=39, humidity_pct=72, tilt_deg=8, acceleration_g=1.1, work_duration_min=96, movement='low', harness='yes', waterlogging='no'),
        'fall': dict(temperature_c=31, humidity_pct=68, tilt_deg=68, acceleration_g=3.8, work_duration_min=110, movement='very_low', harness='yes', waterlogging='no'),
        'ppe': dict(temperature_c=31, humidity_pct=65, tilt_deg=5, acceleration_g=1.0, work_duration_min=40, movement='normal', harness='no', waterlogging='no'),
        'waterlogging': dict(temperature_c=32, humidity_pct=80, tilt_deg=5, acceleration_g=1.0, work_duration_min=45, movement='normal', harness='yes', waterlogging='yes'),
    }
    if name not in scenarios: raise KeyError(f'Unknown scenario: {name}')
    return scenarios[name]
