# 🏗️ IoMT System Architecture

## Overview

The IoMT ecosystem is structured in four distinct layers, each building on the one below it.

```
┌─────────────────────────────────────────────────────────────────┐
│                     LAYER 4: CLINICAL LAYER                      │
│   EHR Systems  │  Physician Dashboards  │  Alert Management      │
└───────────────────────────────┬─────────────────────────────────┘
                                │  HL7 FHIR / REST API
┌───────────────────────────────▼─────────────────────────────────┐
│                    LAYER 3: ANALYTICS LAYER                      │
│   AI/ML Models  │  Anomaly Detection  │  Predictive Engines      │
└───────────────────────────────┬─────────────────────────────────┘
                                │  Processed Data Streams
┌───────────────────────────────▼─────────────────────────────────┐
│                   LAYER 2: CONNECTIVITY LAYER                    │
│   MQTT Broker  │  5G/WiFi/BLE  │  Edge Gateway  │  Cloud Ingest │
└───────────────────────────────┬─────────────────────────────────┘
                                │  Raw Sensor Data
┌───────────────────────────────▼─────────────────────────────────┐
│                    LAYER 1: DEVICE LAYER                         │
│   CGM  │  ECG Patch  │  Smart Implant  │  Ambient Sensors        │
└─────────────────────────────────────────────────────────────────┘
```

## Layer 1: Device Layer

The device layer consists of physical IoMT hardware deployed on or near the patient.

| Device | Communication | Sampling Rate | Edge Processing |
|--------|--------------|---------------|-----------------|
| CGM (FreeStyle Libre) | Bluetooth LE | Every 1 min | Glucose trend calculation |
| ECG Patch | Bluetooth LE | 250 Hz continuous | Arrhythmia detection |
| Smart Pacemaker | Proprietary RF | Daily summary | HF decompensation scoring |
| Ambient Sensors (PIR) | Zigbee/Z-Wave | Event-driven | Routine deviation detection |
| Smart Insulin Pump | Bluetooth LE | Every 5 min | Closed-loop PID control |

## Layer 2: Connectivity Layer

### Protocols Used

| Protocol | Use Case | Why |
|----------|----------|-----|
| **Bluetooth LE (BLE)** | Wearable → smartphone | Low power, short range |
| **MQTT** | Smartphone/hub → cloud | Lightweight, pub/sub, low bandwidth |
| **HL7 FHIR** | Cloud → EHR | Healthcare interoperability standard |
| **TLS 1.3** | All connections | End-to-end encryption |
| **5G NR** | High-bandwidth imaging | Low latency, high throughput |

### Edge Gateway

The edge gateway (patient's smartphone or home hub) performs:
- Local data buffering during connectivity loss
- First-pass anomaly detection (reduces cloud traffic 10x)
- Data compression and batching
- Device authentication and authorization

## Layer 3: Analytics Layer

### Real-Time Stream Processing
- Apache Kafka or AWS Kinesis for high-throughput ingestion
- Apache Flink or AWS Lambda for stream processing
- TimescaleDB or InfluxDB for time-series storage

### AI/ML Pipeline
```
Raw Data → Feature Engineering → Model Inference → Alert Generation
    ↓              ↓                    ↓                  ↓
 Sensor       Sliding window        ONNX Runtime      PagerDuty /
  data        aggregations          on Edge or         EHR Alert
              (5m, 1h, 24h)         Cloud GPU          System
```

## Layer 4: Clinical Layer

### EHR Integration
- **SMART on FHIR** for app authorization
- **CDS Hooks** for real-time clinical decision support
- **DICOM** for imaging device integration

### Dashboard Architecture
- Real-time WebSocket connections for live vital displays
- Role-based access control (RBAC):
  - Patient: own data only
  - Nurse: assigned patient ward
  - Physician: full patient panel
  - Admin: system-wide view

## Security Architecture

```
Device → [BLE+AES-128] → Gateway → [TLS 1.3] → Cloud → [RBAC] → Clinician
              ↑                          ↑
         Device cert               Zero-Trust
         (hardware)               Network Policy
```

## Data Flow Example: CGM → Insulin Dose Adjustment

```
1. CGM reads glucose (180 mg/dL) [Device Layer]
2. BLE transmits to smartphone [Connectivity Layer]
3. Edge processor detects rising trend [Edge Processing]
4. MQTT message published to broker [Connectivity Layer]
5. ML model predicts 220 mg/dL in 30 min [Analytics Layer]
6. Alert sent to physician dashboard [Clinical Layer]
7. Physician confirms → insulin pump adjustment sent back [Clinical Layer]
8. Pump receives instruction [Device Layer]
```
