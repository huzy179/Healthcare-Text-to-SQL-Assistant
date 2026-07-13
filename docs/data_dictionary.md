# Data Dictionary

This dictionary is based on CSV headers currently present in `data/synthea_csv`.

## `patients.csv`

Patient demographic and profile data.

Columns:

```text
Id, BIRTHDATE, DEATHDATE, SSN, DRIVERS, PASSPORT, PREFIX, FIRST, MIDDLE, LAST, SUFFIX, MAIDEN, MARITAL, RACE, ETHNICITY, GENDER, BIRTHPLACE, ADDRESS, CITY, STATE, COUNTY, FIPS, ZIP, LAT, LON, HEALTHCARE_EXPENSES, HEALTHCARE_COVERAGE, INCOME
```

Useful questions:

- Patient count.
- Patient count by gender, race, ethnicity, city, state.
- Age distribution.
- Average healthcare expenses or coverage.

## `encounters.csv`

Patient visits or interactions with the healthcare system.

Columns:

```text
Id, START, STOP, PATIENT, ORGANIZATION, PROVIDER, PAYER, ENCOUNTERCLASS, CODE, DESCRIPTION, BASE_ENCOUNTER_COST, TOTAL_CLAIM_COST, PAYER_COVERAGE, REASONCODE, REASONDESCRIPTION
```

Useful questions:

- Encounter count by year/month.
- Most common encounter classes.
- Average claim cost by encounter class.
- Encounters by organization, provider, payer, or patient.

## `conditions.csv`

Diagnoses or condition records.

Columns:

```text
START, STOP, PATIENT, ENCOUNTER, SYSTEM, CODE, DESCRIPTION
```

Useful questions:

- Top diseases/conditions.
- Patient count for a condition.
- Conditions by year.
- Conditions by gender via join with `patients`.

## `medications.csv`

Medication records and medication costs.

Columns:

```text
START, STOP, PATIENT, PAYER, ENCOUNTER, CODE, DESCRIPTION, BASE_COST, PAYER_COVERAGE, DISPENSES, TOTALCOST, REASONCODE, REASONDESCRIPTION
```

Useful questions:

- Top prescribed medications.
- Medication cost by year.
- Medication usage by condition reason.
- Medication coverage by payer.

## `observations.csv`

Clinical observations, lab values, and vital signs.

Columns:

```text
DATE, PATIENT, ENCOUNTER, CATEGORY, CODE, DESCRIPTION, VALUE, UNITS, TYPE
```

Useful questions:

- Most common observations.
- Average numeric lab/vital values.
- Patient count by abnormal threshold, when values are numeric.
- Observations for patients with a condition.

Important: `VALUE` should initially be treated as text. Numeric analytics need safe casting.

## `procedures.csv`

Procedure or treatment action records.

Columns:

```text
START, STOP, PATIENT, ENCOUNTER, SYSTEM, CODE, DESCRIPTION, BASE_COST, REASONCODE, REASONDESCRIPTION
```

Useful questions:

- Top procedures.
- Procedure count by year.
- Average procedure cost.
- Procedures linked to diagnosis reason.

## `claims.csv`

Claim and billing status records.

Columns:

```text
Id, PATIENTID, PROVIDERID, PRIMARYPATIENTINSURANCEID, SECONDARYPATIENTINSURANCEID, DEPARTMENTID, PATIENTDEPARTMENTID, DIAGNOSIS1, DIAGNOSIS2, DIAGNOSIS3, DIAGNOSIS4, DIAGNOSIS5, DIAGNOSIS6, DIAGNOSIS7, DIAGNOSIS8, REFERRINGPROVIDERID, APPOINTMENTID, CURRENTILLNESSDATE, SERVICEDATE, SUPERVISINGPROVIDERID, STATUS1, STATUS2, STATUSP, OUTSTANDING1, OUTSTANDING2, OUTSTANDINGP, LASTBILLEDDATE1, LASTBILLEDDATE2, LASTBILLEDDATEP, HEALTHCARECLAIMTYPEID1, HEALTHCARECLAIMTYPEID2
```

Useful questions:

- Claim count by service date.
- Outstanding amount by status.
- Claims by provider or patient.

## `providers.csv`

Provider metadata.

Columns:

```text
Id, ORGANIZATION, NAME, GENDER, SPECIALITY, ADDRESS, CITY, STATE, ZIP, LAT, LON, ENCOUNTERS, PROCEDURES
```

Useful questions:

- Provider count by specialty.
- Providers by organization.
- Top providers by encounter/procedure count.

## `organizations.csv`

Healthcare organization metadata.

Columns:

```text
Id, NAME, ADDRESS, CITY, STATE, ZIP, LAT, LON, PHONE, REVENUE, UTILIZATION
```

Useful questions:

- Organization count by state/city.
- Top organizations by revenue or utilization.
- Encounters by organization via join.

## `payers.csv`

Payer or insurance metadata.

Columns:

```text
Id, NAME, OWNERSHIP, ADDRESS, CITY, STATE_HEADQUARTERED, ZIP, PHONE, AMOUNT_COVERED, AMOUNT_UNCOVERED, REVENUE, COVERED_ENCOUNTERS, UNCOVERED_ENCOUNTERS, COVERED_MEDICATIONS, UNCOVERED_MEDICATIONS, COVERED_PROCEDURES, UNCOVERED_PROCEDURES, COVERED_IMMUNIZATIONS, UNCOVERED_IMMUNIZATIONS, UNIQUE_CUSTOMERS, QOLS_AVG, MEMBER_MONTHS
```

Useful questions:

- Payer revenue ranking.
- Covered vs uncovered amounts.
- Covered encounters/medications/procedures by payer.

## Later Tables

These are useful after the MVP is stable:

- `claims_transactions.csv`: detailed claim transaction lines.
- `imaging_studies.csv`: imaging study details.
- `payer_transitions.csv`: payer history per patient.
- `immunizations.csv`: immunization events.
- `allergies.csv`: allergy records.
- `careplans.csv`: care plan records.
- `devices.csv`: device records.
- `supplies.csv`: supply usage.
