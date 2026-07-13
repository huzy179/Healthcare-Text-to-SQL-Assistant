CREATE INDEX IF NOT EXISTS idx_encounters_patient ON encounters(patient);
CREATE INDEX IF NOT EXISTS idx_encounters_start ON encounters(start);
CREATE INDEX IF NOT EXISTS idx_encounters_class ON encounters(encounterclass);

CREATE INDEX IF NOT EXISTS idx_conditions_patient ON conditions(patient);
CREATE INDEX IF NOT EXISTS idx_conditions_encounter ON conditions(encounter);
CREATE INDEX IF NOT EXISTS idx_conditions_start ON conditions(start);
CREATE INDEX IF NOT EXISTS idx_conditions_description ON conditions(description);

CREATE INDEX IF NOT EXISTS idx_medications_patient ON medications(patient);
CREATE INDEX IF NOT EXISTS idx_medications_encounter ON medications(encounter);
CREATE INDEX IF NOT EXISTS idx_medications_start ON medications(start);
CREATE INDEX IF NOT EXISTS idx_medications_description ON medications(description);

CREATE INDEX IF NOT EXISTS idx_observations_patient ON observations(patient);
CREATE INDEX IF NOT EXISTS idx_observations_encounter ON observations(encounter);
CREATE INDEX IF NOT EXISTS idx_observations_date ON observations(date);
CREATE INDEX IF NOT EXISTS idx_observations_description ON observations(description);

CREATE INDEX IF NOT EXISTS idx_procedures_patient ON procedures(patient);
CREATE INDEX IF NOT EXISTS idx_procedures_encounter ON procedures(encounter);
CREATE INDEX IF NOT EXISTS idx_procedures_start ON procedures(start);

CREATE INDEX IF NOT EXISTS idx_claims_patientid ON claims(patientid);
CREATE INDEX IF NOT EXISTS idx_claims_providerid ON claims(providerid);
CREATE INDEX IF NOT EXISTS idx_claims_servicedate ON claims(servicedate);
