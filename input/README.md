# Input Files

This directory contains GP consultation transcript files in Markdown format for processing.

## Input File Format

### File Requirements

- **Format**: Markdown (`.md`)
- **Encoding**: UTF-8
- **Structure**: Conversational dialogue between patient and GP

### Minimum Required Structure

A valid consultation transcript should include:
1. Patient dialogue (symptoms, concerns, history)
2. GP dialogue (questions, examination, diagnosis, treatment plan)
3. Clear speaker identification (e.g., "Patient:", "GP:", "Doctor:")

### Example Format

```markdown
# GP Consultation - [Date]

**Patient**: I've been having lower back pain for about a week now.

**GP**: Can you describe the pain? Is it sharp or dull?

**Patient**: It's a dull ache, mostly on the right side.

**GP**: Have you had any recent injuries or heavy lifting?

**Patient**: Yes, I helped move furniture last weekend.

**GP**: Let me examine your back. [Performs physical examination]

**GP**: Based on the examination, this appears to be a mechanical strain. I'll prescribe some pain relief and recommend rest.

**Patient**: Should I take time off work?

**GP**: Yes, I recommend 3-5 days of rest. Take Ibuprofen 400mg three times daily with food.
```

## Validation Rules

The system validates input files for:

1. **File Existence**: File must exist at specified path
2. **File Readability**: File must be readable with UTF-8 encoding
3. **Minimum Content**: File must contain dialogue text
4. **Format Structure**: File should have identifiable patient/GP dialogue

### Validation Errors

Common validation errors:
- `FileNotFoundError`: Input file does not exist
- `UnicodeDecodeError`: File is not UTF-8 encoded
- `ValidationError`: File does not contain valid consultation structure

## Sample Consultation Files

The repository includes sample consultation files in `consulation_recording_simulation/`:

### `case_1.md` - Lower Back Pain
- **Chief Complaint**: Lower back pain
- **Diagnosis**: Mechanical strain
- **Treatment**: Pain relief, rest, physiotherapy referral

### `case_2.md` - Sore Throat
- **Chief Complaint**: Sore throat
- **Diagnosis**: Bacterial tonsillitis
- **Treatment**: Antibiotics, pain relief

### `case_3.md` - [Additional Case]
- [Description to be added]

### `case_4.md` - [Additional Case]
- [Description to be added]

## Creating New Input Files

### Guidelines

1. **Use clear speaker labels**: "Patient:", "GP:", "Doctor:"
2. **Include clinical details**: Symptoms, examination findings, diagnoses
3. **Mention medications explicitly**: Include dosage, frequency, duration
4. **Document follow-up plans**: Specify timing and conditions
5. **Include vital signs if measured**: Blood pressure, temperature, etc.

### Template

```markdown
# GP Consultation - [Date]

## Chief Complaint
**Patient**: [Main reason for visit]

## History of Present Illness
**GP**: [Questions about symptoms]
**Patient**: [Detailed symptom description]

## Physical Examination
**GP**: [Examination findings]

## Assessment
**GP**: [Diagnosis and reasoning]

## Plan
**GP**: [Treatment plan, medications, follow-up]
**Patient**: [Questions or concerns]

## Follow-up
**GP**: [Follow-up instructions]
```

## Entity Extraction Examples

The system extracts the following entities from consultation transcripts:

### Symptoms
- Name, severity, duration, onset, temporal pattern
- Example: "severe headache for 3 days, worse in the morning"

### Medications
- Name, dosage, route, frequency, duration, indication
- Example: "Ibuprofen 400mg orally three times daily for 5 days for pain relief"

### Diagnoses
- Name, certainty level, supporting features
- Example: "Probable migraine based on unilateral throbbing pain and photophobia"

### Vital Signs
- Temperature, blood pressure, heart rate, oxygen saturation, respiratory rate
- Example: "Blood pressure 120/80, heart rate 72 bpm"

### Physical Examination
- Examination type, anatomical site, findings, severity
- Example: "Cardiovascular examination: heart sounds normal, no murmurs"

### Red Flags
- Warning description, type, severity
- Example: "Chest pain radiating to left arm - urgent cardiology referral needed"

### Follow-up Plans
- Type, timing, condition, action, priority
- Example: "Follow-up in 2 weeks if symptoms persist"

## Best Practices

1. **Use realistic dialogue**: Natural conversation flow helps extraction accuracy
2. **Be specific with measurements**: Include units (mg, ml, days, etc.)
3. **Document examination findings**: Even negative findings are valuable
4. **Include temporal information**: When symptoms started, how long medications should be taken
5. **Mention patient concerns**: Questions and worries provide context
6. **Document clinical reasoning**: Why a diagnosis was made or ruled out

## Processing Input Files

### Command-Line Usage

```bash
# Process a single consultation
python -m src.main --input input/consultation.md --use-test-data

# Process with specific patient/doctor IDs
python -m src.main --input input/consultation.md
```

### Docker Usage

```bash
# Mount input directory and process file
docker-compose run extractor --input /input/consultation.md --use-test-data
```

## Troubleshooting

### File Not Found
- Verify file path is correct
- Check file is in `input/` directory
- Use absolute or relative path from project root

### Encoding Errors
- Ensure file is saved with UTF-8 encoding
- Convert file encoding if necessary: `iconv -f ISO-8859-1 -t UTF-8 input.md > output.md`

### Poor Extraction Results
- Add more clinical details to the transcript
- Use clear speaker labels
- Include specific measurements and dosages
- Review few-shot examples in `config/few_shot_examples.yaml`

## Privacy and Security

**Important**: Consultation transcripts may contain sensitive patient information (PII/PHI).

- **Never commit real patient data** to version control
- Use anonymized or synthetic data for testing
- Follow HIPAA/GDPR guidelines for data handling
- Encrypt files containing real patient information
- Use the `--use-test-data` flag to generate synthetic patient data
