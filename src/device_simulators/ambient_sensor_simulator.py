"""
ambient_sensor_simulator.py
Ambient Assisted Living (AAL) Sensor System Simulator

Simulates a privacy-preserving passive infrared (PIR) and
smart environment sensor network for elderly patients living
independently at home.

Key innovation: Detects health crises from ROUTINE DEVIATIONS
without using cameras — preserving dignity and privacy.

Monitored behaviors:
- Refrigerator door opens (meal/hydration proxy)
- Bathroom occupancy duration (fall detection)
- Bedroom wake/sleep patterns
- Front door usage (going outside = good activity)
- Motion in living areas (general activity level)
"""

import random
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict
from enum import Enum


class AlertSeverity(Enum):
    INFO     = "INFO"
    WARNING  = "WARNING"
    URGENT   = "URGENT"
    CRITICAL = "CRITICAL"


@dataclass
class SensorEvent:
    sensor_id: str
    sensor_type: str
    location: str
    timestamp: str
    event: str            # "TRIGGERED", "CLEARED", "DURATION_EXCEEDED"
    duration_seconds: Optional[float] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class DailyHealthSummary:
    patient_id: str
    date: str
    fridge_opens: int
    bathroom_visits: int
    longest_bathroom_duration_min: float
    bedroom_wake_time: str
    bedroom_sleep_time: str
    front_door_exits: int
    motion_events: int
    risk_score: float         # 0–100
    alerts: List[dict] = field(default_factory=list)
    overall_status: str = "NORMAL"


class AmbientSensorSimulator:
    """
    Simulates an Ambient Assisted Living (AAL) sensor network.

    Normal daily baseline for an elderly patient:
    - Fridge opens:        6–10 times/day (meals, drinks)
    - Bathroom visits:     5–8 times/day, each < 20 min
    - Wake time:           06:00–08:00
    - Sleep time:          21:00–23:00
    - Door exits:          1–3 times/day
    - Motion events:       30–60 per day
    """

    NORMAL_BASELINES = {
        "fridge_opens":         (6, 10),
        "bathroom_visits":      (5, 8),
        "bathroom_max_min":     20,       # Alert if > 20 min
        "wake_hour_range":      (6, 8),
        "sleep_hour_range":     (21, 23),
        "front_door_exits":     (1, 3),
        "motion_events":        (30, 60),
        "fridge_critical_min":  2,        # < 2 opens = possible not eating
    }

    def __init__(self, patient_id: str, home_id: str = "HOME-A001"):
        self.patient_id = patient_id
        self.home_id = home_id
        self.history: List[DailyHealthSummary] = []
        self.events: List[SensorEvent] = []

    def _make_timestamp(self, date: datetime, hour: int, minute: int = 0) -> str:
        return date.replace(hour=hour, minute=minute, second=0).isoformat()

    def _generate_normal_day(self, date: datetime) -> DailyHealthSummary:
        b = self.NORMAL_BASELINES
        return DailyHealthSummary(
            patient_id=self.patient_id,
            date=date.date().isoformat(),
            fridge_opens=random.randint(*b["fridge_opens"]),
            bathroom_visits=random.randint(*b["bathroom_visits"]),
            longest_bathroom_duration_min=random.uniform(3, 12),
            bedroom_wake_time=self._make_timestamp(date, random.randint(*b["wake_hour_range"]), random.randint(0, 30)),
            bedroom_sleep_time=self._make_timestamp(date, random.randint(*b["sleep_hour_range"]), random.randint(0, 30)),
            front_door_exits=random.randint(*b["front_door_exits"]),
            motion_events=random.randint(*b["motion_events"]),
            risk_score=random.uniform(5, 20),
            overall_status="NORMAL",
        )

    def _generate_crisis_day(self, date: datetime, crisis_type: str) -> DailyHealthSummary:
        """Simulate a day where something is wrong."""
        base = self._generate_normal_day(date)
        alerts = []

        if crisis_type == "NOT_EATING":
            base.fridge_opens = random.randint(0, 1)
            base.risk_score = 75
            alerts.append({
                "severity": AlertSeverity.URGENT.value,
                "sensor": "FRIDGE_SENSOR",
                "message": f"⚠️  URGENT: Fridge opened only {base.fridge_opens} time(s) today. "
                           f"Patient may not be eating or drinking. Check-in required.",
                "threshold": "< 2 opens/day",
                "actual": f"{base.fridge_opens} opens",
            })

        elif crisis_type == "BATHROOM_FALL":
            base.longest_bathroom_duration_min = random.uniform(35, 90)
            base.risk_score = 90
            alerts.append({
                "severity": AlertSeverity.CRITICAL.value,
                "sensor": "BATHROOM_PIR",
                "message": f"🚨 CRITICAL: Patient in bathroom for {base.longest_bathroom_duration_min:.0f} minutes. "
                           f"Possible fall. Emergency contact notified.",
                "threshold": "< 20 min",
                "actual": f"{base.longest_bathroom_duration_min:.0f} min",
            })

        elif crisis_type == "INACTIVE":
            base.motion_events = random.randint(2, 6)
            base.fridge_opens = random.randint(1, 2)
            base.front_door_exits = 0
            base.risk_score = 65
            alerts.append({
                "severity": AlertSeverity.WARNING.value,
                "sensor": "MOTION_NETWORK",
                "message": f"⚠️  WARNING: Very low activity detected ({base.motion_events} motion events). "
                           f"Patient has not left home. Possible illness or depression.",
                "threshold": "> 30 motion events/day",
                "actual": f"{base.motion_events} events",
            })

        elif crisis_type == "UNUSUAL_WAKE":
            wake_hour = random.choice([2, 3, 4])
            base.bedroom_wake_time = self._make_timestamp(date, wake_hour)
            base.risk_score = 45
            alerts.append({
                "severity": AlertSeverity.INFO.value,
                "sensor": "BEDROOM_PIR",
                "message": f"ℹ️  INFO: Patient woke at {wake_hour}:00 AM — outside normal pattern (6–8 AM). "
                           f"Monitor for 2+ consecutive days.",
                "threshold": "06:00–08:00 wake window",
                "actual": f"0{wake_hour}:00 AM",
            })

        base.alerts = alerts
        base.overall_status = "ALERT" if alerts else "NORMAL"
        return base

    def simulate_week(self, include_crises: bool = True) -> List[DailyHealthSummary]:
        """Simulate 7 days of ambient sensor monitoring."""
        print(f"\n{'='*70}")
        print(f"  Ambient Assisted Living Sensor System")
        print(f"  Patient: {self.patient_id} | Home: {self.home_id}")
        print(f"  7-Day Monitoring Report")
        print(f"{'='*70}")
        print(f"{'Day':<5} | {'Date':<12} | {'Fridge':>6} | {'Bathrm':>6} | {'Max Bath':>9} | {'Motion':>7} | {'Risk':>5} | Status")
        print("-" * 80)

        summaries = []
        base_date = datetime.utcnow().replace(hour=0, minute=0, second=0)

        # Crisis schedule: realistic sparse crises
        crisis_schedule = {
            3: "NOT_EATING",
            5: "BATHROOM_FALL",
            6: "INACTIVE",
        } if include_crises else {}

        for i in range(7):
            date = base_date + timedelta(days=i)
            crisis = crisis_schedule.get(i)

            if crisis:
                summary = self._generate_crisis_day(date, crisis)
            else:
                summary = self._generate_normal_day(date)

            summaries.append(summary)
            self.history.append(summary)

            status_icons = {"NORMAL": "🟢", "ALERT": "🔴"}
            icon = status_icons.get(summary.overall_status, "⚪")
            bath_flag = "🚨" if summary.longest_bathroom_duration_min > 20 else ""

            print(f"Day {i+1:<2} | {summary.date} | {summary.fridge_opens:>6} | "
                  f"{summary.bathroom_visits:>6} | {summary.longest_bathroom_duration_min:>7.1f}m {bath_flag} | "
                  f"{summary.motion_events:>7} | {summary.risk_score:>5.1f} | {icon} {summary.overall_status}")

            if summary.alerts:
                for a in summary.alerts:
                    print(f"         └─ [{a['severity']}] {a['message']}")

        print(f"\n[AAL] Week simulation complete.")
        alert_days = [s for s in summaries if s.alerts]
        print(f"  Alert days:    {len(alert_days)}/7")
        print(f"  Total alerts:  {sum(len(s.alerts) for s in summaries)}")
        return summaries

    def export_json(self, filepath: str = "aal_weekly_report.json"):
        with open(filepath, "w") as f:
            json.dump([asdict(s) for s in self.history], f, indent=2)
        print(f"[AAL] Report exported to {filepath}")


if __name__ == "__main__":
    aal = AmbientSensorSimulator(patient_id="PT-20240004-ELDERLY")
    aal.simulate_week(include_crises=True)
    aal.export_json()
