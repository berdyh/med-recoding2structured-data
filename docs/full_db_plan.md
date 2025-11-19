# Complete Healthcare Database Schema for GP Consultation Management

## Overview

This schema stores patient health records and GP consultations with full support for:
- Unstructured consultation transcripts (NLP extraction)
- Structured clinical data (symptoms, findings, diagnoses, medications)
- Audit trails and data quality management
- Clinical decision support (differential diagnoses, red flags, follow-ups)
- International coding standards (SNOMED CT, ICD-10, RxNorm, LOINC)

**Key Principle**: Flat columns for frequently queried clinical data + JSON sub-structures for optional context.

---

## 1. Core Patient Management Tables

### PATIENTS Table

**Purpose**: Store patient demographic and contact information

**Relationships**:
- One Patient → Many Consultations
- One Patient → Many Allergies
- One Patient → Many Medical History records

```sql
CREATE TABLE PATIENTS (
  patient_id UUID PRIMARY KEY,
  nhs_number VARCHAR(20) UNIQUE NOT NULL,      -- UK National Health Service number
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  date_of_birth DATE NOT NULL,
  gender VARCHAR(20),                          -- M, F, Other, Prefer not to say
  address TEXT,
  phone_number VARCHAR(20),
  email VARCHAR(150),
  emergency_contact_name VARCHAR(100),
  emergency_contact_phone VARCHAR(20),
  registration_date DATE DEFAULT CURRENT_DATE,
  preferred_language VARCHAR(10) DEFAULT 'en-UK',
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (patient_id),
  INDEX idx_nhs_number (nhs_number),
  INDEX idx_patient_name (last_name, first_name),
  INDEX idx_created_at (created_at DESC)
);
```

**Sample Data**:
```sql
INSERT INTO PATIENTS VALUES (
  'pat-12345-uuid',
  'NHS1234567890',
  'John',
  'Smith',
  '1990-05-15',
  'M',
  '123 Main Street, London, UK',
  '+44-123-456-7890',
  'john.smith@email.com',
  'Jane Smith',
  '+44-123-456-7891',
  '2020-01-10',
  'en-UK',
  TRUE,
  NOW(),
  NOW()
);
```

---

### DOCTORS Table

**Purpose**: Store practitioner information and specialties

**Relationships**:
- One Doctor → Many Appointments
- One Doctor → Many Consultations
- Many Doctors ↔ Many Departments

```sql
CREATE TABLE DOCTORS (
    doctor_id UUID PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    specialty VARCHAR(100),                      -- GP, Cardiologist, etc.
    license_number VARCHAR(50) UNIQUE,
    contact_information VARCHAR(150),
    availability_schedule JSONB,                 -- {"monday": ["09:00-17:00"], ...}
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (doctor_id),
    INDEX idx_specialty (specialty)
);
```

### DOCTOR_DEPARTMENT Table

**Purpose**: Associate doctors with multiple departments

```sql
CREATE TABLE DOCTOR_DEPARTMENT (
    doctor_id UUID NOT NULL,
    department_id UUID NOT NULL,

    PRIMARY KEY (doctor_id, department_id),
    FOREIGN KEY (doctor_id) REFERENCES DOCTORS(doctor_id),
    FOREIGN KEY (department_id) REFERENCES DEPARTMENTS(department_id)
);
```

### DEPARTMENTS Table

**Purpose**: Store practice/hospital department structure

**Relationships**:
- One Department → Many Doctors

```sql
CREATE TABLE DEPARTMENTS (
    department_id UUID PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL,
    department_location VARCHAR(200),
    contact_information VARCHAR(150),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (department_id),
    INDEX idx_department_name (department_name)
);
```

---

## 2. Appointment and Consultation Tables

### APPOINTMENTS Table

**Purpose**: Schedule and track appointments

**Relationships**:
- One Patient → Many Appointments
- One Doctor → Many Appointments
- One Appointment → One Consultation

```sql
CREATE TABLE APPOINTMENTS (
  appointment_id UUID PRIMARY KEY,
  patient_id UUID NOT NULL,
  doctor_id UUID NOT NULL,
  appointment_date DATE NOT NULL,
  appointment_time TIME NOT NULL,
  duration_minutes INT DEFAULT 30,
  appointment_type VARCHAR(50),                -- consultation, follow-up, urgent, routine
  status VARCHAR(20) DEFAULT 'scheduled',      -- scheduled, completed, cancelled, no-show
  reason_for_visit VARCHAR(255),
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (appointment_id),
  FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id),
  FOREIGN KEY (doctor_id) REFERENCES DOCTORS(doctor_id),
  INDEX idx_patient_appointments (patient_id, appointment_date),
  INDEX idx_doctor_appointments (doctor_id, appointment_date),
  INDEX idx_status (status),
  CHECK (status IN ('scheduled', 'completed', 'cancelled', 'no-show'))
);
```

---

### CONSULTATION_SESSIONS Table

**Purpose**: Store full unstructured consultation transcript and session metadata

**Relationships**:
- One Consultation Session → Multiple extracted entities (symptoms, findings, etc.)
- Links to CONSULTATIONS table for structured results

```sql
CREATE TABLE CONSULTATION_SESSIONS (
  consultation_session_id UUID PRIMARY KEY,
  consultation_id UUID,                        -- Links to structured consultation
  patient_id UUID NOT NULL,
  doctor_id UUID NOT NULL,
  appointment_id UUID,                         -- Links to appointment if applicable
  session_start_datetime TIMESTAMP NOT NULL,
  session_end_datetime TIMESTAMP,
  session_duration_minutes INT,
  conversation_format VARCHAR(50),             -- face-to-face, remote, phone, hybrid
  full_transcript TEXT,                        -- UNSTRUCTURED: Complete conversation (sensitive PII)
  transcript_language VARCHAR(10) DEFAULT 'en-UK',
  nlp_processed_flag BOOLEAN DEFAULT FALSE,    -- Has NLP extraction been run?
  nlp_processing_timestamp TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (consultation_session_id),
  FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id),
  FOREIGN KEY (doctor_id) REFERENCES DOCTORS(doctor_id),
  FOREIGN KEY (appointment_id) REFERENCES APPOINTMENTS(appointment_id) ON DELETE SET NULL,
  INDEX idx_patient_sessions (patient_id, session_start_datetime DESC),
  INDEX idx_nlp_processed (nlp_processed_flag),
  CHECK (conversation_format IN ('face-to-face', 'remote', 'phone', 'hybrid'))
);
```

---

### CONSULTATIONS Table

**Purpose**: Record consultation details and structured clinical information

**Relationships**:
- One Consultation Session → One Consultation (structured results)
- One Appointment → One Consultation

```sql
CREATE TABLE CONSULTATIONS (
  consultation_id UUID PRIMARY KEY,
  consultation_session_id UUID NOT NULL,
  appointment_id UUID,
  patient_id UUID NOT NULL,
  doctor_id UUID NOT NULL,
  consultation_date DATE NOT NULL,
  consultation_time TIME NOT NULL,
  chief_complaint_free_text VARCHAR(500),      -- Patient's own words
  consultation_notes TEXT,                     -- Unstructured clinical notes
  provisional_status VARCHAR(50),              -- awaiting_filing, filed (for external consultations)
  nlp_processed_flag BOOLEAN DEFAULT FALSE,
  nlp_processing_timestamp TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (consultation_id),
  FOREIGN KEY (consultation_session_id) REFERENCES CONSULTATION_SESSIONS(consultation_session_id),
  FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id),
  FOREIGN KEY (doctor_id) REFERENCES DOCTORS(doctor_id),
  FOREIGN KEY (appointment_id) REFERENCES APPOINTMENTS(appointment_id) ON DELETE SET NULL,
  INDEX idx_consultation_date (consultation_date DESC),
  INDEX idx_patient_consultations (patient_id, consultation_date DESC),
  CHECK (provisional_status IN ('awaiting_filing', 'filed', NULL))
);
```

---

## 3. Clinical Data Tables - Symptoms and Findings

### SYMPTOMS Table

**Purpose**: Store individual symptoms reported by patient during consultation

**Structure**: 
- FLAT columns for frequently queried attributes (indexed)
- JSON sub-structure for optional contextual properties

**Relationships**:
- Many Symptoms → One Consultation Session
- One Symptom → Optional Related Finding

```sql
CREATE TABLE SYMPTOMS (
  symptom_id UUID PRIMARY KEY,
  consultation_session_id UUID NOT NULL,
  patient_id UUID NOT NULL,

  -- FLAT COLUMNS (Core clinical data)
  symptom_name VARCHAR(100) NOT NULL,          -- "sore throat", "fever", "fatigue"
  symptom_code VARCHAR(20) NOT NULL,           -- SNOMED CT code: 405737000
  symptom_code_system VARCHAR(20) DEFAULT 'SNOMED-CT',
  symptom_presence VARCHAR(20) NOT NULL,       -- present, absent, unknown
  symptom_negation_flag BOOLEAN DEFAULT FALSE, -- TRUE if patient said "NOT present" (e.g., "no cough")
  onset_date DATE,                             -- When symptom started
  duration_days INT,                           -- How long lasted
  severity VARCHAR(20),                        -- mild, moderate, severe, critical
  temporal_pattern VARCHAR(50),                -- progressive, constant, intermittent, improving, worsening
  confidence_score DECIMAL(3,2),               -- NLP extraction confidence 0.00-1.00
  patient_reported BOOLEAN DEFAULT TRUE,       -- TRUE=patient reported, FALSE=clinician observed

  -- JSON SUB-STRUCTURE (Flexible context)
  clinical_modifiers JSONB,                    -- {
                                               --   "location": "pharynx",
                                               --   "bilateral": false,
                                               --   "radiates_to_ear": true,
                                               --   "aggravating": ["swallowing", "eating"],
                                               --   "alleviating": ["rest", "paracetamol"],
                                               --   "sleep_affected": true,
                                               --   "impacts_appetite": "severe"
                                               -- }

  -- Link to findings
  related_finding_id UUID,                     -- If symptom generates measurable finding

  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (symptom_id),
  FOREIGN KEY (consultation_session_id) REFERENCES CONSULTATION_SESSIONS(consultation_session_id),
  FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id),
  FOREIGN KEY (related_finding_id) REFERENCES ASSOCIATED_FINDINGS(finding_id) ON DELETE SET NULL,
  INDEX idx_consultation_symptom (consultation_session_id, symptom_code),
  INDEX idx_severity (severity),
  INDEX idx_duration (duration_days),
  INDEX idx_patient_symptoms (patient_id, created_at DESC),
  CHECK (symptom_presence IN ('present', 'absent', 'unknown')),
  CHECK (severity IN ('mild', 'moderate', 'severe', 'critical')),
  CHECK (confidence_score >= 0 AND confidence_score <= 1)
);
```

**Sample Data**:
```sql
INSERT INTO SYMPTOMS VALUES (
  'sym-001-uuid',
  'cons-session-001',
  'pat-12345',
  'sore throat',
  '405737000',
  'SNOMED-CT',
  'present',
  FALSE,
  '2025-11-13',
  2,
  'severe',
  'progressive',
  0.98,
  TRUE,
  '{
    "location": "pharynx",
    "bilateral": false,
    "radiates_to_ear": true,
    "aggravating": ["swallowing", "eating", "hot drinks"],
    "alleviating": ["lozenges", "rest", "ice cream"],
    "sleep_affected": true,
    "impacts_appetite": "severe"
  }',
  'find-001-uuid',
  NOW(),
  NOW()
);
```

---

### ASSOCIATED_FINDINGS Table

**Purpose**: Store objective clinical findings (not just vital signs)

**Note**: DIFFERENT from SYMPTOMS (patient reports) and VITAL_SIGNS (measurements)

**Relationships**:
- One Finding → Multiple linked Symptoms

```sql
CREATE TABLE ASSOCIATED_FINDINGS (
  finding_id UUID PRIMARY KEY,
  consultation_session_id UUID NOT NULL,
  patient_id UUID NOT NULL,

  -- FLAT COLUMNS
  finding_name VARCHAR(100) NOT NULL,          -- "fever", "swollen glands", "white patches on tonsils"
  finding_code VARCHAR(20) NOT NULL,           -- SNOMED CT code
  finding_code_system VARCHAR(20) DEFAULT 'SNOMED-CT',
  finding_type VARCHAR(50),                    -- objective, subjective, reported
  finding_present BOOLEAN NOT NULL,            -- TRUE/FALSE
  finding_value DECIMAL(10,2),                 -- 39.0 (for temperature)
  finding_unit VARCHAR(20),                    -- °C, mmHg, mg/dL, etc.
  reference_range VARCHAR(50),                 -- "36.5-37.5°C"
  finding_severity VARCHAR(20),                -- mild, moderate, severe
  anatomical_location VARCHAR(50),             -- SNOMED body structure code
  clinical_significance VARCHAR(20),           -- normal, abnormal, critical

  -- JSON (Clinical interpretation)
  interpretation_details JSONB,                -- {
                                               --   "is_significant": true,
                                               --   "clinical_implication": "suggests_infection",
                                               --   "trend": "worsening"
                                               -- }

  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (finding_id),
  FOREIGN KEY (consultation_session_id) REFERENCES CONSULTATION_SESSIONS(consultation_session_id),
  FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id),
  INDEX idx_consultation_findings (consultation_session_id, finding_code),
  INDEX idx_finding_severity (finding_severity),
  INDEX idx_patient_findings (patient_id, created_at DESC),
  CHECK (finding_type IN ('objective', 'subjective', 'reported')),
  CHECK (clinical_significance IN ('normal', 'abnormal', 'critical'))
);
```

---

### PHYSICAL_EXAMINATION_FINDINGS Table

**Purpose**: Store results of physical examinations

**Relationships**:
- One Consultation → Multiple Physical Examinations

```sql
CREATE TABLE PHYSICAL_EXAMINATION_FINDINGS (
  examination_id UUID PRIMARY KEY,
  consultation_session_id UUID NOT NULL,
  patient_id UUID NOT NULL,
  doctor_id UUID NOT NULL,

  -- FLAT COLUMNS
  examination_type VARCHAR(100) NOT NULL,      -- "oropharyngeal_exam", "abdominal_exam"
  examination_type_code VARCHAR(20),           -- SNOMED CT procedure code: 117220006
  examination_performed BOOLEAN DEFAULT TRUE,
  anatomical_site VARCHAR(100),                -- "pharynx", "tonsils", "neck"
  anatomical_site_code VARCHAR(20),            -- SNOMED body structure code
  finding_normal BOOLEAN,                      -- TRUE/FALSE
  finding_description VARCHAR(500),            -- "Tonsils enlarged with exudate"
  severity VARCHAR(20),                        -- normal, mild, moderate, severe

  -- JSON (Detailed findings)
  examination_details JSONB,                   -- {
                                               --   "tonsil_size": 3,  (1-4 scale)
                                               --   "exudate_type": "whitish",
                                               --   "exudate_coverage": "bilateral",
                                               --   "pharyngeal_erythema": true,
                                               --   "uvula_position": "midline",
                                               --   "petechiae": false
                                               -- }

  clinician_interpretation JSONB,              -- {
                                               --   "significant": true,
                                               --   "supports_diagnosis": "bacterial_tonsillitis",
                                               --   "concerning_features": []
                                               -- }

  examination_timestamp TIMESTAMP,

  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (examination_id),
  FOREIGN KEY (consultation_session_id) REFERENCES CONSULTATION_SESSIONS(consultation_session_id),
  FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id),
  FOREIGN KEY (doctor_id) REFERENCES DOCTORS(doctor_id),
  INDEX idx_consultation_exams (consultation_session_id, examination_type),
  INDEX idx_patient_exams (patient_id, examination_timestamp DESC),
  CHECK (severity IN ('normal', 'mild', 'moderate', 'severe'))
);
```

---

### REVIEW_OF_SYSTEMS Table

**Purpose**: Systematic assessment of body systems (what was checked, what wasn't)

**Relationships**:
- One Consultation → One Review of Systems (aggregated)

```sql
CREATE TABLE REVIEW_OF_SYSTEMS (
  ros_id UUID PRIMARY KEY,
  consultation_session_id UUID NOT NULL,
  patient_id UUID NOT NULL,

  ros_system VARCHAR(100) NOT NULL,            -- ENT, Respiratory, Cardiovascular, GI, etc.
  ros_system_code VARCHAR(20),                 -- SNOMED hierarchy code
  system_positive_findings TEXT,               -- JSON array: abnormal findings detected
  system_negative_findings TEXT,               -- JSON array: normal findings (absence of symptoms)
  system_not_reviewed BOOLEAN,                 -- TRUE if system not assessed
  notes TEXT,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (ros_id),
  FOREIGN KEY (consultation_session_id) REFERENCES CONSULTATION_SESSIONS(consultation_session_id),
  FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id),
  INDEX idx_consultation_ros (consultation_session_id, ros_system),
  UNIQUE (consultation_session_id, ros_system)
);
```

---

## 4. Vital Signs and Laboratory Results

### VITAL_SIGNS Table

**Purpose**: Store clinical measurements during consultation

**Relationships**:
- One Consultation → Multiple Vital Signs (at different times)

```sql
CREATE TABLE VITAL_SIGNS (
  vital_sign_id UUID PRIMARY KEY,
  consultation_session_id UUID NOT NULL,
  patient_id UUID NOT NULL,

  measurement_timestamp TIMESTAMP NOT NULL,
  blood_pressure_systolic INT,                 -- mmHg
  blood_pressure_diastolic INT,                -- mmHg
  heart_rate INT,                              -- bpm
  respiratory_rate INT,                        -- breaths per minute
  temperature DECIMAL(5,2),                    -- °C
  oxygen_saturation INT,                       -- %
  weight DECIMAL(6,2),                         -- kg
  height DECIMAL(5,2),                         -- cm
  bmi DECIMAL(5,2),                            -- calculated or entered
  recorded_by UUID,                            -- Which staff member

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (vital_sign_id),
  FOREIGN KEY (consultation_session_id) REFERENCES CONSULTATION_SESSIONS(consultation_session_id),
  FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id),
  INDEX idx_consultation_vitals (consultation_session_id, measurement_timestamp DESC),
  INDEX idx_patient_vitals (patient_id, measurement_timestamp DESC)
);
```

---

### LABORATORY_RESULTS Table

**Purpose**: Store test results with interpretations

**Relationships**:
- One Consultation → Multiple Lab Results

```sql
CREATE TABLE LABORATORY_RESULTS (
  lab_result_id UUID PRIMARY KEY,
  consultation_session_id UUID NOT NULL,
  patient_id UUID NOT NULL,

  test_code VARCHAR(50) NOT NULL,              -- LOINC code
  test_name VARCHAR(200) NOT NULL,
  test_date DATE NOT NULL,
  result_value VARCHAR(100),                   -- Can be text or numeric
  unit_of_measurement VARCHAR(50),
  reference_range VARCHAR(100),
  abnormal_flag VARCHAR(20),                   -- normal, high, low, critical
  interpretation TEXT,                        -- Clinical interpretation
  ordering_doctor_id UUID,
  lab_facility VARCHAR(200),

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (lab_result_id),
  FOREIGN KEY (consultation_session_id) REFERENCES CONSULTATION_SESSIONS(consultation_session_id),
  FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id),
  FOREIGN KEY (ordering_doctor_id) REFERENCES DOCTORS(doctor_id) ON DELETE SET NULL,
  INDEX idx_consultation_labs (consultation_session_id, test_date DESC),
  INDEX idx_patient_labs (patient_id, test_date DESC),
  CHECK (abnormal_flag IN ('normal', 'high', 'low', 'critical'))
);
```

---

## 5. Diagnostic Assessment Tables

### CLINICAL_ASSESSMENT_EXTRACTED Table

**Purpose**: Store doctor's diagnostic assessment with reasoning

**Relationships**:
- One Consultation → One Clinical Assessment (primary diagnosis)
- One Assessment → Multiple Differential Diagnoses

```sql
CREATE TABLE CLINICAL_ASSESSMENT_EXTRACTED (
  assessment_id UUID PRIMARY KEY,
  consultation_session_id UUID NOT NULL,
  patient_id UUID NOT NULL,
  doctor_id UUID NOT NULL,

  assessment_type VARCHAR(50),                 -- working_diagnosis, differential_diagnosis
  assessment_diagnosis VARCHAR(200) NOT NULL, -- Free text: "bacterial tonsillitis"
  assessment_diagnosis_code VARCHAR(20),       -- ICD-10: J03.90
  assessment_diagnosis_code_icd10 VARCHAR(10), -- ICD-10 code
  assessment_diagnosis_code_snomed VARCHAR(20), -- SNOMED CT: 21300005
  assessment_diagnosis_code_system VARCHAR(50),
  diagnostic_certainty VARCHAR(50) NOT NULL,  -- confirmed, probable, suspected, ruled_out
  diagnostic_likelihood_percentage INT,       -- 0-100
  diagnostic_reasoning TEXT,                  -- WHY doctor thinks this
  key_clinical_features_supporting TEXT,      -- Comma-separated or JSON array
  differential_diagnoses TEXT,                -- Alternatives considered

  -- JSON for detailed assessment
  assessment_details JSONB,                   -- {
                                              --   "criteria_met": ["exudate", "enlarged tonsils", "fever"],
                                              --   "red_flags": ["difficulty swallowing saliva"],
                                              --   "follow_up_needed": true
                                              -- }

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (assessment_id),
  FOREIGN KEY (consultation_session_id) REFERENCES CONSULTATION_SESSIONS(consultation_session_id),
  FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id),
  FOREIGN KEY (doctor_id) REFERENCES DOCTORS(doctor_id),
  INDEX idx_consultation_assessment (consultation_session_id),
  INDEX idx_diagnosis_code (assessment_diagnosis_code_icd10),
  CHECK (diagnostic_certainty IN ('confirmed', 'probable', 'suspected', 'ruled_out'))
);
```

---

### DIFFERENTIAL_DIAGNOSES Table

**Purpose**: Track alternative diagnoses considered

**Relationships**:
- One Assessment → Multiple Differential Diagnoses

```sql
CREATE TABLE DIFFERENTIAL_DIAGNOSES (
  differential_id UUID PRIMARY KEY,
  assessment_id UUID NOT NULL,
  consultation_session_id UUID NOT NULL,

  diagnosis_code VARCHAR(20),
  diagnosis_name VARCHAR(200),
  diagnosis_code_icd10 VARCHAR(10),
  diagnosis_code_snomed VARCHAR(20),
  diagnosis_likelihood VARCHAR(20),            -- high, moderate, low
  reason_included TEXT,                        -- Why considered
  reason_ruled_out TEXT,                       -- Why not selected

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (differential_id),
  FOREIGN KEY (assessment_id) REFERENCES CLINICAL_ASSESSMENT_EXTRACTED(assessment_id),
  FOREIGN KEY (consultation_session_id) REFERENCES CONSULTATION_SESSIONS(consultation_session_id),
  INDEX idx_assessment_differentials (assessment_id),
  CHECK (diagnosis_likelihood IN ('high', 'moderate', 'low'))
);
```

---

## 6. Treatment and Management Tables

### MEDICATIONS Table

**Purpose**: Store prescribed medications with complete dosage and frequency information

**Relationships**:
- One Consultation → Multiple Medications

```sql
CREATE TABLE MEDICATIONS (
  prescription_id UUID PRIMARY KEY,
  consultation_session_id UUID NOT NULL,
  patient_id UUID NOT NULL,
  doctor_id UUID NOT NULL,

  -- FLAT COLUMNS (structured prescription)
  medication_name VARCHAR(200) NOT NULL,      -- "Penicillin V"
  medication_code VARCHAR(50),                -- RxNorm code: 7980
  medication_code_snomed VARCHAR(20),         -- SNOMED CT code
  medication_code_system VARCHAR(50),         -- RxNorm, dm+d (UK)
  dosage_value INT,                           -- 400
  dosage_unit VARCHAR(20),                    -- mg, ml, units
  frequency VARCHAR(50),                      -- "4 times daily"
  frequency_code VARCHAR(20),                 -- SNOMED frequency code: 307439001
  duration_value INT,                         -- 10
  duration_unit VARCHAR(20),                  -- days, weeks, months
  route_of_administration VARCHAR(50),        -- oral, IV, topical, intramuscular
  route_code VARCHAR(20),                     -- SNOMED code
  indication VARCHAR(200),                    -- Reason prescribed
  indication_code VARCHAR(20),                -- ICD-10/SNOMED of indication
  special_instructions VARCHAR(500),          -- "with food", "avoid dairy"
  prescription_status VARCHAR(50) DEFAULT 'active', -- active, completed, discontinued, suspended
  start_date DATE,
  end_date DATE,
  refills INT DEFAULT 0,

  -- JSON (Optional details)
  medication_details JSONB,                   -- {
                                              --   "contraindications": ["penicillin allergy check"],
                                              --   "interactions": ["avoid ibuprofen"],
                                              --   "monitoring": ["watch for rash"]
                                              -- }

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (prescription_id),
  FOREIGN KEY (consultation_session_id) REFERENCES CONSULTATION_SESSIONS(consultation_session_id),
  FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id),
  FOREIGN KEY (doctor_id) REFERENCES DOCTORS(doctor_id),
  INDEX idx_patient_medications (patient_id, status),
  INDEX idx_medication_code (medication_code),
  CHECK (prescription_status IN ('active', 'completed', 'discontinued', 'suspended')),
  CHECK (dosage_value > 0),
  CHECK (duration_value > 0)
);
```

---

## 7. Safety and Follow-up Tables

### RED_FLAGS_AND_WARNINGS Table

**Purpose**: Store critical warning signs discussed

**Relationships**:
- One Consultation → Multiple Red Flags

```sql
CREATE TABLE RED_FLAGS_AND_WARNINGS (
  warning_id UUID PRIMARY KEY,
  consultation_session_id UUID NOT NULL,
  patient_id UUID NOT NULL,

  warning_type VARCHAR(50),                   -- danger_sign, red_flag, follow_up_indicator
  warning_description TEXT NOT NULL,          -- "difficulty swallowing", "trouble breathing"
  warning_code VARCHAR(20),                   -- Clinical code for this warning
  severity VARCHAR(20),                       -- high, moderate, low
  action_required BOOLEAN DEFAULT TRUE,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (warning_id),
  FOREIGN KEY (consultation_session_id) REFERENCES CONSULTATION_SESSIONS(consultation_session_id),
  FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id),
  INDEX idx_patient_warnings (patient_id),
  INDEX idx_severity (severity),
  CHECK (warning_type IN ('danger_sign', 'red_flag', 'follow_up_indicator')),
  CHECK (severity IN ('high', 'moderate', 'low'))
);
```

---

### FOLLOW_UP_PLAN_EXTRACTED Table

**Purpose**: Store structured follow-up instructions

**Relationships**:
- One Consultation → Multiple Follow-up Plans

```sql
CREATE TABLE FOLLOW_UP_PLAN_EXTRACTED (
  follow_up_id UUID PRIMARY KEY,
  consultation_session_id UUID NOT NULL,
  patient_id UUID NOT NULL,
  doctor_id UUID NOT NULL,

  follow_up_type VARCHAR(50),                 -- symptom_monitoring, medication_review, lab_tests, urgent_care, imaging
  follow_up_timing VARCHAR(100),              -- "48 hours", "1 week", "2 weeks"
  follow_up_condition VARCHAR(255),           -- "if symptoms don't improve", "if fever persists"
  follow_up_action VARCHAR(255),              -- "return to GP", "seek urgent care", "attend hospital"
  follow_up_priority VARCHAR(20),             -- routine, urgent, emergent
  scheduled_date DATE,                        -- Optional: when follow-up is scheduled

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (follow_up_id),
  FOREIGN KEY (consultation_session_id) REFERENCES CONSULTATION_SESSIONS(consultation_session_id),
  FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id),
  FOREIGN KEY (doctor_id) REFERENCES DOCTORS(doctor_id),
  INDEX idx_follow_up_priority (follow_up_priority),
  INDEX idx_patient_followups (patient_id, follow_up_priority),
  CHECK (follow_up_type IN ('symptom_monitoring', 'medication_review', 'lab_tests', 'urgent_care', 'imaging')),
  CHECK (follow_up_priority IN ('routine', 'urgent', 'emergent'))
);
```

---

## 8. Patient Education and Context Tables

### PATIENT_EDUCATION_EXTRACTED Table

**Purpose**: Store advice and instructions given to patient

**Relationships**:
- One Consultation → Multiple Education Items

```sql
CREATE TABLE PATIENT_EDUCATION_EXTRACTED (
  education_id UUID PRIMARY KEY,
  consultation_session_id UUID NOT NULL,
  patient_id UUID NOT NULL,

  education_topic VARCHAR(100),               -- medication_compliance, self_care, warning_signs, dietary, activity
  education_content TEXT,                     -- "Stay hydrated, rest, take medication with food"
  education_structured TEXT,                  -- Normalized version

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (education_id),
  FOREIGN KEY (consultation_session_id) REFERENCES CONSULTATION_SESSIONS(consultation_session_id),
  FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id),
  INDEX idx_consultation_education (consultation_session_id),
  CHECK (education_topic IN ('medication_compliance', 'self_care', 'warning_signs', 'dietary', 'activity'))
);
```

---

### SOCIAL_HISTORY_EXTRACTED Table

**Purpose**: Store recent medications, exposures, lifestyle mentioned

**Relationships**:
- One Consultation → Multiple Social History items

```sql
CREATE TABLE SOCIAL_HISTORY_EXTRACTED (
  social_history_id UUID PRIMARY KEY,
  consultation_session_id UUID NOT NULL,
  patient_id UUID NOT NULL,

  history_type VARCHAR(50),                   -- medication_taken, recent_exposure, lifestyle, allergic_reaction
  history_detail TEXT,                        -- Free text from conversation
  history_structured TEXT,                    -- Normalized detail

  -- Medication-specific fields (if applicable)
  medication_name VARCHAR(100),
  medication_code VARCHAR(50),                -- RxNorm or dm+d
  medication_dose_value INT,
  medication_dose_unit VARCHAR(20),
  medication_frequency VARCHAR(50),
  medication_timing_relative VARCHAR(100),    -- "before consultation", "this morning", "yesterday"
  medication_effect VARCHAR(255),             -- "helped a bit with fever"

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (social_history_id),
  FOREIGN KEY (consultation_session_id) REFERENCES CONSULTATION_SESSIONS(consultation_session_id),
  FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id),
  INDEX idx_consultation_history (consultation_session_id),
  CHECK (history_type IN ('medication_taken', 'recent_exposure', 'lifestyle', 'allergic_reaction'))
);
```

---

## 9. Patient Medical History Tables

### MEDICAL_HISTORY Table

**Purpose**: Store past medical conditions and chronic diseases

**Relationships**:
- One Patient → Many Medical History records

```sql
CREATE TABLE MEDICAL_HISTORY (
  medical_history_id UUID PRIMARY KEY,
  patient_id UUID NOT NULL,

  condition_name VARCHAR(200) NOT NULL,
  condition_code VARCHAR(20),                 -- ICD-10 code
  diagnosis_date DATE,
  status VARCHAR(20),                         -- active, resolved, chronic
  notes TEXT,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (medical_history_id),
  FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id),
  INDEX idx_patient_history (patient_id),
  CHECK (status IN ('active', 'resolved', 'chronic'))
);
```

---

### ALLERGIES Table

**Purpose**: Store patient allergies and reactions

**Relationships**:
- One Patient → Many Allergies

```sql
CREATE TABLE ALLERGIES (
  allergy_id UUID PRIMARY KEY,
  patient_id UUID NOT NULL,

  allergen_name VARCHAR(100) NOT NULL,
  allergen_code VARCHAR(20),                  -- SNOMED CT code
  reaction VARCHAR(255),                      -- "anaphylaxis", "rash", "itching"
  severity VARCHAR(20),                       -- mild, moderate, severe
  status VARCHAR(20) DEFAULT 'active',        -- active, inactive, resolved
  onset_date DATE,
  recorded_date DATE,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (allergy_id),
  FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id),
  INDEX idx_patient_allergies (patient_id),
  CHECK (severity IN ('mild', 'moderate', 'severe')),
  CHECK (status IN ('active', 'inactive', 'resolved'))
);
```

---

### DIAGNOSES Table

**Purpose**: Store diagnosed conditions with full clinical context

**Relationships**:
- One Consultation → Many Diagnoses (primary, secondary, differential)
- One Patient → Many Diagnoses (medical history)

```sql
CREATE TABLE DIAGNOSES (
  diagnosis_id UUID PRIMARY KEY,
  consultation_session_id UUID,
  patient_id UUID NOT NULL,

  diagnosis_name VARCHAR(200) NOT NULL,
  diagnosis_code VARCHAR(20),                 -- ICD-10 code
  diagnosis_code_icd10 VARCHAR(10),
  diagnosis_code_snomed VARCHAR(20),          -- SNOMED CT code
  diagnosis_code_system VARCHAR(50),
  diagnosis_type VARCHAR(50),                 -- primary, secondary, differential
  status VARCHAR(20),                         -- active, resolved, chronic
  certainty VARCHAR(50),                      -- confirmed, probable, suspected
  onset_date DATE,
  resolution_date DATE,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (diagnosis_id),
  FOREIGN KEY (consultation_session_id) REFERENCES CONSULTATION_SESSIONS(consultation_session_id) ON DELETE SET NULL,
  FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id),
  INDEX idx_patient_diagnoses (patient_id, status),
  INDEX idx_consultation_diagnoses (consultation_session_id),
  INDEX idx_diagnosis_code (diagnosis_code_icd10),
  CHECK (diagnosis_type IN ('primary', 'secondary', 'differential')),
  CHECK (status IN ('active', 'resolved', 'chronic')),
  CHECK (certainty IN ('confirmed', 'probable', 'suspected'))
);
```

---

### DOCUMENTS Table

**Purpose**: Store references to clinical documents

**Relationships**:
- One Consultation → Many Documents
- One Patient → Many Documents

```sql
CREATE TABLE DOCUMENTS (
  document_id UUID PRIMARY KEY,
  patient_id UUID NOT NULL,
  consultation_session_id UUID,

  document_type VARCHAR(100),                 -- discharge_summary, imaging_report, lab_report, correspondence, prescription
  document_format VARCHAR(50),                -- PDF, XML, FHIR, HL7, plain_text
  file_path VARCHAR(500),                     -- Storage location reference
  file_size_bytes INT,
  upload_date DATE,
  uploaded_by UUID,
  status VARCHAR(50),                         -- awaiting_filing, filed, archived

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (document_id),
  FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id),
  FOREIGN KEY (consultation_session_id) REFERENCES CONSULTATION_SESSIONS(consultation_session_id) ON DELETE SET NULL,
  INDEX idx_patient_documents (patient_id),
  INDEX idx_status (status),
  CHECK (document_type IN ('discharge_summary', 'imaging_report', 'lab_report', 'correspondence', 'prescription')),
  CHECK (status IN ('awaiting_filing', 'filed', 'archived'))
);
```

---

## 10. NLP Processing and Quality Assurance Tables (Do we need it for the MVP?)

### NLP_EXTRACTION_LOG Table

**Purpose**: Track NLP processing metadata and audit trail

**Relationships**:
- One Consultation Session → One NLP Extraction Log

```sql
CREATE TABLE NLP_EXTRACTION_LOG (
  extraction_log_id UUID PRIMARY KEY,
  consultation_session_id UUID NOT NULL,

  extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  extraction_model_name VARCHAR(100),         -- "Claude-medical-v2", "specialized-clinical-nlp"
  extraction_model_version VARCHAR(50),

  -- Extraction statistics
  total_entities_extracted INT,
  symptoms_extracted_count INT,
  diagnoses_extracted_count INT,
  medications_extracted_count INT,
  findings_extracted_count INT,

  -- Quality metrics
  average_confidence_score DECIMAL(3,2),      -- 0.00-1.00
  extraction_status VARCHAR(50),              -- success, partial_success, failed
  error_messages TEXT,

  -- Review status
  human_review_required BOOLEAN DEFAULT FALSE,
  human_reviewer_id UUID,
  human_review_notes TEXT,
  human_review_timestamp TIMESTAMP,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (extraction_log_id),
  FOREIGN KEY (consultation_session_id) REFERENCES CONSULTATION_SESSIONS(consultation_session_id),
  INDEX idx_extraction_status (extraction_status),
  INDEX idx_human_review (human_review_required),
  CHECK (extraction_status IN ('success', 'partial_success', 'failed'))
);
```

---

### CONSULTATION_QUALITY_FLAGS Table (Do we need it for the MVP?)

**Purpose**: Flag consultations requiring data quality review

**Relationships**:
- One Consultation Session → Many Quality Flags

```sql
CREATE TABLE CONSULTATION_QUALITY_FLAGS (
  quality_flag_id UUID PRIMARY KEY,
  consultation_session_id UUID NOT NULL,

  flag_type VARCHAR(100),                     -- incomplete_information, coding_review_needed, clinical_review_needed, data_quality_issue
  flag_description TEXT,
  severity VARCHAR(20),                       -- low, medium, high, critical
  assigned_to UUID,                           -- Staff member responsible for review
  flag_status VARCHAR(50) DEFAULT 'open',     -- open, in_review, resolved

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  resolved_at TIMESTAMP,

  PRIMARY KEY (quality_flag_id),
  FOREIGN KEY (consultation_session_id) REFERENCES CONSULTATION_SESSIONS(consultation_session_id),
  INDEX idx_flag_status (flag_status),
  INDEX idx_severity (severity),
  CHECK (flag_type IN ('incomplete_information', 'coding_review_needed', 'clinical_review_needed', 'data_quality_issue')),
  CHECK (severity IN ('low', 'medium', 'high', 'critical')),
  CHECK (flag_status IN ('open', 'in_review', 'resolved'))
);
```

---

### CONVERSATION_UTTERANCE_MAP Table

**Purpose**: Granular mapping of conversation lines to extracted entities

**Relationships**:
- One Consultation Session → Many Utterances

```sql
CREATE TABLE CONVERSATION_UTTERANCE_MAP (
  utterance_id UUID PRIMARY KEY,
  consultation_session_id UUID NOT NULL,

  utterance_sequence_number INT,
  speaker_role VARCHAR(50),                   -- patient, doctor, system
  utterance_text TEXT,                        -- Individual conversation line
  utterance_timestamp TIMESTAMP,

  -- Links to extracted entities from this utterance
  related_symptom_ids TEXT,                   -- JSON array: ["sym-001", "sym-002"]
  related_finding_ids TEXT,                   -- JSON array
  related_diagnosis_ids TEXT,                 -- JSON array
  related_medication_ids TEXT,                -- JSON array
  related_plan_ids TEXT,                      -- JSON array

  nlp_intent VARCHAR(100),                    -- info_seeking, symptom_reporting, question_answering, recommendation

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (utterance_id),
  FOREIGN KEY (consultation_session_id) REFERENCES CONSULTATION_SESSIONS(consultation_session_id),
  INDEX idx_utterance_sequence (consultation_session_id, utterance_sequence_number),
  CHECK (speaker_role IN ('patient', 'doctor', 'system'))
);
```

---

## 11. Lookup/Reference Tables

### SEVERITY_LEVELS Table

**Purpose**: Reference table for severity levels

```sql
CREATE TABLE SEVERITY_LEVELS (
  severity_id INT PRIMARY KEY,
  severity_name VARCHAR(50) NOT NULL UNIQUE,
  severity_code VARCHAR(10),
  description VARCHAR(255),
  ordering INT                                -- For sorting
);

INSERT INTO SEVERITY_LEVELS VALUES
(1, 'mild', 'M', 'Mild symptoms, minimal impact', 1),
(2, 'moderate', 'MOD', 'Moderate symptoms, some impact', 2),
(3, 'severe', 'S', 'Severe symptoms, significant impact', 3),
(4, 'critical', 'C', 'Critical symptoms, life-threatening', 4);
```

---

### DIAGNOSTIC_CERTAINTY Table

**Purpose**: Reference table for diagnostic certainty levels

```sql
CREATE TABLE DIAGNOSTIC_CERTAINTY (
  certainty_id INT PRIMARY KEY,
  certainty_name VARCHAR(50) NOT NULL UNIQUE,
  description VARCHAR(255),
  ordering INT
);

INSERT INTO DIAGNOSTIC_CERTAINTY VALUES
(1, 'confirmed', 'Diagnosis confirmed by tests or clinical signs', 1),
(2, 'probable', 'Highly likely based on clinical presentation', 2),
(3, 'suspected', 'Suspected but unconfirmed', 3),
(4, 'ruled_out', 'Previously considered but ruled out', 4);
```

---

## Common Query Examples

### Find all severe symptoms lasting >2 days

```sql
SELECT 
  p.first_name,
  p.last_name,
  s.symptom_name,
  s.duration_days,
  s.severity,
  cs.session_start_datetime
FROM SYMPTOMS s
JOIN CONSULTATION_SESSIONS cs ON s.consultation_session_id = cs.consultation_session_id
JOIN PATIENTS p ON s.patient_id = p.patient_id
WHERE s.severity = 'severe' AND s.duration_days > 2
ORDER BY cs.session_start_datetime DESC;
```

### Find consultations with bacterial tonsillitis diagnosis and antibiotic prescriptions

```sql
SELECT 
  p.patient_id,
  p.first_name,
  p.last_name,
  cae.assessment_diagnosis,
  cae.diagnostic_certainty,
  m.medication_name,
  m.dosage_value,
  m.dosage_unit,
  m.frequency,
  m.duration_value,
  m.duration_unit
FROM CLINICAL_ASSESSMENT_EXTRACTED cae
JOIN CONSULTATION_SESSIONS cs ON cae.consultation_session_id = cs.consultation_session_id
JOIN PATIENTS p ON cae.patient_id = p.patient_id
LEFT JOIN MEDICATIONS m ON cs.consultation_session_id = m.consultation_session_id
WHERE cae.assessment_diagnosis_code_icd10 = 'J03.90'
  AND cae.diagnostic_certainty IN ('confirmed', 'probable')
  AND m.medication_code IS NOT NULL
ORDER BY cs.session_start_datetime DESC;
```

### Find consultations requiring urgent follow-up

```sql
SELECT 
  p.first_name,
  p.last_name,
  fup.follow_up_action,
  fup.follow_up_priority,
  rfaw.warning_description,
  rfaw.severity,
  cs.session_start_datetime
FROM FOLLOW_UP_PLAN_EXTRACTED fup
JOIN CONSULTATION_SESSIONS cs ON fup.consultation_session_id = cs.consultation_session_id
JOIN PATIENTS p ON fup.patient_id = p.patient_id
LEFT JOIN RED_FLAGS_AND_WARNINGS rfaw ON cs.consultation_session_id = rfaw.consultation_session_id
WHERE fup.follow_up_priority IN ('urgent', 'emergent')
ORDER BY fup.follow_up_priority DESC, cs.session_start_datetime DESC;
```

### Extract complete clinical summary for a consultation (audit trail)

```sql
SELECT 
  cs.consultation_session_id,
  p.first_name,
  p.last_name,
  d.first_name AS doctor_first_name,
  d.last_name AS doctor_last_name,
  cs.session_start_datetime,
  -- Chief complaint
  cc.chief_complaint_free_text,
  -- Symptoms
  GROUP_CONCAT(DISTINCT CONCAT(s.symptom_name, ' (', s.severity, ')')) AS symptoms,
  -- Findings
  GROUP_CONCAT(DISTINCT af.finding_name) AS findings,
  -- Assessment
  cae.assessment_diagnosis,
  cae.diagnostic_certainty,
  -- Medications
  GROUP_CONCAT(DISTINCT CONCAT(m.medication_name, ' ', m.dosage_value, m.dosage_unit)) AS medications,
  -- Red flags
  GROUP_CONCAT(DISTINCT rfaw.warning_description) AS red_flags,
  -- Follow-up
  GROUP_CONCAT(DISTINCT fup.follow_up_action) AS follow_ups,
  -- Original transcript (for audit)
  SUBSTRING(cs.full_transcript, 1, 500) AS transcript_preview
FROM CONSULTATION_SESSIONS cs
JOIN CONSULTATIONS c ON cs.consultation_id = c.consultation_id
JOIN PATIENTS p ON cs.patient_id = p.patient_id
JOIN DOCTORS d ON cs.doctor_id = d.doctor_id
LEFT JOIN CHIEF_COMPLAINTS cc ON cs.consultation_session_id = cc.consultation_session_id
LEFT JOIN SYMPTOMS s ON cs.consultation_session_id = s.consultation_session_id
LEFT JOIN ASSOCIATED_FINDINGS af ON cs.consultation_session_id = af.consultation_session_id
LEFT JOIN CLINICAL_ASSESSMENT_EXTRACTED cae ON cs.consultation_session_id = cae.consultation_session_id
LEFT JOIN MEDICATIONS m ON cs.consultation_session_id = m.consultation_session_id
LEFT JOIN RED_FLAGS_AND_WARNINGS rfaw ON cs.consultation_session_id = rfaw.consultation_session_id
LEFT JOIN FOLLOW_UP_PLAN_EXTRACTED fup ON cs.consultation_session_id = fup.consultation_session_id
WHERE cs.consultation_session_id = 'your-consultation-uuid'
GROUP BY cs.consultation_session_id;
```

---

## Coding Standards Reference

| Element | Standard | Example |
|---------|----------|---------|
| **Symptoms/Findings** | SNOMED CT | Sore throat: 405737000, Fever: 386661006 |
| **Diagnoses** | ICD-10 primary, SNOMED CT secondary | Bacterial tonsillitis: J03.90 (ICD-10), 21300005 (SNOMED) |
| **Medications** | RxNorm (international), dm+d (UK) | Penicillin V: RxNorm 7980 |
| **Laboratory Tests** | LOINC | Complete Blood Count: 85025-9 |
| **Procedures** | SNOMED CT procedure codes | Throat exam: 117220006 |
| **Anatomical Sites** | SNOMED CT body structure codes | Pharynx: 31389004, Tonsil: 39607008 |
| **Frequency** | SNOMED CT frequency expressions | Four times daily: 307439001 |

---

## Data Retention and Compliance

- **Adult consultations**: Retain 8+ years after last contact (NHS standard)
- **Pediatric records**: Retain until patient age 25-26
- **Research data**: Minimum 10 years for basic research, 20+ years for clinical trials
- **GDPR**: Full transcript marked as PII, limited access required
- **Audit trail**: All access logged and tracked
- **Data deletion**: Can delete transcript after retention period, structured data retained longer

---

## Performance Optimization Notes

**Indexes**:
- Foreign keys: Always indexed for JOIN performance
- Frequently queried fields: severity, codes, dates, status
- Date ranges: consultation_date, created_at for range queries
- Full-text search: consultation_notes, education_content (if using full-text indexes)

**Partitioning Strategy** (for large data):
- Partition CONSULTATION_SESSIONS by year (session_start_datetime)
- Partition SYMPTOMS by patient_id (for faster patient-specific queries)
- Partition MEDICATIONS by consultation_session_id

**Query Optimization**:
- Always filter on consultation_session_id or patient_id when possible
- Use indexes on (consultation_session_id, code) for dual filtering
- Avoid scanning full_transcript column (expensive TEXT search)

---

## Database Creation Script Summary

Total tables: **30+** (production-ready)

**Core tables**: PATIENTS, DOCTORS, DEPARTMENTS, APPOINTMENTS, CONSULTATIONS, CONSULTATION_SESSIONS (6)

**Clinical data**: SYMPTOMS, ASSOCIATED_FINDINGS, PHYSICAL_EXAMINATION_FINDINGS, REVIEW_OF_SYSTEMS, VITAL_SIGNS, LABORATORY_RESULTS (6)

**Assessment**: CLINICAL_ASSESSMENT_EXTRACTED, DIFFERENTIAL_DIAGNOSES, DIAGNOSES, MEDICAL_HISTORY, ALLERGIES (5)

**Treatment**: MEDICATIONS, DOCUMENTS (2)

**Safety/Follow-up**: RED_FLAGS_AND_WARNINGS, FOLLOW_UP_PLAN_EXTRACTED (2)

**Education/Context**: PATIENT_EDUCATION_EXTRACTED, SOCIAL_HISTORY_EXTRACTED (2)

**NLP/QA**: NLP_EXTRACTION_LOG, CONSULTATION_QUALITY_FLAGS, CONVERSATION_UTTERANCE_MAP (3)

**Lookup**: SEVERITY_LEVELS, DIAGNOSTIC_CERTAINTY (2)

All tables include:
- Primary keys (UUID)
- Foreign key relationships
- Appropriate data types with lengths/precision
- NOT NULL constraints on required fields
- CHECK constraints for enums
- UNIQUE constraints where needed
- Timestamps (created_at, updated_at)
- Indexes on frequently queried fields
- Sample data examples
