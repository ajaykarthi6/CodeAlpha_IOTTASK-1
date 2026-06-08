# 📱 IoMT Device Catalog

A reference guide to all device types covered in the research report.

---

## 1. Continuous Glucose Monitors (CGMs)

| Field | Details |
|-------|---------|
| **Example Devices** | Abbott FreeStyle Libre 3, Dexcom G7, Medtronic Guardian 4 |
| **Mechanism** | Sub-dermal glucose-oxidase filament |
| **Sampling Rate** | Every 1–5 minutes |
| **Connectivity** | Bluetooth LE → smartphone |
| **Data Output** | Glucose mg/dL, trend arrow, estimated HbA1c |
| **Clinical Use** | Type 1 & Type 2 diabetes management |
| **Wear Duration** | 10–15 days (sensor replaced) |
| **FDA Status** | Cleared / Approved |
| **Key Innovation** | Replaces finger-prick testing; enables closed-loop "artificial pancreas" |

**Alert Thresholds:**
- Critical Low: < 54 mg/dL
- Low: < 70 mg/dL  
- High: > 180 mg/dL
- Critical High: > 300 mg/dL

---

## 2. Clinical-Grade ECG Patches

| Field | Details |
|-------|---------|
| **Example Devices** | iRhythm Zio XT, Biotricity Bioflux, Carnation Ambulatory Monitor |
| **Mechanism** | Single-lead or multi-lead surface ECG electrodes |
| **Sampling Rate** | 128–256 Hz continuous |
| **Connectivity** | BLE (real-time) or store-and-forward (upload at end of wear) |
| **Wear Duration** | 7–14 days |
| **Clinical Use** | Paroxysmal AFib detection, cryptogenic stroke workup |
| **Key Innovation** | Detects intermittent arrhythmias missed by 24h Holter monitors |

**Detected Arrhythmias:**
- Atrial Fibrillation (AFib) → stroke risk
- Atrial Flutter
- SVT (supraventricular tachycardia)
- Bradycardia / AV Block
- Premature contractions (PACs/PVCs)

---

## 3. Ingestible Sensors (Smart Pills)

| Field | Details |
|-------|---------|
| **Example Devices** | Proteus Digital Health / Abilify MyCite (aripiprazole + sensor) |
| **Mechanism** | Copper-magnesium galvanic cell activated by stomach acid |
| **Signal Path** | Pill → gastric signal → abdominal patch → smartphone → cloud |
| **Clinical Use** | Medication adherence monitoring (psychiatry, geriatrics) |
| **FDA Status** | First FDA-approved digital medicine (2017) |
| **Key Innovation** | Objective adherence data; eliminates self-report bias |

---

## 4. Connected Pacemakers & CRT Devices

| Field | Details |
|-------|---------|
| **Example Devices** | Medtronic Azure, Abbott Gallant, Boston Scientific Resonate |
| **Mechanism** | Intracardiac electrical leads + impedance measurement |
| **Connectivity** | MICS band RF → bedside transmitter → secure cloud |
| **Transmission** | Nightly automatic transmission while patient sleeps |
| **Data Output** | Pacing %, HR, intrathoracic impedance, activity level, HRV |
| **Key Innovation** | Predicts HF hospitalization 2–3 weeks early via impedance trend |

**Heart Failure Warning Signs (Implant-Detected):**
1. Falling intrathoracic impedance (fluid in lungs)
2. Reduced patient activity
3. Reduced heart rate variability
4. Elevated resting/night heart rate
5. Increased AF burden

---

## 5. Smart Beds & Pressure Mapping Systems

| Field | Details |
|-------|---------|
| **Example Devices** | Hill-Rom Smart Bed, Stryker InTouch, Wellsense MAP System |
| **Mechanism** | Resistive or capacitive pressure sensor matrix (64–2000 sensors) |
| **Sampling Rate** | 1 Hz continuous |
| **Clinical Use** | Pressure ulcer prevention, fall prevention, vital sign monitoring |
| **Key Innovation** | Non-contact vital monitoring (HR, RR) through mattress |

---

## 6. Ambient Assisted Living (AAL) Sensors

| Sensor Type | Technology | Detects |
|-------------|------------|---------|
| Passive Infrared (PIR) | IR motion | Room occupancy, movement patterns |
| Door/window contact | Magnetic reed switch | Exit/entry events |
| Smart plug monitors | Current sensing | Appliance usage (kettle = morning routine) |
| Water flow sensors | Ultrasonic | Bathroom usage duration |
| Medication dispensers | RFID + weight | Pill dispensing events |
| Bed pressure mats | Piezoelectric | Sleep duration, restlessness |

---

## 7. Smart Inhalers

| Field | Details |
|-------|---------|
| **Example Devices** | Propeller Health, Hailie (Adherium), Cohero Health |
| **Mechanism** | Sensor clip attaches to standard MDI or DPI inhaler |
| **Connectivity** | Bluetooth → smartphone |
| **Data Captured** | Date/time of each actuation, GPS location |
| **Clinical Use** | COPD & asthma adherence monitoring, trigger identification |
| **Key Innovation** | Identifies personal triggers by correlating usage with location/weather |

---

## 8. Wearable Multi-Parameter Monitors

| Field | Details |
|-------|---------|
| **Example Devices** | Masimo W1, Biobeat patch, Vital Connect HealthPatch |
| **Parameters** | SpO2, HR, RR, skin temp, posture, activity |
| **Clinical Use** | Step-down unit monitoring, RPM post-discharge |
| **Key Innovation** | Hospital-grade monitoring without bedside equipment |
