# Output Documentation

This directory contains the generated CSV files and manifest from the extraction process.

## Output Files

After running the extraction, this directory will contain:

### CSV Files (Database Tables)

1. **consultation_sessions.csv** - Session metadata and full transcript
2. **consultations.csv** - Structured consultation record
3. **symptoms.csv** - Patient-reported symptoms
4. **medications.csv** - Prescribed medications
5. **diagnoses.csv** - Final diagnoses
6. **clinical_assessment_extracted.csv** - Diagnostic assessment
7. **vital_signs.csv** - Clinical measurements
8. **physical_examination_findings.csv** - Physical exam results
9. **red_flags_and_warnings.csv** - Warning signs
10. **follow_up_plan_extracted.csv** - Follow-up instructions

### Manifest File

**manifest.json** - Extraction metadata and file listing

## CSV Format

All CSV files follow these conventions:

- **Encoding**: UTF-8
- **Delimiter**: Comma (`,`)
- **Quote Character**: Double quote (`"`)
- **Escape Character**: Backslash (`\`)
- **NULL Values**: Empty strings
- **Headers**: First row contains column names matching database schema

## Table Schemas

### consultation_sessions.csv

Session metadata and full transcript.

| Column | Type | Description |
|--------|------|-------------|
| consultation_session_id | UUID | Primary key |
| patient_id | UUID | Foreign key to patient |
| doctor_id | UUID | Foreign key to doctor |
| session_start_datetime | TIMESTAMP | Session start time (ISO 8601) |
| full_transcript | TEXT | Complete consultation transcript |
| transcript_language | VARCHAR | Language code (e.g., "en-UK") |
| nlp_processed_flag | BOOLEAN | Always true for extracted data |
| created_at | TIMESTAMP | Record creation time (ISO 8601) |

**Example**:
```csv
consultation_session_id,patient_id,doctor_id,session_start_datetime,full_transcript,transcript_language,nlp_processed_flag,created_at
123e4567-e89b-12d3-a456-426614174000,987fcdeb-51a2-43f7-8c9d-123456789abc,456e7890-f12b-34c5-d678-901234567def,2024-11-16T10:30:00Z,"# GP Consultation...",en-UK,true,2024-11-16T10:30:00Z
```

### consultations.csv

Structured consultation record.

| Column | Type | Description |
|--------|------|-------------|
| consultation_id | UUID | Primary key |
| consultation_session_id | UUID | Foreign key to session |
| patient_id | UUID | Foreign key to patient |
| doctor_id | UUID | Foreign key to doctor |
| consultation_datetime | TIMESTAMP | Consultation date/time |
| consultation_type | VARCHAR | Type (e.g., "GP Consultation") |
| chief_complaint | TEXT | Main complaint |
| history_of_present_illness | TEXT | History details |
| created_at | TIMESTAMP | Record creation time |

### symptoms.csv

Patient-reported symptoms.

| Column | Type | Description |
|--------|------|-------------|
| symptom_id | UUID | Primary key |
| consultation_session_id | UUID | Foreign key to session |
| patient_id | UUID | Foreign key to patient |
| symptom_name | VARCHAR | Symptom name |
| symptom_code | VARCHAR | SNOMED CT code (if available) |
| severity | VARCHAR | Severity level (mild/moderate/severe/critical) |
| duration_days | INTEGER | Duration in days |
| onset_date | DATE | Onset date (ISO 8601) |
| temporal_pattern | VARCHAR | Pattern description |
| confidence_score | FLOAT | Extraction confidence (0.0-1.0) |
| clinical_modifiers | JSONB | Additional modifiers (JSON string) |
| extracted_at | TIMESTAMP | Extraction timestamp |

**Example**:
```csv
symptom_id,consultation_session_id,patient_id,symptom_name,symptom_code,severity,duration_days,onset_date,temporal_pattern,confidence_score,clinical_modifiers,extracted_at
abc12345-...,123e4567-...,987fcdeb-...,lower back pain,,moderate,1,2024-11-15,sharp pain when moving,0.85,{},2024-11-16T10:30:00Z
```

### medications.csv

Prescribed medications.

| Column | Type | Description |
|--------|------|-------------|
| prescription_id | UUID | Primary key |
| consultation_session_id | UUID | Foreign key to session |
| patient_id | UUID | Foreign key to patient |
| doctor_id | UUID | Foreign key to doctor |
| medication_name | VARCHAR | Medication name |
| dosage_value | INTEGER | Dosage amount |
| dosage_unit | VARCHAR | Dosage unit (mg, ml, etc.) |
| frequency | VARCHAR | Frequency (daily, twice daily, etc.) |
| duration_value | INTEGER | Duration amount |
| duration_unit | VARCHAR | Duration unit (days, weeks, etc.) |
| route_of_administration | VARCHAR | Route (oral, IV, etc.) |
| indication | VARCHAR | Reason for prescription |
| prescribed_at | TIMESTAMP | Prescription timestamp |

**Example**:
```csv
prescription_id,consultation_session_id,patient_id,doctor_id,medication_name,dosage_value,dosage_unit,frequency,duration_value,duration_unit,route_of_administration,indication,prescribed_at
def45678-...,123e4567-...,987fcdeb-...,456e7890-...,Ibuprofen,400,mg,as needed,7,days,oral,pain relief,2024-11-16T10:30:00Z
```

### diagnoses.csv

Final diagnoses.

| Column | Type | Description |
|--------|------|-------------|
| diagnosis_id | UUID | Primary key |
| consultation_session_id | UUID | Foreign key to session |
| patient_id | UUID | Foreign key to patient |
| doctor_id | UUID | Foreign key to doctor |
| diagnosis_name | VARCHAR | Diagnosis name |
| diagnosis_code | VARCHAR | ICD-10 code (if available) |
| diagnostic_certainty | VARCHAR | Certainty level (confirmed/probable/suspected/ruled_out) |
| clinical_notes | TEXT | Additional notes |
| diagnosed_at | TIMESTAMP | Diagnosis timestamp |

### vital_signs.csv

Clinical measurements.

| Column | Type | Description |
|--------|------|-------------|
| vital_sign_id | UUID | Primary key |
| consultation_session_id | UUID | Foreign key to session |
| patient_id | UUID | Foreign key to patient |
| temperature | FLOAT | Temperature in Celsius |
| blood_pressure | VARCHAR | Blood pressure (e.g., "120/80") |
| heart_rate | INTEGER | Heart rate in bpm |
| oxygen_saturation | FLOAT | O2 saturation percentage |
| respiratory_rate | INTEGER | Respiratory rate per minute |
| measured_at | TIMESTAMP | Measurement timestamp |

### physical_examination_findings.csv

Physical exam results.

| Column | Type | Description |
|--------|------|-------------|
| exam_finding_id | UUID | Primary key |
| consultation_session_id | UUID | Foreign key to session |
| patient_id | UUID | Foreign key to patient |
| examination_type | VARCHAR | Type of examination |
| anatomical_site | VARCHAR | Body part examined |
| findings | TEXT | Examination findings |
| severity | VARCHAR | Severity level |
| examined_at | TIMESTAMP | Examination timestamp |

### red_flags_and_warnings.csv

Warning signs.

| Column | Type | Description |
|--------|------|-------------|
| red_flag_id | UUID | Primary key |
| consultation_session_id | UUID | Foreign key to session |
| patient_id | UUID | Foreign key to patient |
| warning_description | TEXT | Warning description |
| warning_type | VARCHAR | Type of warning |
| severity | VARCHAR | Severity level |
| identified_at | TIMESTAMP | Identification timestamp |

### follow_up_plan_extracted.csv

Follow-up instructions.

| Column | Type | Description |
|--------|------|-------------|
| follow_up_id | UUID | Primary key |
| consultation_session_id | UUID | Foreign key to session |
| patient_id | UUID | Foreign key to patient |
| follow_up_type | VARCHAR | Type of follow-up |
| timing | VARCHAR | When to follow up |
| condition | TEXT | Conditions for follow-up |
| action | TEXT | Action to take |
| priority | VARCHAR | Priority level |
| planned_at | TIMESTAMP | Planning timestamp |

## Manifest File Format

The `manifest.json` file contains metadata about the extraction:

```json
{
  "extraction_timestamp": "2024-11-16T10:30:00Z",
  "consultation_session_id": "123e4567-e89b-12d3-a456-426614174000",
  "files": [
    {
      "table": "CONSULTATION_SESSIONS",
      "file": "consultation_sessions.csv",
      "row_count": 1
    },
    {
      "table": "SYMPTOMS",
      "file": "symptoms.csv",
      "row_count": 5
    }
  ],
  "total_entities_extracted": 42,
  "processing_time_seconds": 15.3
}
```

## JSONB Fields

Some fields contain JSON data serialized as strings:

### clinical_modifiers (in symptoms.csv)

```json
{
  "location": "lower back",
  "radiation": "down left leg",
  "aggravating_factors": ["bending", "lifting"],
  "relieving_factors": ["rest"]
}
```

In CSV, this appears as:
```csv
"{""location"": ""lower back"", ""radiation"": ""down left leg""}"
```

## Database Ingestion

### PostgreSQL COPY Command

Import CSV files into PostgreSQL:

```sql
-- Import consultation sessions
COPY consultation_sessions 
FROM '/path/to/output/consultation_sessions.csv' 
WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');

-- Import symptoms
COPY symptoms 
FROM '/path/to/output/symptoms.csv' 
WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');

-- Import medications
COPY medications 
FROM '/path/to/output/medications.csv' 
WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');

-- Continue for all tables...
```

### Import Order

Import tables in this order to satisfy foreign key constraints:

1. `consultation_sessions.csv` (parent table)
2. `consultations.csv`
3. All other tables (order doesn't matter)

### Handling Empty Tables

Empty CSV files contain only headers. PostgreSQL will import them without errors:

```csv
symptom_id,consultation_session_id,patient_id,symptom_name,...
```

Result: 0 rows imported.

### JSONB Import

JSONB fields are automatically converted from JSON strings:

```sql
-- The clinical_modifiers column is defined as JSONB
-- PostgreSQL automatically converts the JSON string
SELECT clinical_modifiers->>'location' FROM symptoms;
-- Returns: "lower back"
```

## Data Validation

Before importing, validate:

1. **File Existence**: All expected CSV files exist
2. **File Size**: Files are not empty (except for tables with no data)
3. **Header Match**: Headers match database schema
4. **UUID Format**: All UUIDs are valid UUID4 format
5. **Foreign Keys**: All foreign keys reference existing records
6. **Data Types**: Values match expected data types

### Validation Script Example

```python
import pandas as pd
import uuid

def validate_csv(filepath, required_columns):
    df = pd.read_csv(filepath)
    
    # Check headers
    assert set(required_columns).issubset(set(df.columns))
    
    # Check UUIDs
    for col in df.columns:
        if col.endswith('_id'):
            for val in df[col].dropna():
                uuid.UUID(val)  # Raises ValueError if invalid
    
    print(f"✓ {filepath} validated")

validate_csv('output/symptoms.csv', [
    'symptom_id', 'consultation_session_id', 'patient_id'
])
```

## Troubleshooting

### Empty CSV Files

If all CSV files are empty:
- Check input file format
- Verify LLM API credentials
- Review extraction logs for errors

### Missing Columns

If columns are missing:
- Verify application version matches schema
- Check for extraction errors in logs
- Ensure all entity types were extracted

### Invalid UUIDs

If UUIDs are invalid:
- Check UUID generation in data_mapper.py
- Verify Python uuid module is working
- Review logs for UUID generation errors

### JSONB Parse Errors

If JSONB fields fail to import:
- Verify JSON is valid: `python -c "import json; json.loads(...)"`
- Check for unescaped quotes
- Review CSV escaping in csv_exporter.py

## Performance

### File Sizes

Typical file sizes for a standard consultation:

- consultation_sessions.csv: ~5-10 KB
- symptoms.csv: ~1-2 KB
- medications.csv: ~1-2 KB
- diagnoses.csv: ~1 KB
- Total: ~10-20 KB

### Import Time

PostgreSQL import times (approximate):

- Small consultation (<50 entities): <1 second
- Medium consultation (50-200 entities): 1-2 seconds
- Large consultation (>200 entities): 2-5 seconds

## Best Practices

1. **Backup**: Always backup database before importing
2. **Validation**: Validate CSV files before importing
3. **Transactions**: Use transactions for atomic imports
4. **Logging**: Log import results and errors
5. **Monitoring**: Monitor import performance and errors

## Example Import Script

```bash
#!/bin/bash

# PostgreSQL import script
DB_NAME="gp_consultations"
OUTPUT_DIR="output"

# Import in correct order
psql $DB_NAME -c "COPY consultation_sessions FROM '$(pwd)/$OUTPUT_DIR/consultation_sessions.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');"
psql $DB_NAME -c "COPY consultations FROM '$(pwd)/$OUTPUT_DIR/consultations.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');"
psql $DB_NAME -c "COPY symptoms FROM '$(pwd)/$OUTPUT_DIR/symptoms.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');"
psql $DB_NAME -c "COPY medications FROM '$(pwd)/$OUTPUT_DIR/medications.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');"
psql $DB_NAME -c "COPY diagnoses FROM '$(pwd)/$OUTPUT_DIR/diagnoses.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');"
psql $DB_NAME -c "COPY clinical_assessment_extracted FROM '$(pwd)/$OUTPUT_DIR/clinical_assessment_extracted.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');"
psql $DB_NAME -c "COPY vital_signs FROM '$(pwd)/$OUTPUT_DIR/vital_signs.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');"
psql $DB_NAME -c "COPY physical_examination_findings FROM '$(pwd)/$OUTPUT_DIR/physical_examination_findings.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');"
psql $DB_NAME -c "COPY red_flags_and_warnings FROM '$(pwd)/$OUTPUT_DIR/red_flags_and_warnings.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');"
psql $DB_NAME -c "COPY follow_up_plan_extracted FROM '$(pwd)/$OUTPUT_DIR/follow_up_plan_extracted.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');"

echo "Import complete!"
```
