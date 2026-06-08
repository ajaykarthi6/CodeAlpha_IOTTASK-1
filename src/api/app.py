"""
app.py
IoMT Data REST API — FastAPI Application

Provides endpoints for:
  - Ingesting real-time device readings
  - Querying patient vital history
  - Retrieving anomaly alerts
  - Device registration and status

Run with: uvicorn src.api.app:app --reload
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import random

app = FastAPI(
    title="IoMT Research Hub API",
    description="REST API for IoMT device data ingestion, querying, and alerting.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory storage (replace with TimescaleDB / InfluxDB in production) ──
_readings_store: Dict[str, List[dict]] = {}
_alerts_store:   List[dict] = []
_devices_store:  Dict[str, dict] = {}


# ── Pydantic Models ──

class DeviceReading(BaseModel):
    patient_id: str
    device_id: str
    device_type: str     # "CGM", "ECG_PATCH", "PACEMAKER", "AMBIENT"
    timestamp: str
    vital_type: str
    value: float
    unit: str
    status: Optional[str] = "NORMAL"
    metadata: Optional[Dict[str, Any]] = {}


class DeviceRegistration(BaseModel):
    device_id: str
    device_type: str
    patient_id: str
    manufacturer: str
    firmware_version: str
    battery_percent: int = 100


class AlertResponse(BaseModel):
    alert_id: str
    timestamp: str
    patient_id: str
    device_id: str
    severity: str
    message: str
    acknowledged: bool = False


# ── Endpoints ──

@app.get("/", tags=["Health"])
def root():
    return {
        "service": "IoMT Research Hub API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "uptime_seconds": 99999}


@app.post("/devices/register", tags=["Devices"])
def register_device(device: DeviceRegistration):
    """Register a new IoMT device and associate it with a patient."""
    _devices_store[device.device_id] = {
        **device.dict(),
        "registered_at": datetime.utcnow().isoformat() + "Z",
        "last_seen": None,
        "online": True,
    }
    return {
        "message": f"Device {device.device_id} registered successfully.",
        "device": _devices_store[device.device_id],
    }


@app.get("/devices", tags=["Devices"])
def list_devices(patient_id: Optional[str] = Query(None)):
    """List all registered devices, optionally filtered by patient."""
    devices = list(_devices_store.values())
    if patient_id:
        devices = [d for d in devices if d["patient_id"] == patient_id]
    return {"count": len(devices), "devices": devices}


@app.post("/readings", tags=["Readings"], status_code=201)
def ingest_reading(reading: DeviceReading):
    """Ingest a real-time vital sign reading from an IoMT device."""
    key = reading.patient_id
    if key not in _readings_store:
        _readings_store[key] = []

    reading_dict = reading.dict()
    reading_dict["received_at"] = datetime.utcnow().isoformat() + "Z"
    _readings_store[key].append(reading_dict)

    # Keep only last 1000 readings per patient
    if len(_readings_store[key]) > 1000:
        _readings_store[key] = _readings_store[key][-1000:]

    # Update device last_seen
    if reading.device_id in _devices_store:
        _devices_store[reading.device_id]["last_seen"] = reading_dict["received_at"]

    return {"message": "Reading ingested.", "reading_id": f"RD-{len(_readings_store[key]):05d}"}


@app.get("/readings/{patient_id}", tags=["Readings"])
def get_readings(
    patient_id: str,
    vital_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    """Retrieve recent vital sign readings for a patient."""
    readings = _readings_store.get(patient_id, [])
    if vital_type:
        readings = [r for r in readings if r["vital_type"] == vital_type]
    readings = readings[-limit:]
    return {
        "patient_id": patient_id,
        "count": len(readings),
        "readings": readings,
    }


@app.get("/readings/{patient_id}/latest", tags=["Readings"])
def get_latest_readings(patient_id: str):
    """Get the most recent reading for each vital type for a patient."""
    readings = _readings_store.get(patient_id, [])
    latest: Dict[str, dict] = {}
    for r in readings:
        latest[r["vital_type"]] = r
    return {
        "patient_id": patient_id,
        "latest_vitals": latest,
        "vital_count": len(latest),
    }


@app.post("/alerts", tags=["Alerts"], status_code=201)
def create_alert(alert: AlertResponse):
    """Create a new clinical alert from a device anomaly detection."""
    _alerts_store.append(alert.dict())
    return {"message": "Alert created.", "alert_id": alert.alert_id}


@app.get("/alerts", tags=["Alerts"])
def get_alerts(
    patient_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    unacknowledged_only: bool = Query(False),
    limit: int = Query(20, ge=1, le=200),
):
    """Retrieve clinical alerts with optional filters."""
    alerts = list(_alerts_store)
    if patient_id:
        alerts = [a for a in alerts if a["patient_id"] == patient_id]
    if severity:
        alerts = [a for a in alerts if a["severity"].upper() == severity.upper()]
    if unacknowledged_only:
        alerts = [a for a in alerts if not a["acknowledged"]]
    alerts = alerts[-limit:]
    return {"count": len(alerts), "alerts": alerts}


@app.patch("/alerts/{alert_id}/acknowledge", tags=["Alerts"])
def acknowledge_alert(alert_id: str):
    """Mark a clinical alert as acknowledged by care staff."""
    for alert in _alerts_store:
        if alert["alert_id"] == alert_id:
            alert["acknowledged"] = True
            alert["acknowledged_at"] = datetime.utcnow().isoformat() + "Z"
            return {"message": f"Alert {alert_id} acknowledged."}
    raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found.")


@app.get("/patients/{patient_id}/summary", tags=["Patients"])
def get_patient_summary(patient_id: str):
    """Get a comprehensive patient IoMT summary dashboard."""
    readings = _readings_store.get(patient_id, [])
    latest: Dict[str, dict] = {}
    for r in readings:
        latest[r["vital_type"]] = r

    patient_alerts = [a for a in _alerts_store if a["patient_id"] == patient_id]
    critical_alerts = [a for a in patient_alerts if a["severity"] == "CRITICAL" and not a["acknowledged"]]

    devices = [d for d in _devices_store.values() if d["patient_id"] == patient_id]

    return {
        "patient_id": patient_id,
        "summary_generated_at": datetime.utcnow().isoformat() + "Z",
        "total_readings": len(readings),
        "latest_vitals": latest,
        "active_devices": len(devices),
        "total_alerts": len(patient_alerts),
        "unacknowledged_critical_alerts": len(critical_alerts),
        "status": "CRITICAL" if critical_alerts else ("WARNING" if patient_alerts else "STABLE"),
    }
