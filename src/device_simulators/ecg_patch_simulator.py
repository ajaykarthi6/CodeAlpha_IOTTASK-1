"""
ecg_patch_simulator.py
Clinical-Grade ECG Patch Simulator

Simulates a wearable ECG patch that:
- Monitors cardiac rhythm continuously
- Detects arrhythmias (atrial fibrillation, bradycardia, tachycardia)
- Alerts cardiologists to potential stroke risks in real time
- Generates synthetic ECG waveform data
"""

import random
import math
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


class RhythmType(Enum):
    NORMAL_SINUS    = "NORMAL_SINUS_RHYTHM"
    ATRIAL_FIB      = "ATRIAL_FIBRILLATION"
    BRADYCARDIA     = "BRADYCARDIA"
    TACHYCARDIA     = "TACHYCARDIA"
    PREMATURE_BEAT  = "PREMATURE_ATRIAL_CONTRACTION"
    FLUTTER         = "ATRIAL_FLUTTER"


@dataclass
class ECGBeat:
    beat_number: int
    timestamp: str
    rr_interval_ms: float          # Time between R peaks
    heart_rate_bpm: float
    p_wave_present: bool           # Absent in AFib
    qrs_duration_ms: float
    qt_interval_ms: float
    rhythm: str
    alert: Optional[str]


@dataclass
class ECGSession:
    patient_id: str
    device_id: str
    start_time: str
    duration_hours: float
    beats: List[ECGBeat] = field(default_factory=list)
    arrhythmia_events: List[dict] = field(default_factory=list)


class ECGPatchSimulator:
    """
    Simulates a clinical-grade adhesive ECG patch (similar to iRhythm Zio Patch).

    Detects:
    - Atrial Fibrillation (irregular RR intervals, no P waves) → stroke risk
    - Bradycardia (HR < 60 bpm) → possible heart block
    - Tachycardia (HR > 100 bpm) → possible SVT or VT
    - Premature Atrial Contractions (PACs)
    """

    # Alert thresholds
    BRADY_THRESHOLD  = 60    # bpm
    TACHY_THRESHOLD  = 100   # bpm
    AFIB_IRREGULARITY_THRESHOLD = 120  # ms RR interval variation

    def __init__(self, patient_id: str, device_id: str = "ИРHYTHM-ZIO-001"):
        self.patient_id = patient_id
        self.device_id = device_id
        self.beat_count = 0
        self.rr_history: List[float] = []
        self.session = ECGSession(
            patient_id=patient_id,
            device_id=device_id,
            start_time=datetime.utcnow().isoformat() + "Z",
            duration_hours=0,
        )
        self._current_rhythm = RhythmType.NORMAL_SINUS
        self._afib_probability = 0.05  # 5% baseline chance per window

    def _generate_normal_rr(self, base_hr: float = 72) -> float:
        """Generate RR interval for normal sinus rhythm (some variability = HRV)."""
        base_rr = 60000 / base_hr  # ms
        hrv = random.gauss(0, 30)  # Heart rate variability
        return max(500, min(1200, base_rr + hrv))

    def _generate_afib_rr(self) -> float:
        """AFib: chaotically irregular RR intervals."""
        return random.uniform(400, 1000)

    def _detect_rhythm(self) -> Tuple[RhythmType, Optional[str]]:
        """Classify cardiac rhythm from recent RR intervals."""
        if len(self.rr_history) < 5:
            return RhythmType.NORMAL_SINUS, None

        recent_rr = self.rr_history[-10:]
        avg_rr = sum(recent_rr) / len(recent_rr)
        rr_variability = max(recent_rr) - min(recent_rr)
        hr = 60000 / avg_rr

        # Atrial Fibrillation: highly irregular RR intervals
        if rr_variability > self.AFIB_IRREGULARITY_THRESHOLD:
            return (
                RhythmType.ATRIAL_FIB,
                "🚨 ALERT: Atrial Fibrillation detected. High stroke risk — notify cardiologist immediately."
            )

        # Bradycardia
        if hr < self.BRADY_THRESHOLD:
            return (
                RhythmType.BRADYCARDIA,
                f"⚠️  ALERT: Bradycardia — HR {hr:.0f} bpm. Possible AV block or sinus node dysfunction."
            )

        # Tachycardia
        if hr > self.TACHY_THRESHOLD:
            return (
                RhythmType.TACHYCARDIA,
                f"⚠️  ALERT: Tachycardia — HR {hr:.0f} bpm. Rule out SVT, fever, dehydration."
            )

        return RhythmType.NORMAL_SINUS, None

    def _generate_beat(self, force_afib: bool = False) -> ECGBeat:
        """Generate a single cardiac beat with ECG parameters."""
        self.beat_count += 1

        if force_afib or self._current_rhythm == RhythmType.ATRIAL_FIB:
            rr = self._generate_afib_rr()
            p_wave = False  # AFib = absent P waves (chaotic atrial activity)
        else:
            rr = self._generate_normal_rr()
            p_wave = True

        self.rr_history.append(rr)
        if len(self.rr_history) > 50:
            self.rr_history.pop(0)

        hr = 60000 / rr
        rhythm, alert = self._detect_rhythm()
        self._current_rhythm = rhythm

        # QRS duration (normal: 80-120ms; wide = bundle branch block)
        qrs = random.gauss(95, 5)
        # QT interval (normal: 350-450ms corrected; prolonged QT = arrhythmia risk)
        qt = random.gauss(400, 15)

        beat = ECGBeat(
            beat_number=self.beat_count,
            timestamp=datetime.utcnow().isoformat() + "Z",
            rr_interval_ms=round(rr, 1),
            heart_rate_bpm=round(hr, 1),
            p_wave_present=p_wave,
            qrs_duration_ms=round(qrs, 1),
            qt_interval_ms=round(qt, 1),
            rhythm=rhythm.value,
            alert=alert,
        )

        if alert:
            self.session.arrhythmia_events.append({
                "beat_number": self.beat_count,
                "timestamp": beat.timestamp,
                "rhythm": rhythm.value,
                "hr_bpm": round(hr, 1),
                "alert": alert,
            })

        return beat

    def simulate_afib_episode(self, beats: int = 30):
        """Force an AFib episode for demonstration."""
        print(f"\n[ECG] Simulating AFib episode ({beats} beats)...")
        self._current_rhythm = RhythmType.ATRIAL_FIB
        episode_beats = []
        for _ in range(beats):
            beat = self._generate_beat(force_afib=True)
            episode_beats.append(beat)
            self.session.beats.append(beat)
        self._current_rhythm = RhythmType.NORMAL_SINUS
        return episode_beats

    def simulate_session(self, total_beats: int = 100) -> ECGSession:
        """Simulate a multi-beat ECG monitoring session."""
        print(f"\n{'='*65}")
        print(f"  ECG Patch Simulator — Patient: {self.patient_id}")
        print(f"  Device: {self.device_id}")
        print(f"  Simulating {total_beats} cardiac beats...")
        print(f"{'='*65}")
        print(f"{'Beat':>5} | {'HR (bpm)':>9} | {'RR (ms)':>8} | {'P-Wave':>6} | {'Rhythm':<28} | Alert")
        print("-" * 95)

        # Inject an AFib episode in the middle
        afib_start = total_beats // 3
        afib_end   = afib_start + 20

        for i in range(total_beats):
            if afib_start <= i < afib_end:
                beat = self._generate_beat(force_afib=True)
            else:
                beat = self._generate_beat()

            self.session.beats.append(beat)
            self._print_beat(beat)

        print(f"\n[ECG] Session complete.")
        print(f"  Total beats:        {len(self.session.beats)}")
        print(f"  Arrhythmia events:  {len(self.session.arrhythmia_events)}")
        return self.session

    def _print_beat(self, b: ECGBeat):
        p_icon = "✓" if b.p_wave_present else "✗"
        rhythm_short = b.rhythm.replace("_", " ")[:25]
        alert_flag = "⚠️ " if b.alert else ""
        print(f"{b.beat_number:>5} | {b.heart_rate_bpm:>9.1f} | {b.rr_interval_ms:>8.1f} | "
              f"{p_icon:>6} | {rhythm_short:<28} | {alert_flag}")

    def export_report(self, filepath: str = "ecg_report.json"):
        """Export ECG session report as JSON."""
        report = {
            "patient_id": self.session.patient_id,
            "device_id": self.session.device_id,
            "session_start": self.session.start_time,
            "total_beats": len(self.session.beats),
            "arrhythmia_summary": {
                "total_events": len(self.session.arrhythmia_events),
                "events": self.session.arrhythmia_events,
            },
            "heart_rate_stats": self._compute_hr_stats(),
        }
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)
        print(f"[ECG] Report exported to {filepath}")

    def _compute_hr_stats(self) -> dict:
        hrs = [b.heart_rate_bpm for b in self.session.beats]
        if not hrs:
            return {}
        return {
            "mean_hr":   round(sum(hrs) / len(hrs), 1),
            "min_hr":    round(min(hrs), 1),
            "max_hr":    round(max(hrs), 1),
            "afib_beats": sum(1 for b in self.session.beats if "FIBRILLATION" in b.rhythm),
        }


# ── Demo ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ecg = ECGPatchSimulator(patient_id="PT-20240002")
    session = ecg.simulate_session(total_beats=80)
    ecg.export_report("ecg_report.json")

    stats = ecg._compute_hr_stats()
    print(f"\n📊 Heart Rate Statistics:")
    for k, v in stats.items():
        print(f"   {k}: {v}")
