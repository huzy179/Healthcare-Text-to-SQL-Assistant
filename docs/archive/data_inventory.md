# Data Inventory

This document records what is actually present in the local CSV dataset.

Important note: the repository contains healthcare CSV files under `data/synthea_csv`, but it does not contain the data generation tool or scripts. The exact external source of the dataset should be confirmed separately before writing final project/portfolio claims.

## File Summary

Line counts include the CSV header row.

| File | Lines | Data rows | MVP priority | Notes |
|---|---:|---:|---|---|
| `patients.csv` | 11,380 | 11,379 | High | Patient demographics and profile fields. |
| `encounters.csv` | 656,916 | 656,915 | High | Visit/encounter records; central join table. |
| `conditions.csv` | 406,116 | 406,115 | High | Diagnoses/conditions. |
| `medications.csv` | 545,440 | 545,439 | High | Medication records and costs. |
| `observations.csv` | 8,430,611 | 8,430,610 | High | Lab/vital observations; large table. |
| `procedures.csv` | 1,811,161 | 1,811,160 | High | Procedures and treatment actions. |
| `claims.csv` | 1,202,355 | 1,202,354 | Medium | Billing/claim status fields. |
| `providers.csv` | 1,141 | 1,140 | Medium | Provider metadata. |
| `organizations.csv` | 1,141 | 1,140 | Medium | Organization metadata. |
| `payers.csv` | 11 | 10 | Medium | Payer/insurance metadata. |
| `payer_transitions.csv` | 420,127 | 420,126 | Later | Patient payer history. |
| `immunizations.csv` | 164,780 | 164,779 | Later | Immunization events. |
| `allergies.csv` | 10,923 | 10,922 | Later | Allergy records. |
| `careplans.csv` | 37,161 | 37,160 | Later | Care plan records. |
| `devices.csv` | 64,743 | 64,742 | Later | Device records. |
| `imaging_studies.csv` | 905,752 | 905,751 | Later | Imaging metadata; relatively large. |
| `supplies.csv` | 297,156 | 297,155 | Later | Supply usage records. |
| `claims_transactions.csv` | 10,609,215 | 10,609,214 | Later | Very large claim transaction detail table. |

## Recommended MVP Tables

Use these first:

- `patients`
- `encounters`
- `conditions`
- `medications`
- `observations`
- `procedures`
- `claims`
- `providers`
- `organizations`
- `payers`

Leave these for later:

- `claims_transactions`
- `imaging_studies`
- `payer_transitions`
- `immunizations`
- `allergies`
- `careplans`
- `devices`
- `supplies`

Reason: the MVP should prove the full Text-to-SQL flow with manageable schema complexity before adding very large or more specialized tables.

## Main Join Keys

Likely relationships based on CSV headers:

| From table.column | To table.column | Purpose |
|---|---|---|
| `encounters.PATIENT` | `patients.Id` | Encounter belongs to a patient. |
| `encounters.ORGANIZATION` | `organizations.Id` | Encounter happened at an organization. |
| `encounters.PROVIDER` | `providers.Id` | Encounter handled by a provider. |
| `encounters.PAYER` | `payers.Id` | Encounter associated with a payer. |
| `conditions.PATIENT` | `patients.Id` | Condition belongs to a patient. |
| `conditions.ENCOUNTER` | `encounters.Id` | Condition recorded during an encounter. |
| `medications.PATIENT` | `patients.Id` | Medication belongs to a patient. |
| `medications.ENCOUNTER` | `encounters.Id` | Medication recorded during an encounter. |
| `medications.PAYER` | `payers.Id` | Medication associated with a payer. |
| `observations.PATIENT` | `patients.Id` | Observation belongs to a patient. |
| `observations.ENCOUNTER` | `encounters.Id` | Observation recorded during an encounter. |
| `procedures.PATIENT` | `patients.Id` | Procedure belongs to a patient. |
| `procedures.ENCOUNTER` | `encounters.Id` | Procedure performed during an encounter. |
| `claims.PATIENTID` | `patients.Id` | Claim belongs to a patient. |
| `claims.PROVIDERID` | `providers.Id` | Claim associated with a provider. |
| `providers.ORGANIZATION` | `organizations.Id` | Provider belongs to an organization. |

These should be verified with sample joins after importing data into PostgreSQL.

## Early Risks

- Some CSV columns use uppercase names, while PostgreSQL schema should use lowercase names for easier SQL generation.
- `observations.csv` and `claims_transactions.csv` are large, so import/index time can be significant.
- `observations.VALUE` is text because the same column can contain numeric and non-numeric values.
- The exact dataset source is not proven by repo contents alone.
