"""
edge_processor.py
Edge Computing Simulation for IoMT Devices

Demonstrates the concept of on-device (edge) processing for
life-critical IoMT use cases — particularly insulin pump control.

Key insight from the report:
  "For an IoT-enabled insulin pump, edge computing ensures that
   life-saving insulin adjustments happen instantaneously based on
   real-time sensor feedback, WITHOUT relying on an internet connection."

This module simulates the decision loop of a closed-loop insulin pump
(artificial pancreas) running entirely on-device.
"""

import time
import random
from dataclasses import dataclass
from typing import List, Tuple
from datetime import datetime


@dataclass
class EdgeDecision:
    timestamp: str
    glucose_mg_dl: float
    insulin_on_board_units: float
    recommended_action: str
    insulin_dose_units: float      # 0 = no dose
    glucagon_dose_mg: float        # 0 = no glucagon
    processing_time_ms: float      # Latency of edge decision
    would_cloud_latency_ms: float  # Simulated cloud round-trip
    edge_advantage_ms: float       # Life-critical time saved


class EdgeInsulinPump:
    """
    Simulates a closed-loop insulin pump (artificial pancreas) with edge computing.

    The control algorithm:
    1. Read glucose from embedded CGM sensor (every 5 min)
    2. Calculate insulin-on-board (IOB) from previous doses
    3. Compute correction dose using PID-like algorithm
    4. Actuate pump motor directly on device (NO CLOUD)

    Critical comparison:
    - Edge latency:  ~50ms (on-device microcontroller)
    - Cloud latency: ~800-2500ms (network round-trip)
    - During hypoglycemia, every millisecond matters
    """

    # Insulin pump parameters
    BASAL_RATE_U_HR   = 0.8   # Units/hour background insulin
    CORRECTION_FACTOR = 50    # 1 unit drops glucose by 50 mg/dL
    CARB_RATIO        = 10    # 1 unit covers 10g carbohydrates
    TARGET_GLUCOSE    = 100   # mg/dL

    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        self.iob = 0.0   # Insulin on board (units)
        self.decisions: List[EdgeDecision] = []

    def _simulate_edge_latency_ms(self) -> float:
        """On-device ARM Cortex-M processor: ~20-80ms"""
        return random.uniform(20, 80)

    def _simulate_cloud_latency_ms(self) -> float:
        """4G LTE round-trip to cloud server: 400-2500ms"""
        return random.uniform(400, 2500)

    def _calculate_correction(self, glucose: float) -> Tuple[float, float, str]:
        """Calculate insulin or glucagon correction needed."""
        error = glucose - self.TARGET_GLUCOSE
        glucagon = 0.0
        insulin  = 0.0

        if glucose < 70:
            # Hypoglycemia: suspend insulin, consider mini-glucagon
            insulin  = 0.0
            glucagon = 0.15 if glucose < 60 else 0.0
            action = f"SUSPEND insulin. {'Mini-glucagon 0.15mg. ' if glucagon else ''}Alert patient."
        elif glucose < 80:
            insulin = 0.0
            action = "SUSPEND basal insulin. Monitor closely."
        elif glucose <= 140:
            # In range: deliver basal only
            insulin = self.BASAL_RATE_U_HR / 12   # Per 5-min interval
            action = "IN RANGE: basal delivery only."
        elif glucose <= 200:
            # Mild hyperglycemia: small correction
            correction = error / self.CORRECTION_FACTOR * 0.5
            insulin = max(0, (self.BASAL_RATE_U_HR / 12) + correction - self.iob * 0.1)
            action = f"MILD HIGH: basal + {correction:.2f}U correction."
        else:
            # Significant hyperglycemia: full correction
            correction = error / self.CORRECTION_FACTOR
            insulin = max(0, (self.BASAL_RATE_U_HR / 12) + correction - self.iob * 0.1)
            action = f"HIGH: {correction:.2f}U correction dose."

        self.iob = max(0, self.iob + insulin - self.iob * 0.05)
        return insulin, glucagon, action

    def process_reading(self, glucose: float) -> EdgeDecision:
        """Process a glucose reading and make an insulin pump decision."""
        start = time.time()

        insulin, glucagon, action = self._calculate_correction(glucose)

        edge_time_ms = self._simulate_edge_latency_ms()
        cloud_time_ms = self._simulate_cloud_latency_ms()

        decision = EdgeDecision(
            timestamp=datetime.utcnow().isoformat() + "Z",
            glucose_mg_dl=glucose,
            insulin_on_board_units=round(self.iob, 3),
            recommended_action=action,
            insulin_dose_units=round(insulin, 3),
            glucagon_dose_mg=round(glucagon, 3),
            processing_time_ms=round(edge_time_ms, 1),
            would_cloud_latency_ms=round(cloud_time_ms, 1),
            edge_advantage_ms=round(cloud_time_ms - edge_time_ms, 1),
        )
        self.decisions.append(decision)
        return decision

    def simulate_control_loop(self, readings: List[float]):
        """Run the closed-loop control algorithm over a series of glucose readings."""
        print(f"\n{'='*75}")
        print(f"  Edge Computing — Closed-Loop Insulin Pump")
        print(f"  Patient: {self.patient_id}")
        print(f"{'='*75}")
        print(f"{'#':>3} | {'Glucose':>8} | {'Action':<35} | {'Edge':>8} | {'Cloud':>8} | {'Saved':>8}")
        print("-" * 85)

        total_edge_ms = 0
        total_cloud_ms = 0

        for i, glucose in enumerate(readings, 1):
            d = self.process_reading(glucose)
            total_edge_ms  += d.processing_time_ms
            total_cloud_ms += d.would_cloud_latency_ms

            status = "🔴 HYPO" if glucose < 70 else ("🟠 HIGH" if glucose > 180 else "🟢 OK  ")
            print(f"{i:>3} | {glucose:>6.0f} {status} | {d.recommended_action:<35} | "
                  f"{d.processing_time_ms:>6.0f}ms | {d.would_cloud_latency_ms:>6.0f}ms | "
                  f"{d.edge_advantage_ms:>6.0f}ms")

        total_saved = total_cloud_ms - total_edge_ms
        print(f"\n  📊 Across {len(readings)} readings:")
        print(f"     Total edge processing time:    {total_edge_ms/1000:.2f} seconds")
        print(f"     If cloud-dependent:            {total_cloud_ms/1000:.2f} seconds")
        print(f"     Total time saved by edge:      {total_saved/1000:.2f} seconds")
        print(f"  ➜ Edge computing critical for insulin pump: no network dependency = no deadly delays")


if __name__ == "__main__":
    pump = EdgeInsulinPump(patient_id="PT-20240007-T1D")

    # Simulate a glucose profile: normal → meal spike → overcorrection hypoglycemia
    glucose_readings = [
        95, 92, 88,                    # Baseline normal
        110, 145, 190, 230, 210,       # Meal spike (post-lunch)
        185, 160, 130, 100,            # Correcting
        82, 68, 54,                    # Overcorrection → hypoglycemia
        62, 75, 88, 95, 100,           # Recovery
    ]
    pump.simulate_control_loop(glucose_readings)
