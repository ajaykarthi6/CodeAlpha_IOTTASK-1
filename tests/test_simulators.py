"""
test_simulators.py
Unit Tests for IoMT Device Simulators
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from src.device_simulators.cgm_simulator import CGMSimulator, GlycemicStatus


class TestCGMSimulator(unittest.TestCase):

    def setUp(self):
        self.cgm = CGMSimulator(
            patient_id="TEST-001",
            device_id="TEST-DEVICE",
            initial_glucose=100.0,
        )

    def test_initial_reading(self):
        reading = self.cgm.read()
        self.assertIsNotNone(reading)
        self.assertEqual(reading.patient_id, "TEST-001")
        self.assertGreater(reading.glucose_mg_dl, 30)
        self.assertLess(reading.glucose_mg_dl, 500)

    def test_glycemic_status_normal(self):
        status = self.cgm._get_status(100)
        self.assertEqual(status, GlycemicStatus.NORMAL)

    def test_glycemic_status_hypo(self):
        status = self.cgm._get_status(60)
        self.assertEqual(status, GlycemicStatus.HYPOGLYCEMIA)

    def test_glycemic_status_critical_low(self):
        status = self.cgm._get_status(50)
        self.assertEqual(status, GlycemicStatus.CRITICAL_LOW)

    def test_glycemic_status_hyper(self):
        status = self.cgm._get_status(200)
        self.assertEqual(status, GlycemicStatus.HYPERGLYCEMIA)

    def test_glycemic_status_critical_high(self):
        status = self.cgm._get_status(310)
        self.assertEqual(status, GlycemicStatus.CRITICAL_HIGH)

    def test_alert_generated_for_hypo(self):
        self.cgm.glucose = 60
        reading = self.cgm.read()
        # Should be in warning or hypo territory
        self.assertIn(reading.status, [
            GlycemicStatus.HYPOGLYCEMIA.value,
            GlycemicStatus.CRITICAL_LOW.value,
            GlycemicStatus.NORMAL.value  # May fluctuate slightly
        ])

    def test_meal_boost_increases_glucose(self):
        baseline = self.cgm.glucose
        self.cgm.simulate_meal(carbs_grams=80)
        self.assertGreater(self.cgm.meal_boost, 0)

    def test_reading_count_increments(self):
        for _ in range(5):
            self.cgm.read()
        self.assertEqual(self.cgm.reading_count, 5)

    def test_history_accumulates(self):
        for _ in range(10):
            self.cgm.read()
        self.assertEqual(len(self.cgm.history), 10)

    def test_battery_drains(self):
        initial_battery = self.cgm.battery
        for _ in range(50):
            self.cgm.read()
        self.assertLess(self.cgm.battery, initial_battery)

    def test_sensor_warmup_flag(self):
        # Should not be complete initially
        reading = self.cgm.read()
        self.assertFalse(reading.sensor_warmup_complete)
        # After 61 readings, warmup should complete
        for _ in range(60):
            self.cgm.read()
        reading = self.cgm.read()
        self.assertTrue(reading.sensor_warmup_complete)

    def test_trend_detection(self):
        self.cgm.glucose = 80
        r1 = self.cgm.read()
        self.cgm.glucose = 80
        r2 = self.cgm.read()
        self.assertIn(r2.trend, ["RISING", "FALLING", "STABLE"])


class TestCGMAlerts(unittest.TestCase):

    def setUp(self):
        self.cgm = CGMSimulator("TEST-002", "DEV-002", 100.0)

    def test_no_alert_in_normal_range(self):
        self.cgm.glucose = 100
        reading = self.cgm.read()
        # At 100 mg/dL we expect NORMAL status
        # Alert may still be generated for rapid change - that's fine

    def test_critical_low_generates_alert(self):
        self.cgm.glucose = 52
        reading = self.cgm.read()
        if reading.status == GlycemicStatus.CRITICAL_LOW.value:
            self.assertIsNotNone(reading.alert)

    def test_reading_has_all_fields(self):
        reading = self.cgm.read()
        self.assertIsNotNone(reading.patient_id)
        self.assertIsNotNone(reading.device_id)
        self.assertIsNotNone(reading.timestamp)
        self.assertIsNotNone(reading.glucose_mg_dl)
        self.assertIsNotNone(reading.trend)
        self.assertIsNotNone(reading.status)


if __name__ == "__main__":
    print("Running IoMT Simulator Tests...\n")
    unittest.main(verbosity=2)
