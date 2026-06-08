"""
cgm_simulator.py
Continuous Glucose Monitor (CGM) Device Simulator

Simulates a FreeStyle Libre-style CGM that:
- Reads glucose levels every minute
- Detects dangerous glycemic events (spikes / drops)
- Publishes data via MQTT to a physician dashboard
- Demonstrates the IoMT data pipeline end-to-end

Clinical Reference Ranges:
  - Hypoglycemia:   < 70 mg/dL  (DANGEROUS - LOW)
  - Normal:         70–180 mg/dL
  - Hyperglycemia:  > 180 mg/dL (DANGEROUS - HIGH)
  - Critical High:  > 300 mg/dL (CRITICAL)
"""

import time
import random
import json
import math
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Optional, List
from enum import Enum


class GlycemicStatus(Enum):
    CRITICAL_LOW  = "CRITICAL_LOW"    # < 54 mg/dL
    HYPOGLYCEMIA  = "HYPOGLYCEMIA"    # 54–70 mg/dL
    NORMAL        = "NORMAL"          # 70–180 mg/dL
    HYPERGLYCEMIA = "HYPERGLYCEMIA"   # 180–300 mg/dL
    CRITICAL_HIGH = "CRITICAL_HIGH"   # > 300 mg/dL


@dataclass
class CGMReading:
    patient_id: str
    device_id: str
    timestamp: str
    glucose_mg_dl: float
    trend: str                  # "RISING", "FALLING", "STABLE"
    trend_rate: float           # mg/dL per minute
    status: str
    alert: Optional[str]
    battery_percent: int
    sensor_warmup_complete: bool


class CGMSimulator:
    """
    Simulates a clinical-grade Continuous Glucose Monitor (CGM).

    Models realistic physiological glucose patterns including:
    - Post-meal spikes
    - Insulin-driven drops
    - Circadian variation
    - Sensor noise
    """

    ALERT_THRESHOLDS = {
        "CRITICAL_LOW":  54,
        "HYPOGLYCEMIA":  70,
        "HYPERGLYCEMIA": 180,
        "CRITICAL_HIGH": 300,
    }

    def __init__(self, patient_id: str, device_id: str, initial_glucose: float = 100.0):
        self.patient_id = patient_id
        self.device_id = device_id
        self.glucose = initial_glucose
        self.battery = 100
        self.reading_count = 0
        self.history: List[CGMReading] = []
        self.meal_boost = 0.0       # Temporary post-meal glucose elevation
        self.insulin_effect = 0.0   # Temporary insulin-driven drop

    def _get_status(self, glucose: float) -> GlycemicStatus:
        if glucose < 54:
            return GlycemicStatus.CRITICAL_LOW
        elif glucose < 70:
            return GlycemicStatus.HYPOGLYCEMIA
        elif glucose <= 180:
            return GlycemicStatus.NORMAL
        elif glucose <= 300:
            return GlycemicStatus.HYPERGLYCEMIA
        else:
            return GlycemicStatus.CRITICAL_HIGH

    def _get_alert(self, status: GlycemicStatus, trend: str, rate: float) -> Optional[str]:
        alerts = {
            GlycemicStatus.CRITICAL_LOW:  "🚨 CRITICAL: Severe hypoglycemia. Immediate glucose needed!",
            GlycemicStatus.HYPOGLYCEMIA:  "⚠️  ALERT: Low blood sugar. Consume 15g fast-acting carbs.",
            GlycemicStatus.CRITICAL_HIGH: "🚨 CRITICAL: Severe hyperglycemia. Contact physician immediately.",
        }
        base_alert = alerts.get(status)

        # Add predictive alert for rapid trends
        if abs(rate) > 2.0 and status == GlycemicStatus.NORMAL:
            direction = "dropping" if rate < 0 else "rising"
            base_alert = f"📈 PREDICTIVE: Glucose {direction} rapidly at {abs(rate):.1f} mg/dL/min"

        return base_alert

    def simulate_meal(self, carbs_grams: int = 50):
        """Simulate a meal causing a glucose spike."""
        self.meal_boost += carbs_grams * 1.2
        print(f"[{self.patient_id}] 🍽️  Meal simulated: {carbs_grams}g carbs → +{self.meal_boost:.0f} mg/dL boost")

    def simulate_insulin_dose(self, units: float = 5.0):
        """Simulate an insulin dose causing glucose to drop."""
        self.insulin_effect += units * 15
        print(f"[{self.patient_id}] 💉 Insulin simulated: {units}U → -{self.insulin_effect:.0f} mg/dL effect")

    def read(self) -> CGMReading:
        """Take a single CGM reading (simulates 1-minute interval)."""
        self.reading_count += 1

        # Apply physiological dynamics
        prev_glucose = self.glucose

        # Natural mean reversion toward ~100 mg/dL
        reversion = (100 - self.glucose) * 0.02

        # Meal effect (spike then decay)
        meal_effect = self.meal_boost * 0.08
        self.meal_boost = max(0, self.meal_boost - meal_effect)

        # Insulin effect (drop then decay)
        insulin_effect = self.insulin_effect * 0.06
        self.insulin_effect = max(0, self.insulin_effect - insulin_effect)

        # Sensor noise
        noise = random.gauss(0, 1.5)

        # Circadian rhythm (small variation over 24h)
        hour = (self.reading_count / 60) % 24
        circadian = 5 * math.sin(2 * math.pi * (hour - 6) / 24)

        self.glucose = max(40, min(400,
            self.glucose + reversion + meal_effect - insulin_effect + noise + circadian
        ))

        trend_rate = self.glucose - prev_glucose
        if trend_rate > 1.0:
            trend = "RISING"
        elif trend_rate < -1.0:
            trend = "FALLING"
        else:
            trend = "STABLE"

        status = self._get_status(self.glucose)
        alert = self._get_alert(status, trend, trend_rate)

        # Battery drain
        self.battery = max(0, self.battery - 0.005)

        reading = CGMReading(
            patient_id=self.patient_id,
            device_id=self.device_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            glucose_mg_dl=round(self.glucose, 1),
            trend=trend,
            trend_rate=round(trend_rate, 2),
            status=status.value,
            alert=alert,
            battery_percent=int(self.battery),
            sensor_warmup_complete=self.reading_count > 60,
        )

        self.history.append(reading)
        return reading

    def stream(self, duration_minutes: int = 10, interval_seconds: int = 5):
        """
        Stream readings for `duration_minutes` minutes.
        In real deployment: interval_seconds = 60 (one reading per minute).
        Accelerated here for demonstration.
        """
        print(f"\n{'='*60}")
        print(f"  CGM Simulator — Patient: {self.patient_id}")
        print(f"  Device:  {self.device_id}")
        print(f"  Duration: {duration_minutes} min | Sample interval: {interval_seconds}s")
        print(f"{'='*60}\n")

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)

        # Simulate a meal at minute 2
        meal_time = start_time + 120

        try:
            while time.time() < end_time:
                if time.time() >= meal_time and self.meal_boost == 0:
                    self.simulate_meal(carbs_grams=60)

                reading = self.read()
                self._print_reading(reading)

                if reading.alert:
                    self._handle_alert(reading)

                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\n[CGM] Stream interrupted by user.")

        print(f"\n[CGM] Session complete. Total readings: {len(self.history)}")
        return self.history

    def _print_reading(self, r: CGMReading):
        status_icons = {
            "NORMAL":        "🟢",
            "HYPOGLYCEMIA":  "🟡",
            "CRITICAL_LOW":  "🔴",
            "HYPERGLYCEMIA": "🟠",
            "CRITICAL_HIGH": "🔴",
        }
        trend_arrows = {"RISING": "↑", "FALLING": "↓", "STABLE": "→"}

        icon = status_icons.get(r.status, "⚪")
        arrow = trend_arrows.get(r.trend, "→")

        print(f"[{r.timestamp[11:19]}] {icon} {r.glucose_mg_dl:6.1f} mg/dL  "
              f"{arrow} {r.trend:<8} ({r.trend_rate:+.1f}/min)  "
              f"Status: {r.status:<15}  🔋{r.battery_percent}%")

    def _handle_alert(self, r: CGMReading):
        print(f"\n  ╔══════════════════════════════════════════╗")
        print(f"  ║  {r.alert:<42}║")
        print(f"  ╚══════════════════════════════════════════╝\n")
        # In production: send push notification, page physician, trigger EHR alert

    def export_json(self, filepath: str = "cgm_session.json"):
        """Export session history as JSON for dashboard consumption."""
        data = {
            "session_metadata": {
                "patient_id": self.patient_id,
                "device_id": self.device_id,
                "total_readings": len(self.history),
                "exported_at": datetime.utcnow().isoformat() + "Z",
            },
            "readings": [asdict(r) for r in self.history]
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[CGM] Data exported to {filepath}")


# ── Demo ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Create a CGM simulator for a Type 1 diabetic patient
    cgm = CGMSimulator(
        patient_id="PT-20240001",
        device_id="FREESTYLE-LIBRE-X1",
        initial_glucose=95.0,
    )

    # Stream 3 minutes of accelerated readings (5s intervals)
    readings = cgm.stream(duration_minutes=3, interval_seconds=5)

    # Export to JSON
    cgm.export_json("cgm_session.json")

    # Summary statistics
    glucose_values = [r.glucose_mg_dl for r in readings]
    if glucose_values:
        print(f"\n📊 Session Statistics:")
        print(f"   Average glucose:  {sum(glucose_values)/len(glucose_values):.1f} mg/dL")
        print(f"   Min glucose:      {min(glucose_values):.1f} mg/dL")
        print(f"   Max glucose:      {max(glucose_values):.1f} mg/dL")
        in_range = sum(1 for g in glucose_values if 70 <= g <= 180)
        print(f"   Time in range:    {100*in_range/len(glucose_values):.1f}%")
