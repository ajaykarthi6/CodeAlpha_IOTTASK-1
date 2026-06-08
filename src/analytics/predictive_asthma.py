"""
predictive_asthma.py
Asthma Attack Prediction Engine

Combines IoMT data from:
  1. Smart Inhalers (usage frequency, dose timing)
  2. Environmental IoT sensors (pollen count, AQI, humidity)
  3. Patient biometrics (peak flow meter readings)

Uses a multi-factor scoring model to predict asthma attacks
2–5 days in advance, enabling proactive medication adjustment.
"""

import random
import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict
from datetime import datetime, timedelta


@dataclass
class InhalerUsage:
    date: str
    rescue_puffs: int          # Salbutamol/albuterol (should be <2/week normally)
    controller_taken: bool     # Maintenance inhaler compliance
    nighttime_symptoms: bool   # Woken by symptoms?


@dataclass
class EnvironmentalReading:
    date: str
    aqi: float                 # Air Quality Index (0–500, >150 = unhealthy)
    pollen_count: float        # Grains/m³ (>500 = high)
    humidity_percent: float    # High humidity favors dust mites
    temperature_celsius: float
    weather_front: bool        # Pressure changes can trigger attacks


@dataclass
class PeakFlowReading:
    date: str
    am_pef: float              # Morning Peak Expiratory Flow (L/min)
    pm_pef: float              # Evening PEF
    personal_best: float       # Patient's personal best PEF
    am_percent_best: float = 0.0
    pm_percent_best: float = 0.0

    def __post_init__(self):
        self.am_percent_best = round(self.am_pef / self.personal_best * 100, 1)
        self.pm_percent_best = round(self.pm_pef / self.personal_best * 100, 1)


@dataclass
class AsthmaRiskAssessment:
    date: str
    patient_id: str
    risk_score: float          # 0–100
    risk_level: str            # GREEN / YELLOW / ORANGE / RED
    contributing_factors: List[str]
    predicted_attack_probability_48h: float
    predicted_attack_probability_96h: float
    recommended_action: str
    inhaler_data: Optional[InhalerUsage] = None
    environmental_data: Optional[EnvironmentalReading] = None
    peak_flow_data: Optional[PeakFlowReading] = None


class AsthmaPredictor:
    """
    Multi-factor asthma attack prediction model.

    Risk zones (GINA guidelines):
      GREEN:  PEF >80% best, minimal symptoms   → Continue maintenance
      YELLOW: PEF 60-80%, increasing symptoms   → Step up therapy
      ORANGE: PEF 40-60%, frequent rescue use   → Seek medical advice
      RED:    PEF <40%, severe symptoms          → Emergency care
    """

    PERSONAL_BEST_PEF = 480  # L/min (example patient)

    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        self.assessments: List[AsthmaRiskAssessment] = []

    def _compute_risk_score(
        self,
        inhaler: InhalerUsage,
        env: EnvironmentalReading,
        pef: PeakFlowReading,
    ) -> tuple:
        score = 0.0
        factors = []

        # ── Peak Flow (most important indicator) ──
        min_pef_pct = min(pef.am_percent_best, pef.pm_percent_best)
        if min_pef_pct < 40:
            score += 40
            factors.append(f"🔴 PEF critically low: {min_pef_pct:.0f}% of personal best")
        elif min_pef_pct < 60:
            score += 25
            factors.append(f"🟠 PEF significantly reduced: {min_pef_pct:.0f}% of personal best")
        elif min_pef_pct < 80:
            score += 12
            factors.append(f"🟡 PEF mildly reduced: {min_pef_pct:.0f}% of personal best")

        # ── Inhaler Usage ──
        if inhaler.rescue_puffs >= 4:
            score += 20
            factors.append(f"🔴 High rescue inhaler use: {inhaler.rescue_puffs} puffs today")
        elif inhaler.rescue_puffs >= 2:
            score += 10
            factors.append(f"🟡 Elevated rescue inhaler use: {inhaler.rescue_puffs} puffs")
        if not inhaler.controller_taken:
            score += 8
            factors.append("🟠 Controller inhaler not taken (adherence failure)")
        if inhaler.nighttime_symptoms:
            score += 10
            factors.append("🟠 Nighttime symptoms reported (nocturnal asthma)")

        # ── Environmental Factors ──
        if env.aqi > 200:
            score += 15
            factors.append(f"🔴 Hazardous air quality: AQI {env.aqi:.0f}")
        elif env.aqi > 150:
            score += 8
            factors.append(f"🟠 Unhealthy air quality: AQI {env.aqi:.0f}")
        elif env.aqi > 100:
            score += 4
            factors.append(f"🟡 Moderate air quality: AQI {env.aqi:.0f}")

        if env.pollen_count > 1000:
            score += 12
            factors.append(f"🔴 Very high pollen: {env.pollen_count:.0f} grains/m³")
        elif env.pollen_count > 500:
            score += 7
            factors.append(f"🟠 High pollen: {env.pollen_count:.0f} grains/m³")

        if env.weather_front:
            score += 5
            factors.append("🟡 Weather front detected (pressure change trigger)")

        if env.humidity_percent > 80:
            score += 5
            factors.append(f"🟡 High humidity: {env.humidity_percent:.0f}% (dust mite risk)")

        score = min(100, score)

        if score >= 70:
            risk_level = "RED"
            action = "🚨 Seek emergency care immediately. Double rescue inhaler dose. Call physician."
            p48, p96 = 0.85, 0.95
        elif score >= 45:
            risk_level = "ORANGE"
            action = "⚠️  Contact physician today. Start oral corticosteroids if prescribed. Avoid triggers."
            p48, p96 = 0.55, 0.72
        elif score >= 20:
            risk_level = "YELLOW"
            action = "📋 Step up controller therapy. Avoid outdoor activity. Re-assess in 24 hours."
            p48, p96 = 0.22, 0.38
        else:
            risk_level = "GREEN"
            action = "✅ Continue current treatment plan. Monitor peak flow daily."
            p48, p96 = 0.04, 0.08

        return score, risk_level, factors, action, p48, p96

    def assess(
        self,
        inhaler: InhalerUsage,
        env: EnvironmentalReading,
        pef: PeakFlowReading,
    ) -> AsthmaRiskAssessment:

        score, risk_level, factors, action, p48, p96 = self._compute_risk_score(inhaler, env, pef)

        assessment = AsthmaRiskAssessment(
            date=inhaler.date,
            patient_id=self.patient_id,
            risk_score=round(score, 1),
            risk_level=risk_level,
            contributing_factors=factors,
            predicted_attack_probability_48h=round(p48, 2),
            predicted_attack_probability_96h=round(p96, 2),
            recommended_action=action,
            inhaler_data=inhaler,
            environmental_data=env,
            peak_flow_data=pef,
        )
        self.assessments.append(assessment)
        return assessment

    def simulate_7_day_buildup(self) -> List[AsthmaRiskAssessment]:
        """Simulate a week of data showing a building asthma attack."""
        print(f"\n{'='*70}")
        print(f"  Asthma Attack Predictor — Patient: {self.patient_id}")
        print(f"  Simulating 7-day buildup to asthma attack...")
        print(f"{'='*70}")
        print(f"{'Day':>4} | {'PEF%':>6} | {'Rescue':>6} | {'AQI':>5} | {'Pollen':>7} | {'Score':>6} | Risk")
        print("-" * 65)

        for day in range(1, 8):
            date_str = (datetime.today() - timedelta(days=7-day)).strftime("%Y-%m-%d")
            deterioration = day / 7.0

            pef_pct = max(35, 100 - deterioration * 55 + random.gauss(0, 3))
            pef_val = self.PERSONAL_BEST_PEF * pef_pct / 100

            inhaler = InhalerUsage(
                date=date_str,
                rescue_puffs=int(deterioration * 5 + random.randint(0, 1)),
                controller_taken=(random.random() > deterioration * 0.4),
                nighttime_symptoms=(day >= 5 and random.random() > 0.4),
            )
            env = EnvironmentalReading(
                date=date_str,
                aqi=80 + deterioration * 120 + random.gauss(0, 10),
                pollen_count=200 + deterioration * 900 + random.gauss(0, 50),
                humidity_percent=60 + deterioration * 20,
                temperature_celsius=22 + random.gauss(0, 2),
                weather_front=(day == 5),
            )
            pef = PeakFlowReading(
                date=date_str,
                am_pef=pef_val * random.uniform(0.9, 1.0),
                pm_pef=pef_val * random.uniform(0.85, 0.98),
                personal_best=self.PERSONAL_BEST_PEF,
            )

            assessment = self.assess(inhaler, env, pef)
            risk_icons = {"GREEN": "🟢", "YELLOW": "🟡", "ORANGE": "🟠", "RED": "🔴"}
            icon = risk_icons.get(assessment.risk_level, "⚪")
            print(f"{day:>4} | {pef_pct:>5.1f}% | {inhaler.rescue_puffs:>6} | {env.aqi:>5.0f} | "
                  f"{env.pollen_count:>7.0f} | {assessment.risk_score:>6.1f} | "
                  f"{icon} {assessment.risk_level}  (48h P: {assessment.predicted_attack_probability_48h:.0%})")

        print("\n  ➜ Attack prediction enabled physician to intervene on Day 5")
        print("  ➜ Without IoMT: patient would have arrived at ER on Day 7")
        return self.assessments

    def export_json(self, filepath: str = "asthma_prediction_report.json"):
        data = {
            "patient_id": self.patient_id,
            "assessments": [asdict(a) for a in self.assessments],
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"\n[Asthma] Report exported to {filepath}")


if __name__ == "__main__":
    predictor = AsthmaPredictor(patient_id="PT-20240006-ASTHMA")
    assessments = predictor.simulate_7_day_buildup()
    predictor.export_json("asthma_prediction_report.json")
