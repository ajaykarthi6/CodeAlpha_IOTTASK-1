"""
pacemaker_simulator.py
Connected Pacemaker IoMT Simulator

Simulates a modern smart cardiac implant that:
- Monitors heart rhythm and fluid levels in lungs
- Transmits daily telemetry to the clinic
- Predicts heart failure decompensation weeks in advance
- Acts as an internal IoT node inside the patient's body
"""

import random
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Optional
from enum import Enum


class HeartFailureRisk(Enum):
    LOW      = "LOW"
    MODERATE = "MODERATE"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class PacemakerTelemetry:
    patient_id: str
    device_id: str
    timestamp: str
    heart_rate_bpm: float
    paced_beats_percent: float       # % of beats delivered by pacemaker
    battery_voltage: float           # V (replace when < 2.5V)
    lead_impedance_ohms: float       # 300–1000 Ω normal
    intrathoracic_impedance_ohms: float  # Lung fluid proxy: low = more fluid
    activity_hours: float            # Hours of physical activity today
    hf_risk_score: float             # 0–100 composite heart failure risk
    hf_risk_level: str
    alert: Optional[str]
    days_to_predicted_event: Optional[int]


class PacemakerSimulator:
    """
    Simulates a connected cardiac pacemaker / CRT-D device.

    Key innovation: Monitors intrathoracic impedance as a proxy for
    pulmonary fluid accumulation — predicting heart failure
    decompensation WEEKS before the patient feels symptoms.
    """

    NORMAL_IMPEDANCE = 70.0   # Ω baseline (higher = less fluid)
    CRITICAL_IMPEDANCE = 50.0  # Ω threshold for fluid overload alert

    def __init__(self, patient_id: str, device_id: str = "MEDTRONIC-CRTD-001"):
        self.patient_id = patient_id
        self.device_id = device_id
        self.day = 0
        self.impedance = self.NORMAL_IMPEDANCE
        self.battery_voltage = 3.2   # Fresh battery
        self.hf_trend = []           # Trending toward failure?
        self.history: List[PacemakerTelemetry] = []

    def _compute_hf_risk(self, impedance: float, hr: float, activity: float) -> float:
        """Composite heart failure risk score (0-100)."""
        # Low impedance = fluid in lungs = higher risk
        impedance_score = max(0, (self.NORMAL_IMPEDANCE - impedance) / self.NORMAL_IMPEDANCE * 60)
        # Elevated resting HR = higher risk
        hr_score = max(0, (hr - 70) / 60 * 25)
        # Reduced activity = higher risk (too tired to move)
        activity_score = max(0, (2.0 - activity) / 2.0 * 15)
        return min(100, impedance_score + hr_score + activity_score)

    def _predict_event(self, score: float) -> Optional[int]:
        """Estimate days to decompensation if trend continues."""
        if score < 30:
            return None
        elif score < 50:
            return random.randint(14, 21)
        elif score < 70:
            return random.randint(7, 13)
        else:
            return random.randint(1, 6)

    def _get_risk_level(self, score: float) -> HeartFailureRisk:
        if score < 25:  return HeartFailureRisk.LOW
        if score < 50:  return HeartFailureRisk.MODERATE
        if score < 75:  return HeartFailureRisk.HIGH
        return HeartFailureRisk.CRITICAL

    def simulate_day(self, deteriorating: bool = False) -> PacemakerTelemetry:
        """Generate one day of pacemaker telemetry."""
        self.day += 1

        # Gradually reduce impedance if simulating deterioration (fluid accumulation)
        if deteriorating:
            self.impedance -= random.uniform(0.5, 1.5)
        else:
            self.impedance += random.uniform(-0.3, 0.5)  # Natural variation

        self.impedance = max(40, min(85, self.impedance))

        hr = random.gauss(72 + (20 if deteriorating else 0), 5)
        paced_pct = random.uniform(60, 95)
        activity = max(0, random.gauss(1.5 - (0.5 if deteriorating else 0), 0.3))
        lead_impedance = random.gauss(550, 30)
        self.battery_voltage -= 0.001  # Slow drain

        score = self._compute_hf_risk(self.impedance, hr, activity)
        risk = self._get_risk_level(score)
        days_to_event = self._predict_event(score)

        alert = None
        if risk == HeartFailureRisk.CRITICAL:
            alert = f"🚨 CRITICAL: Heart failure decompensation imminent (~{days_to_event} days). Urgent clinic visit required."
        elif risk == HeartFailureRisk.HIGH:
            alert = f"⚠️  HIGH RISK: Pulmonary fluid rising. Schedule clinic review within {days_to_event} days."
        elif risk == HeartFailureRisk.MODERATE:
            alert = f"📊 MONITOR: HF risk elevated. Continue monitoring. Predicted event in ~{days_to_event} days if trend persists."

        telemetry = PacemakerTelemetry(
            patient_id=self.patient_id,
            device_id=self.device_id,
            timestamp=(datetime.utcnow() + timedelta(days=self.day)).isoformat() + "Z",
            heart_rate_bpm=round(hr, 1),
            paced_beats_percent=round(paced_pct, 1),
            battery_voltage=round(self.battery_voltage, 3),
            lead_impedance_ohms=round(lead_impedance, 1),
            intrathoracic_impedance_ohms=round(self.impedance, 1),
            activity_hours=round(activity, 2),
            hf_risk_score=round(score, 1),
            hf_risk_level=risk.value,
            alert=alert,
            days_to_predicted_event=days_to_event,
        )
        self.history.append(telemetry)
        return telemetry

    def simulate_30_day_report(self) -> List[PacemakerTelemetry]:
        """Simulate 30 days of telemetry with gradual deterioration after day 15."""
        print(f"\n{'='*75}")
        print(f"  Connected Pacemaker Telemetry — Patient: {self.patient_id}")
        print(f"  Device: {self.device_id}")
        print(f"  Simulating 30-day remote monitoring report...")
        print(f"{'='*75}")
        print(f"{'Day':>4} | {'HR':>5} | {'Impedance (Ω)':>14} | {'HF Score':>9} | {'Risk':>10} | Alert")
        print("-" * 90)

        for day in range(1, 31):
            deteriorating = day > 15  # Fluid starts accumulating after day 15
            t = self.simulate_day(deteriorating=deteriorating)
            risk_icons = {"LOW": "🟢", "MODERATE": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}
            icon = risk_icons.get(t.hf_risk_level, "⚪")
            alert_flag = "⚠️ " if t.alert else ""
            print(f"{day:>4} | {t.heart_rate_bpm:>5.1f} | {t.intrathoracic_impedance_ohms:>14.1f} | "
                  f"{t.hf_risk_score:>9.1f} | {icon} {t.hf_risk_level:<8} | {alert_flag}")

        print(f"\n[Pacemaker] 30-day report complete.")
        critical = [t for t in self.history if t.hf_risk_level in ("HIGH", "CRITICAL")]
        print(f"  High/Critical risk days: {len(critical)}")
        if critical:
            first = critical[0]
            print(f"  First high-risk day:     Day {self.history.index(first)+1}")
            print(f"  First alert:             {first.alert}")
        return self.history

    def export_json(self, filepath: str = "pacemaker_telemetry.json"):
        with open(filepath, "w") as f:
            json.dump([asdict(t) for t in self.history], f, indent=2)
        print(f"[Pacemaker] Telemetry exported to {filepath}")


if __name__ == "__main__":
    pm = PacemakerSimulator(patient_id="PT-20240003")
    pm.simulate_30_day_report()
    pm.export_json()
