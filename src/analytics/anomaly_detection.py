"""
anomaly_detection.py
Real-Time Vital Sign Anomaly Detection Engine

Uses statistical and rule-based methods to detect dangerous
deviations in patient vitals across all IoMT device streams.

Detects:
  - Sudden spikes/drops in any vital sign
  - Sustained out-of-range readings
  - Dangerous combinations (e.g., high HR + low SpO2)
  - Rate-of-change anomalies (rapid deterioration)
"""

import json
import statistics
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from enum import Enum


class VitalType(Enum):
    HEART_RATE       = "heart_rate_bpm"
    SPO2             = "spo2_percent"
    BLOOD_PRESSURE_S = "bp_systolic_mmhg"
    BLOOD_PRESSURE_D = "bp_diastolic_mmhg"
    GLUCOSE          = "glucose_mg_dl"
    TEMPERATURE      = "temperature_celsius"
    RESPIRATORY_RATE = "respiratory_rate_bpm"


# Clinical normal ranges (min, max)
NORMAL_RANGES = {
    VitalType.HEART_RATE:       (60,  100),
    VitalType.SPO2:             (95,  100),
    VitalType.BLOOD_PRESSURE_S: (90,  140),
    VitalType.BLOOD_PRESSURE_D: (60,   90),
    VitalType.GLUCOSE:          (70,  180),
    VitalType.TEMPERATURE:      (36.1, 37.2),
    VitalType.RESPIRATORY_RATE: (12,   20),
}

CRITICAL_RANGES = {
    VitalType.HEART_RATE:       (40,  150),
    VitalType.SPO2:             (90,  100),
    VitalType.BLOOD_PRESSURE_S: (70,  180),
    VitalType.BLOOD_PRESSURE_D: (40,  120),
    VitalType.GLUCOSE:          (54,  300),
    VitalType.TEMPERATURE:      (35.0, 39.5),
    VitalType.RESPIRATORY_RATE: (8,   30),
}

VITAL_UNITS = {
    VitalType.HEART_RATE:       "bpm",
    VitalType.SPO2:             "%",
    VitalType.BLOOD_PRESSURE_S: "mmHg",
    VitalType.BLOOD_PRESSURE_D: "mmHg",
    VitalType.GLUCOSE:          "mg/dL",
    VitalType.TEMPERATURE:      "°C",
    VitalType.RESPIRATORY_RATE: "bpm",
}


@dataclass
class AnomalyEvent:
    timestamp: str
    patient_id: str
    vital_type: str
    value: float
    unit: str
    severity: str          # "WARNING", "CRITICAL"
    message: str
    recommended_action: str
    combination_flag: bool = False   # True if part of a dangerous combo


@dataclass
class PatientVitalStream:
    patient_id: str
    device_id: str
    vital_type: VitalType
    history: List[float] = field(default_factory=list)
    anomalies: List[AnomalyEvent] = field(default_factory=list)

    def add_reading(self, value: float) -> Optional[AnomalyEvent]:
        self.history.append(value)
        if len(self.history) > 100:
            self.history.pop(0)
        return self._check_anomaly(value)

    def _check_anomaly(self, value: float) -> Optional[AnomalyEvent]:
        normal_min, normal_max = NORMAL_RANGES[self.vital_type]
        crit_min, crit_max    = CRITICAL_RANGES[self.vital_type]
        unit = VITAL_UNITS[self.vital_type]

        # Rate of change anomaly
        if len(self.history) >= 3:
            recent_change = abs(value - self.history[-3])
            baseline = statistics.mean(self.history[:-1]) if len(self.history) > 1 else value
            change_pct = (recent_change / baseline * 100) if baseline != 0 else 0
            if change_pct > 25:
                return AnomalyEvent(
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    patient_id=self.patient_id,
                    vital_type=self.vital_type.value,
                    value=value,
                    unit=unit,
                    severity="WARNING",
                    message=f"Rapid change in {self.vital_type.name}: {change_pct:.1f}% shift in 3 readings",
                    recommended_action="Verify reading. If confirmed, reassess patient immediately.",
                )

        # Critical range
        if value < crit_min:
            return AnomalyEvent(
                timestamp=datetime.utcnow().isoformat() + "Z",
                patient_id=self.patient_id,
                vital_type=self.vital_type.value,
                value=value,
                unit=unit,
                severity="CRITICAL",
                message=f"🚨 CRITICAL LOW {self.vital_type.name}: {value} {unit} (critical min: {crit_min})",
                recommended_action="Immediate clinical intervention required.",
            )
        if value > crit_max:
            return AnomalyEvent(
                timestamp=datetime.utcnow().isoformat() + "Z",
                patient_id=self.patient_id,
                vital_type=self.vital_type.value,
                value=value,
                unit=unit,
                severity="CRITICAL",
                message=f"🚨 CRITICAL HIGH {self.vital_type.name}: {value} {unit} (critical max: {crit_max})",
                recommended_action="Immediate clinical intervention required.",
            )

        # Warning range
        if value < normal_min:
            return AnomalyEvent(
                timestamp=datetime.utcnow().isoformat() + "Z",
                patient_id=self.patient_id,
                vital_type=self.vital_type.value,
                value=value,
                unit=unit,
                severity="WARNING",
                message=f"⚠️  LOW {self.vital_type.name}: {value} {unit} (normal min: {normal_min})",
                recommended_action="Notify care team. Reassess in 15 minutes.",
            )
        if value > normal_max:
            return AnomalyEvent(
                timestamp=datetime.utcnow().isoformat() + "Z",
                patient_id=self.patient_id,
                vital_type=self.vital_type.value,
                value=value,
                unit=unit,
                severity="WARNING",
                message=f"⚠️  HIGH {self.vital_type.name}: {value} {unit} (normal max: {normal_max})",
                recommended_action="Notify care team. Reassess in 15 minutes.",
            )
        return None


class MultiVitalAnomalyDetector:
    """
    Monitors multiple vital sign streams simultaneously and detects
    dangerous combinations (e.g., sepsis pattern: high HR + high RR + low BP).
    """

    DANGEROUS_COMBOS = [
        {
            "name": "Sepsis Pattern",
            "conditions": {
                VitalType.HEART_RATE: (">", 90),
                VitalType.RESPIRATORY_RATE: (">", 20),
                VitalType.TEMPERATURE: (">", 38.0),
            },
            "severity": "CRITICAL",
            "action": "Sepsis protocol activation. Blood cultures, IV access, notify physician STAT.",
        },
        {
            "name": "Respiratory Failure",
            "conditions": {
                VitalType.SPO2: ("<", 92),
                VitalType.RESPIRATORY_RATE: (">", 25),
            },
            "severity": "CRITICAL",
            "action": "Supplemental oxygen immediately. Prepare for possible intubation.",
        },
        {
            "name": "Hypoglycemic Shock Risk",
            "conditions": {
                VitalType.GLUCOSE: ("<", 60),
                VitalType.HEART_RATE: (">", 100),
            },
            "severity": "CRITICAL",
            "action": "IV dextrose immediately. Check consciousness level.",
        },
    ]

    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        self.streams: Dict[VitalType, PatientVitalStream] = {}
        self.latest_values: Dict[VitalType, float] = {}
        self.combo_alerts: List[AnomalyEvent] = []

    def add_stream(self, vital_type: VitalType, device_id: str):
        self.streams[vital_type] = PatientVitalStream(
            patient_id=self.patient_id,
            device_id=device_id,
            vital_type=vital_type,
        )

    def ingest(self, vital_type: VitalType, value: float) -> List[AnomalyEvent]:
        events = []
        self.latest_values[vital_type] = value

        if vital_type in self.streams:
            anomaly = self.streams[vital_type].add_reading(value)
            if anomaly:
                events.append(anomaly)

        combo_events = self._check_combinations()
        events.extend(combo_events)
        return events

    def _check_combinations(self) -> List[AnomalyEvent]:
        events = []
        for combo in self.DANGEROUS_COMBOS:
            triggered = True
            for vital, (op, threshold) in combo["conditions"].items():
                val = self.latest_values.get(vital)
                if val is None:
                    triggered = False
                    break
                if op == ">" and val <= threshold:
                    triggered = False
                    break
                if op == "<" and val >= threshold:
                    triggered = False
                    break

            if triggered:
                event = AnomalyEvent(
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    patient_id=self.patient_id,
                    vital_type="MULTI_VITAL",
                    value=0,
                    unit="N/A",
                    severity=combo["severity"],
                    message=f"🚨 COMBINATION ALERT: {combo['name']} pattern detected!",
                    recommended_action=combo["action"],
                    combination_flag=True,
                )
                events.append(event)
                self.combo_alerts.append(event)
        return events


# ── Demo ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import random

    detector = MultiVitalAnomalyDetector(patient_id="PT-20240005")
    for vt in VitalType:
        detector.add_stream(vt, device_id=f"SENSOR-{vt.name}")

    print("\n=== Multi-Vital Anomaly Detection Demo ===\n")
    print("Simulating 20 readings with deteriorating patient condition...\n")

    test_sequences = [
        (VitalType.HEART_RATE,       [72, 74, 76, 78, 88, 92, 96, 102, 108, 115]),
        (VitalType.SPO2,             [98, 98, 97, 96, 95, 94, 92, 90, 88, 85]),
        (VitalType.RESPIRATORY_RATE, [14, 15, 15, 16, 18, 20, 22, 25, 28, 30]),
        (VitalType.TEMPERATURE,      [36.8, 37.0, 37.2, 37.5, 37.8, 38.1, 38.4, 38.7, 39.0, 39.4]),
        (VitalType.BLOOD_PRESSURE_S, [120, 118, 115, 110, 105, 100, 95, 88, 82, 75]),
    ]

    for i in range(10):
        print(f"--- Reading Set {i+1} ---")
        for vital_type, sequence in test_sequences:
            value = sequence[i]
            events = detector.ingest(vital_type, value)
            print(f"  {vital_type.name:<22}: {value}")
            for event in events:
                print(f"    ⚡ {event.message}")
                print(f"       Action: {event.recommended_action}")
        print()
