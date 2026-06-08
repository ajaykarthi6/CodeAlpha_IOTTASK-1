# 🔐 IoMT Security & Privacy Guidelines

## The Threat Landscape

IoMT devices present unique cybersecurity challenges because:
1. **Consequences of compromise are physical** — a hacked insulin pump or pacemaker can kill
2. **Devices are resource-constrained** — limited CPU/RAM for security protocols
3. **Long deployment lifecycles** — a pacemaker implanted today may be in-vivo for 10 years
4. **Legacy device proliferation** — many hospitals run unpatched medical devices

---

## Known IoMT Attack Vectors

| Attack Type | Vector | Real-World Example |
|-------------|--------|--------------------|
| **Wireless Hijacking** | BLE / RF protocol exploitation | Barnaby Jack (pacemaker) 2012 |
| **Network Intrusion** | Hospital LAN → device pivot | WannaCry NHS attack 2017 |
| **Firmware Tampering** | Unsigned firmware updates | Multiple vendor advisories |
| **Data Interception** | Unencrypted data transmission | Various CGM implementations |
| **Denial of Service** | Flooding device with packets | Insulin pump DoS (Medtronic) |
| **Replay Attacks** | Capturing and replaying commands | Implantable device commands |

---

## Security Architecture Requirements

### 1. Device-Level Security
```
✅ Secure Boot         — Verify firmware signature before execution
✅ Hardware RoT        — Hardware Root of Trust (TPM chip or equivalent)
✅ Unique Device IDs   — Cryptographic device identity per unit
✅ Tamper Detection    — Physical tamper-evident enclosures
✅ Minimal Attack Surface — Disable all unused interfaces (USB, JTAG in production)
```

### 2. Communication Security
```
✅ TLS 1.3             — All network communications
✅ AES-128 minimum     — Data at rest encryption
✅ Certificate Pinning — Prevent MITM attacks on device-cloud channel
✅ Mutual TLS (mTLS)   — Both device and server authenticate each other
✅ Short Session Keys  — Frequent key rotation
```

### 3. Network Architecture
```
                   ┌─────────────────────────────────┐
   IoMT Devices ───┤   DEVICE VLAN (isolated)        │
                   │   Firewall + IDS/IPS             │
                   └──────────────┬──────────────────┘
                                  │ Controlled ports only
                   ┌──────────────▼──────────────────┐
                   │   CLINICAL NETWORK               │
                   │   Zero-Trust Policy Enforcement  │
                   └──────────────┬──────────────────┘
                                  │ MFA + RBAC
                   ┌──────────────▼──────────────────┐
                   │   INTERNET / CLOUD               │
                   └─────────────────────────────────┘
```

### 4. Zero-Trust Principles
- **Never trust, always verify** — no implicit trust based on network location
- **Least-privilege access** — each device accesses only its own data
- **Microsegmentation** — isolate device types into separate network segments
- **Continuous verification** — re-authenticate sessions, not just at login

---

## HIPAA Compliance Checklist

### Administrative Safeguards
- [ ] Designate a HIPAA Security Officer
- [ ] Conduct annual security risk assessments
- [ ] Implement workforce security training
- [ ] Establish incident response procedures

### Physical Safeguards
- [ ] Workstation access controls
- [ ] Device and media controls (encryption at rest)
- [ ] Secure disposal procedures for replaced devices

### Technical Safeguards
- [ ] Access control with unique user identification
- [ ] Automatic logoff after inactivity
- [ ] Audit controls (log all PHI access)
- [ ] Integrity controls (detect unauthorized alteration)
- [ ] Transmission security (encryption in transit)

---

## GDPR Considerations (EU Patients)

| Requirement | IoMT Implementation |
|-------------|-------------------|
| **Lawful Basis** | Explicit consent + vital interests |
| **Data Minimization** | Collect only clinically necessary parameters |
| **Right to Erasure** | Patient can request device data deletion |
| **Data Portability** | Export in HL7 FHIR format |
| **Privacy by Design** | Security baked into device architecture |
| **Breach Notification** | 72-hour notification to supervisory authority |

---

## FDA Cybersecurity Guidance (2023)

The FDA's 2023 cybersecurity guidance requires:
1. **Software Bill of Materials (SBOM)** — list all software components
2. **Coordinated Vulnerability Disclosure** — public disclosure policy
3. **Cybersecurity Management Plan** — monitoring and patching post-market
4. **Design controls** — cybersecurity built into device development process

---

## Incident Response for Medical Devices

```
Detection → Containment → Eradication → Recovery → Lessons Learned
    │              │              │            │
 IDS Alert    Isolate        Patch/        Restore      Update
 or report    device VLAN    Replace       service    threat model
```

**Critical rule:** During a cybersecurity incident involving life-critical devices,
PATIENT SAFETY takes priority over data preservation. Disconnect/replace a
compromised insulin pump or pacemaker controller immediately.
