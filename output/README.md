# Output Files

This directory contains generated CSV files from the GP Consultation Data Extraction System.

## Output Structure

The system generates one CSV file per database table, plus a manifest file.

### Generated Files

1. `consultation_sessions.csv` - Session metadata and full transcript
2. `consultations.csv` - Structured consultation record
3. `symptoms.csv` - Patient-reported symptoms
4. `medications.csv` - Prescribed medications
5. `associated_findings.csv` - Objective clinical findings
6. `physical_examination_findings.csv` - Physical exam results
7. `review_of_systems.csv` - Systematic body system review
8. `vital_signs.csv` - Clinical measurements
9. `laboratory_results.csv` - Lab test results
10. `clinical_assessment_extracted.csv` - Diagnostic assessment
11. `red_flags_and_warnings.csv` - Warning signs
12. `follow_up_plan_extracted.csv` - Follow-up instructions
13. `allergies.csv` - Patient allergies
14. `diagnoses.csv` - Final diagnoses
15. `severity_levels.csv` - Lookup table for severity values
16. `diagnostic_certainty.csv` - Lookup table for certainty levels
17. `manifest.json` - Metadata about generated files

## CSV Format

### Encoding
- **Character Encoding**: UTF-8
- **Line Endings**: Unix-style (LF)
- **Delimiter**: Comma (,)

### Data Representation
- **NULL Values**: Empty strings
- **JSONB Fields**: Serialized as JSON strings
- **Timestamps**: ISO 8601 format (e.g., `2025-11-16T10:30:00Z`)
- **UUIDs**: Standard UUID format (e.g., `550e8400-e29b-41d4-a716-446655440000`)
- **Special Characters**: Properly escaped with quotes

## Manifest File

The `manifest.json` file contains metadata about the extraction:

```json
{
  "extraction_timestamp": "2025-11-16T10:30:00Z",
  "consultation_session_id": "550e8400-e29b-41d4-a716-446655440000",
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

### Manifest Fields

- `extraction_timestamp`: When the extraction was performed (UTC)
- `consultation_session_id`: UUID of the consultation session
- `files`: Array of generated files with table name, filename, and row count
- `total_entities_extracted`: Total number of clinical entities extracted
- `processing_time_seconds`: Time taken to process the consultation

## Database Ingestion Guide

### Import Order

Import CSV files in this order to satisfy foreign key constraints:

1. **Lookup Tables** (no dependencies):
   - `severity_levels.csv`
   - `diagnostic_certainty.csv`

2. **Parent Table**:
   - `consultation_sessions.csv`

3. **Child Tables** (depend on consultation_sessions):
   - `consultations.csv`
   - `symptoms.csv`
   - `medications.csv`
   - `diagnoses.csv`
   - `vital_signs.csv`
   - `physical_examination_findings.csv`
   - `associated_findings.csv`
   - `review_of_systems.csv`
   - `laboratory_results.csv`
   - `clinical_assessment_extracted.csv`
   - `red_flags_and_warnings.csv`
   - `follow_up_plan_extracted.csv`
   - `allergies.csv`

### PostgreSQL COPY Command

```sql
-- Import lookup tables first
COPY severity_levels FROM '/path/to/severity_levels.csv' 
WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');

COPY diagnostic_certainty FROM '/path/to/diagnostic_certainty.csv' 
WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');

-- Import parent table
COPY consultation_sessions FROM '/path/to/consultation_sessions.csv' 
WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');

-- Import child tables
COPY symptoms FROM '/path/to/symptoms.csv' 
WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');

COPY medications FROM '/path/to/medications.csv' 
WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');

-- Repeat for all other tables...
```

### Batch Import Script

```bash
#!/bin/bash
# import_csvs.sh

DB_NAME="gp_consultations"
CSV_DIR="/path/to/output"

# Import lookup tables
psql -d $DB_NAME -c "COPY severity_levels FROM '$CSV_DIR/severity_levels.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');"
psql -d $DB_NAME -c "COPY diagnostic_certainty FROM '$CSV_DIR/diagnostic_certainty.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');"

# Import parent table
psql -d $DB_NAME -c "COPY consultation_sessions FROM '$CSV_DIR/consultation_sessions.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');"

# Import child tables
for table in consultations symptoms medications diagnoses vital_signs physical_examination_findings; do
  psql -d $DB_NAME -c "COPY $table FROM '$CSV_DIR/${table}.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF-8');"
done
```

## CSV Schema Examples

### consultation_sessions.csv
```csv
consultation_session_id,patient_id,doctor_id,session_start_datetime,full_transcript,transcript_language,nlp_processed_flag,created_at
550e8400-e29b-41d4-a716-446655440000,660e8400-e29b-41d4-a716-446655440001,770e8400-e29b-41d4-a716-446655440002,2025-11-16T10:30:00Z,"Patient: I have a headache...",en-UK,true,2025-11-16T10:35:00Z
```

### symptoms.csv
```csv
symptom_id,consultation_session_id,patient_id,symptom_name,symptom_code,severity,duration_days,onset_date,temporal_pattern,confidence_score,clinical_modifiers,extracted_at
880e8400-e29b-41d4-a716-446655440003,550e8400-e29b-41d4-a716-446655440000,660e8400-e29b-41d4-a716-446655440001,headache,R51,severe,3,2025-11-13T00:00:00Z,worse in morning,0.95,"{""location"": ""frontal""}",2025-11-16T10:35:00Z
```

### medications.csv
```csv
prescription_id,consultation_session_id,patient_id,doctor_id,medication_name,dosage_value,dosage_unit,frequency,duration_value,duration_unit,route_of_administration,indication,prescribed_at
990e8400-e29b-41d4-a716-446655440004,550e8400-e29b-41d4-a716-446655440000,660e8400-e29b-41d4-a716-446655440001,770e8400-e29b-41d4-a716-446655440002,Ibuprofen,400,mg,three times daily,5,days,oral,pain relief,2025-11-16T10:35:00Z
```

## Handling Special Cases

### Empty Tables
If no entities of a type are extracted, an empty CSV with headers only is generated:
```csv
symptom_id,consultation_session_id,patient_id,symptom_name,symptom_code,severity,duration_days,onset_date,temporal_pattern,confidence_score,clinical_modifiers,extracted_at
```

### JSONB Fields
JSONB fields are exported as JSON strings and automatically converted by PostgreSQL:
```csv
clinical_modifiers
"{""location"": ""frontal"", ""radiation"": ""none""}"
```

### NULL Values
NULL values are represented as empty strings:
```csv
symptom_id,symptom_name,severity,duration_days
880e8400...,headache,severe,
```

### Special Characters
Special characters are properly escaped:
```csv
full_transcript
"Patient said: ""I feel terrible"" and started crying."
```

## Validation

Before importing, validate:
1. All UUIDs are valid UUID4 format
2. All timestamps are ISO 8601 format
3. All foreign keys reference existing records
4. All severity values exist in `SEVERITY_LEVELS`
5. All certainty values exist in `DIAGNOSTIC_CERTAINTY`

## Troubleshooting

### Import Errors

**Foreign Key Violation**:
- Ensure parent tables are imported before child tables
- Verify `consultation_session_id` exists in `CONSULTATION_SESSIONS`

**Invalid UUID Format**:
- Check that UUIDs match pattern: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

**Encoding Issues**:
- Ensure database encoding is UTF-8
- Verify CSV files are UTF-8 encoded

**JSONB Parse Errors**:
- Validate JSON strings are properly formatted
- Check for unescaped quotes in JSON

### Performance Tips

1. **Disable Indexes**: Drop indexes before bulk import, recreate after
2. **Batch Import**: Import multiple files in a single transaction
3. **Use COPY**: Much faster than INSERT statements
4. **Increase Work Memory**: `SET work_mem = '256MB';` for large imports

## Best Practices

1. **Backup First**: Always backup database before importing
2. **Test Import**: Test with small dataset first
3. **Validate Data**: Check row counts match manifest
4. **Monitor Logs**: Watch PostgreSQL logs for errors
5. **Verify Relationships**: Query foreign key relationships after import
