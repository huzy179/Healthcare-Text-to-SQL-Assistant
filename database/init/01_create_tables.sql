CREATE TABLE IF NOT EXISTS patients (
  id TEXT PRIMARY KEY,
  birthdate DATE,
  deathdate DATE,
  ssn TEXT,
  drivers TEXT,
  passport TEXT,
  prefix TEXT,
  first_name TEXT,
  middle_name TEXT,
  last_name TEXT,
  suffix TEXT,
  maiden TEXT,
  marital TEXT,
  race TEXT,
  ethnicity TEXT,
  gender TEXT,
  birthplace TEXT,
  address TEXT,
  city TEXT,
  state TEXT,
  county TEXT,
  fips TEXT,
  zip TEXT,
  lat NUMERIC,
  lon NUMERIC,
  healthcare_expenses NUMERIC,
  healthcare_coverage NUMERIC,
  income NUMERIC
);

CREATE TABLE IF NOT EXISTS encounters (
  id TEXT PRIMARY KEY,
  start TIMESTAMPTZ,
  stop TIMESTAMPTZ,
  patient TEXT,
  organization TEXT,
  provider TEXT,
  payer TEXT,
  encounterclass TEXT,
  code TEXT,
  description TEXT,
  base_encounter_cost NUMERIC,
  total_claim_cost NUMERIC,
  payer_coverage NUMERIC,
  reasoncode TEXT,
  reasondescription TEXT
);

CREATE TABLE IF NOT EXISTS conditions (
  start DATE,
  stop DATE,
  patient TEXT,
  encounter TEXT,
  system TEXT,
  code TEXT,
  description TEXT
);

CREATE TABLE IF NOT EXISTS medications (
  start TIMESTAMPTZ,
  stop TIMESTAMPTZ,
  patient TEXT,
  payer TEXT,
  encounter TEXT,
  code TEXT,
  description TEXT,
  base_cost NUMERIC,
  payer_coverage NUMERIC,
  dispenses INTEGER,
  totalcost NUMERIC,
  reasoncode TEXT,
  reasondescription TEXT
);

CREATE TABLE IF NOT EXISTS observations (
  date TIMESTAMPTZ,
  patient TEXT,
  encounter TEXT,
  category TEXT,
  code TEXT,
  description TEXT,
  value TEXT,
  units TEXT,
  type TEXT
);

CREATE TABLE IF NOT EXISTS procedures (
  start DATE,
  stop DATE,
  patient TEXT,
  encounter TEXT,
  system TEXT,
  code TEXT,
  description TEXT,
  base_cost NUMERIC,
  reasoncode TEXT,
  reasondescription TEXT
);

CREATE TABLE IF NOT EXISTS claims (
  id TEXT PRIMARY KEY,
  patientid TEXT,
  providerid TEXT,
  primarypatientinsuranceid TEXT,
  secondarypatientinsuranceid TEXT,
  departmentid TEXT,
  patientdepartmentid TEXT,
  diagnosis1 TEXT,
  diagnosis2 TEXT,
  diagnosis3 TEXT,
  diagnosis4 TEXT,
  diagnosis5 TEXT,
  diagnosis6 TEXT,
  diagnosis7 TEXT,
  diagnosis8 TEXT,
  referringproviderid TEXT,
  appointmentid TEXT,
  currentillnessdate DATE,
  servicedate DATE,
  supervisingproviderid TEXT,
  status1 TEXT,
  status2 TEXT,
  statusp TEXT,
  outstanding1 NUMERIC,
  outstanding2 NUMERIC,
  outstandingp NUMERIC,
  lastbilleddate1 DATE,
  lastbilleddate2 DATE,
  lastbilleddatep DATE,
  healthcareclaimtypeid1 TEXT,
  healthcareclaimtypeid2 TEXT
);

CREATE TABLE IF NOT EXISTS providers (
  id TEXT PRIMARY KEY,
  organization TEXT,
  name TEXT,
  gender TEXT,
  speciality TEXT,
  address TEXT,
  city TEXT,
  state TEXT,
  zip TEXT,
  lat NUMERIC,
  lon NUMERIC,
  encounters INTEGER,
  procedures INTEGER
);

CREATE TABLE IF NOT EXISTS organizations (
  id TEXT PRIMARY KEY,
  name TEXT,
  address TEXT,
  city TEXT,
  state TEXT,
  zip TEXT,
  lat NUMERIC,
  lon NUMERIC,
  phone TEXT,
  revenue NUMERIC,
  utilization INTEGER
);

CREATE TABLE IF NOT EXISTS payers (
  id TEXT PRIMARY KEY,
  name TEXT,
  ownership TEXT,
  address TEXT,
  city TEXT,
  state_headquartered TEXT,
  zip TEXT,
  phone TEXT,
  amount_covered NUMERIC,
  amount_uncovered NUMERIC,
  revenue NUMERIC,
  covered_encounters INTEGER,
  uncovered_encounters INTEGER,
  covered_medications INTEGER,
  uncovered_medications INTEGER,
  covered_procedures INTEGER,
  uncovered_procedures INTEGER,
  covered_immunizations INTEGER,
  uncovered_immunizations INTEGER,
  unique_customers INTEGER,
  qols_avg NUMERIC,
  member_months INTEGER
);
