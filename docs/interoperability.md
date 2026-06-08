# 🔗 IoMT Interoperability Standards

## The Fragmentation Problem

The research report identifies interoperability as a defining challenge:

> "The current IoMT market is highly fragmented. Devices from different manufacturers
> often operate on proprietary protocols, creating data silos."

**The goal:** A smart blood pressure cuff seamlessly "talks" to a smart EHR system,
regardless of who manufactured either device.

---

## Key Standards Stack

```
┌─────────────────────────────────────────────────────────────────┐
│  APPLICATION LAYER  │  HL7 FHIR R4  │  SMART on FHIR  │  CDS  │
├─────────────────────────────────────────────────────────────────┤
│  DATA MODEL LAYER   │  SNOMED CT  │  LOINC  │  RxNorm  │  ICD  │
├─────────────────────────────────────────────────────────────────┤
│  TRANSPORT LAYER    │  HTTPS/REST  │  MQTT  │  WebSockets       │
├─────────────────────────────────────────────────────────────────┤
│  DEVICE LAYER       │  IEEE 11073  │  Continua  │  IHE PCD      │
└─────────────────────────────────────────────────────────────────┘
```

---

## HL7 FHIR (Fast Healthcare Interoperability Resources)

**The backbone of modern health data exchange.**

### Key FHIR Resources Used in IoMT

| FHIR Resource | IoMT Use |
|---------------|---------|
| `Patient` | Patient demographics, consent |
| `Device` | IoMT device registration |
| `DeviceMetric` | Measurement types the device produces |
| `Observation` | Individual vital sign readings |
| `Alert / Flag` | Clinical alert records |
| `CarePlan` | Patient treatment plan incorporating IoMT data |

### Example FHIR Observation (CGM Reading)
```json
{
  "resourceType": "Observation",
  "id": "cgm-reading-001",
  "status": "final",
  "category": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/observation-category",
      "code": "vital-signs"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "99504-3",
      "display": "Glucose [Mass/volume] in Interstitial fluid"
    }]
  },
  "subject": { "reference": "Patient/PT-20240001" },
  "device": { "reference": "Device/FREESTYLE-LIBRE-X1" },
  "effectiveDateTime": "2024-06-08T10:32:00Z",
  "valueQuantity": {
    "value": 142.5,
    "unit": "mg/dL",
    "system": "http://unitsofmeasure.org",
    "code": "mg/dL"
  },
  "interpretation": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
      "code": "H",
      "display": "High"
    }]
  }]
}
```

---

## MQTT for Real-Time IoT Data

MQTT (Message Queuing Telemetry Transport) is the de-facto standard for IoT messaging.

### Why MQTT for IoMT?
- **Lightweight:** 2-byte header — critical for battery-powered devices
- **Pub/Sub model:** Devices publish; multiple subscribers (dashboard, EHR, alert system) receive
- **QoS levels:** QoS 2 (exactly-once delivery) for life-critical data
- **Low bandwidth:** Works on 2G cellular when 4G/5G unavailable

### Topic Naming Convention
```
iomt/{hospital_id}/{ward}/{patient_id}/{device_type}/{vital_type}

Examples:
  iomt/HOSP001/ICU/PT-001/CGM/glucose
  iomt/HOSP001/CARDIO/PT-002/ECG_PATCH/heart_rate
  iomt/HOSP001/HOME/PT-003/PACEMAKER/impedance
```

---

## IEEE 11073 (Device Communication Standard)

IEEE 11073 defines the communication between point-of-care medical devices and computer systems.

| Standard | Covers |
|----------|--------|
| IEEE 11073-10101 | Medical device nomenclature |
| IEEE 11073-10404 | Pulse oximeter |
| IEEE 11073-10406 | Basic ECG |
| IEEE 11073-10417 | Glucose meters |
| IEEE 11073-10441 | Cardiovascular fitness |
| IEEE 11073-20601 | Optimized Exchange Protocol (transport) |

---

## LOINC Codes for Common IoMT Vitals

| Vital Sign | LOINC Code | Display Name |
|-----------|-----------|--------------|
| Heart Rate | 8867-4 | Heart rate |
| SpO2 | 59408-5 | Oxygen saturation by pulse oximetry |
| Systolic BP | 8480-6 | Systolic blood pressure |
| Diastolic BP | 8462-4 | Diastolic blood pressure |
| Body Temperature | 8310-5 | Body temperature |
| Respiratory Rate | 9279-1 | Respiratory rate |
| Blood Glucose | 99504-3 | Glucose [CGM] |
| Body Weight | 29463-7 | Body weight |

---

## Interoperability Maturity Model

| Level | Description | Example |
|-------|-------------|---------|
| **Level 1: Foundational** | Data can be exchanged | File transfer between systems |
| **Level 2: Structural** | Format is standardized | HL7 v2.x messages |
| **Level 3: Semantic** | Meaning is standardized | FHIR + SNOMED CT + LOINC |
| **Level 4: Organizational** | Governance & policy aligned | Regional HIE networks |

**Current IoMT market:** Mostly Level 1–2. The target is Level 3–4.

---

## Open-Source Interoperability Tools

| Tool | Purpose | Link |
|------|---------|-------|
| HAPI FHIR | Java FHIR server | hapifhir.io |
| Microsoft FHIR Server | Azure FHIR implementation | github.com/microsoft/fhir-server |
| Google Cloud Healthcare API | Managed FHIR/HL7/DICOM | cloud.google.com/healthcare-api |
| Open mHealth | Mobile health data schemas | openmhealth.org |
| Continua Design Guidelines | End-to-end interoperability | pchalliance.org |
