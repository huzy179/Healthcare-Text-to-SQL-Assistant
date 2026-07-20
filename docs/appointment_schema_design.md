# Appointment Management Schema Design

The MVP schema is based on Synthea healthcare CSV files and models a simplified appointment/encounter management system.

## Core Concept Mapping

| Appointment system concept | PostgreSQL table | Notes |
|---|---|---|
| Patient profile | `patients` | Demographics and patient identifiers. |
| Appointment or visit | `encounters` | Visit time, patient, organization, provider, payer, encounter class, cost. |
| Diagnosis after visit | `conditions` | Linked to patient and encounter. |
| Medication order | `medications` | Linked to patient, encounter, payer, and reason. |
| Procedure | `procedures` | Linked to patient and encounter. |
| Lab/vital result | `observations` | Linked to patient; encounter is sometimes missing in Synthea. |
| Provider | `providers` | Clinician metadata and organization. |
| Facility | `organizations` | Hospital or clinic metadata. |
| Payer/insurance | `payers` | Insurance/payment metadata. |
| Billing claim | `claims` | Claim status and outstanding amounts. |

## Main Join Keys

```text
encounters.patient -> patients.id
encounters.provider -> providers.id
encounters.organization -> organizations.id
encounters.payer -> payers.id

conditions.patient -> patients.id
conditions.encounter -> encounters.id

medications.patient -> patients.id
medications.encounter -> encounters.id
medications.payer -> payers.id

procedures.patient -> patients.id
procedures.encounter -> encounters.id

observations.patient -> patients.id
observations.encounter -> encounters.id

providers.organization -> organizations.id
```

## Notes For Text-to-SQL

- Use `encounters` for appointment volume, visit type, visit date, provider, organization, payer, and claim cost analytics.
- Use `conditions`, `medications`, `procedures`, and `observations` for clinical details connected to a visit.
- Prefer joining observations through `patient` unless the question explicitly requires encounter context, because some observation rows do not have a matching encounter.
- Use `COUNT(DISTINCT patient)` when the question asks for number of patients with a diagnosis or event.
