"""Clinical entity extraction using LangExtract.

This module extracts structured clinical entities from consultation transcripts
using LangExtract with few-shot learning examples.
"""

import yaml
import time
from typing import List, Dict, Optional
from pathlib import Path
import logging

try:
    import langextract as lx
except ImportError:
    # For testing without langextract installed
    lx = None

from llm_provider import LLMProviderManager, LLMProviderError


logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Raised when entity extraction fails."""
    pass


class ClinicalEntityExtractor:
    """Extracts structured clinical entities using LangExtract."""
    
    def __init__(self, llm_provider: LLMProviderManager, few_shot_config_path: str = 'config/few_shot_examples.yaml'):
        """Initialize clinical entity extractor.
        
        Args:
            llm_provider: LLM provider manager instance
            few_shot_config_path: Path to few-shot examples configuration file
            
        Raises:
            ExtractionError: If few-shot examples cannot be loaded
        """
        if lx is None:
            raise ExtractionError("langextract library not installed")
        
        self.llm_provider = llm_provider
        self.few_shot_examples = self._load_few_shot_examples(few_shot_config_path)
        self.retry_attempts = 1
        self.retry_delay = 1  # seconds
    
    def _load_few_shot_examples(self, config_path: str) -> Dict:
        """Load few-shot examples from YAML configuration.
        
        Args:
            config_path: Path to YAML configuration file
            
        Returns:
            Dictionary of few-shot examples by entity type
            
        Raises:
            ExtractionError: If configuration file cannot be loaded
        """
        path = Path(config_path)
        if not path.exists():
            raise ExtractionError(f"Few-shot examples file not found: {config_path}")
        
        try:
            with open(path, 'r') as f:
                examples = yaml.safe_load(f)
            
            if not examples:
                raise ExtractionError("Few-shot examples file is empty")
            
            return examples
        except yaml.YAMLError as e:
            raise ExtractionError(f"Failed to parse few-shot examples: {e}")
        except Exception as e:
            raise ExtractionError(f"Failed to load few-shot examples: {e}")
    
    def _convert_to_langextract_examples(self, examples_config: List[Dict]) -> List:
        """Convert YAML examples to LangExtract ExampleData format.
        
        Args:
            examples_config: List of example dictionaries from YAML
            
        Returns:
            List of LangExtract ExampleData objects
        """
        langextract_examples = []
        
        for example in examples_config:
            text = example.get('text', '')
            extractions_config = example.get('extractions', [])
            
            extractions = []
            for ext in extractions_config:
                extraction = lx.data.Extraction(
                    extraction_class=ext.get('class'),
                    extraction_text=ext.get('text'),
                    attributes=ext.get('attributes', {})
                )
                extractions.append(extraction)
            
            example_data = lx.data.ExampleData(
                text=text,
                extractions=extractions
            )
            langextract_examples.append(example_data)
        
        return langextract_examples
    
    def _extract_with_retry(self, text: str, prompt_description: str, 
                           examples: List, entity_type: str) -> List[Dict]:
        """Extract entities with retry logic for API failures.
        
        Args:
            text: Text to extract from
            prompt_description: Description of what to extract
            examples: Few-shot examples
            entity_type: Type of entity being extracted (for logging)
            
        Returns:
            List of extracted entities
            
        Raises:
            ExtractionError: If extraction fails after retries
        """
        credentials = self.llm_provider.get_api_credentials()
        provider = self.llm_provider.get_provider()
        
        for attempt in range(self.retry_attempts + 1):
            try:
                if provider == 'gemini':
                    api_key = credentials['api_key']
                    model_id = credentials.get('model', 'gemini-2.5-pro')
                    
                    result = lx.extract(
                        text_or_documents=text,
                        prompt_description=prompt_description,
                        examples=examples,
                        api_key=api_key,
                        model_id=model_id
                    )
                
                elif provider == 'bedrock':
                    # For Bedrock, we need to use boto3 client
                    bedrock_client = self.llm_provider.get_bedrock_client()
                    model_id = credentials.get('model_id')
                    
                    # LangExtract supports Bedrock through custom client
                    result = lx.extract(
                        text_or_documents=text,
                        prompt_description=prompt_description,
                        examples=examples,
                        bedrock_client=bedrock_client,
                        model_id=model_id
                    )
                
                else:
                    raise ExtractionError(f"Unsupported provider: {provider}")
                
                logger.info(f"Successfully extracted {entity_type} entities")
                return self._parse_extraction_result(result)
            
            except Exception as e:
                if attempt < self.retry_attempts:
                    logger.warning(
                        f"Extraction attempt {attempt + 1} failed for {entity_type}: {e}. "
                        f"Retrying in {self.retry_delay}s..."
                    )
                    time.sleep(self.retry_delay)
                    self.retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Extraction failed for {entity_type} after {attempt + 1} attempts: {e}")
                    raise ExtractionError(f"Failed to extract {entity_type}: {e}")
    
    def _parse_extraction_result(self, result) -> List[Dict]:
        """Parse LangExtract result into list of dictionaries.
        
        Args:
            result: LangExtract extraction result
            
        Returns:
            List of extracted entities as dictionaries
        """
        entities = []
        
        if hasattr(result, 'extractions'):
            for extraction in result.extractions:
                entity = {
                    'class': extraction.extraction_class,
                    'text': extraction.extraction_text,
                    'attributes': extraction.attributes if hasattr(extraction, 'attributes') else {}
                }
                entities.append(entity)
        
        return entities
    
    def extract_symptoms(self, text: str) -> List[Dict]:
        """Extract symptoms with attributes.
        
        Args:
            text: Consultation transcript text
            
        Returns:
            List of symptom dictionaries with grouping attributes
        """
        examples_config = self.few_shot_examples.get('symptoms', [])
        examples = self._convert_to_langextract_examples(examples_config)
        
        prompt_description = """
        Extract symptom information including symptom name, severity, duration, onset, and temporal pattern.
        Use 'symptom_group' attribute to link related information about the same symptom.
        Extract entities in the order they appear in the text.
        """
        
        return self._extract_with_retry(text, prompt_description, examples, 'symptoms')
    
    def extract_medications(self, text: str) -> List[Dict]:
        """Extract medications with grouping.
        
        Args:
            text: Consultation transcript text
            
        Returns:
            List of medication dictionaries with grouping attributes
        """
        examples_config = self.few_shot_examples.get('medications', [])
        examples = self._convert_to_langextract_examples(examples_config)
        
        prompt_description = """
        Extract medication information including medication name, dosage, route, frequency, duration, and indication.
        Use 'medication_group' attribute to group related information about the same medication.
        Extract entities in the order they appear in the text.
        """
        
        return self._extract_with_retry(text, prompt_description, examples, 'medications')
    
    def extract_diagnoses(self, text: str) -> List[Dict]:
        """Extract diagnoses with certainty.
        
        Args:
            text: Consultation transcript text
            
        Returns:
            List of diagnosis dictionaries with grouping attributes
        """
        examples_config = self.few_shot_examples.get('diagnoses', [])
        examples = self._convert_to_langextract_examples(examples_config)
        
        prompt_description = """
        Extract diagnosis information including diagnosis name, diagnostic certainty, and clinical features.
        Use 'diagnosis_group' attribute to link related information about the same diagnosis.
        Extract entities in the order they appear in the text.
        """
        
        return self._extract_with_retry(text, prompt_description, examples, 'diagnoses')
    
    def extract_vital_signs(self, text: str) -> List[Dict]:
        """Extract vital signs measurements.
        
        Args:
            text: Consultation transcript text
            
        Returns:
            List of vital sign dictionaries
        """
        examples_config = self.few_shot_examples.get('vital_signs', [])
        examples = self._convert_to_langextract_examples(examples_config)
        
        prompt_description = """
        Extract vital signs measurements including temperature, blood pressure, heart rate, 
        oxygen saturation, and respiratory rate.
        Extract entities in the order they appear in the text.
        """
        
        return self._extract_with_retry(text, prompt_description, examples, 'vital_signs')
    
    def extract_physical_exam(self, text: str) -> List[Dict]:
        """Extract physical examination findings.
        
        Args:
            text: Consultation transcript text
            
        Returns:
            List of physical exam dictionaries with grouping attributes
        """
        examples_config = self.few_shot_examples.get('physical_exam', [])
        examples = self._convert_to_langextract_examples(examples_config)
        
        prompt_description = """
        Extract physical examination findings including examination type, anatomical site, findings, and severity.
        Use 'exam_group' attribute to link related information about the same examination.
        Extract entities in the order they appear in the text.
        """
        
        return self._extract_with_retry(text, prompt_description, examples, 'physical_exam')
    
    def extract_red_flags(self, text: str) -> List[Dict]:
        """Extract warning signs.
        
        Args:
            text: Consultation transcript text
            
        Returns:
            List of red flag dictionaries with grouping attributes
        """
        examples_config = self.few_shot_examples.get('red_flags', [])
        examples = self._convert_to_langextract_examples(examples_config)
        
        prompt_description = """
        Extract red flags and warning signs including warning description, warning type, and severity.
        Use 'warning_group' attribute to link related information about the same warning.
        Extract entities in the order they appear in the text.
        """
        
        return self._extract_with_retry(text, prompt_description, examples, 'red_flags')
    
    def extract_follow_up(self, text: str) -> List[Dict]:
        """Extract follow-up plans.
        
        Args:
            text: Consultation transcript text
            
        Returns:
            List of follow-up dictionaries with grouping attributes
        """
        examples_config = self.few_shot_examples.get('follow_up', [])
        examples = self._convert_to_langextract_examples(examples_config)
        
        prompt_description = """
        Extract follow-up plan information including follow-up type, timing, condition, action, and priority.
        Use 'followup_group' attribute to link related information about the same follow-up item.
        Extract entities in the order they appear in the text.
        """
        
        return self._extract_with_retry(text, prompt_description, examples, 'follow_up')
    
    def extract_all(self, text: str) -> Dict[str, List[Dict]]:
        """Extract all entity types in one pass.
        
        Args:
            text: Consultation transcript text
            
        Returns:
            Dictionary mapping entity type to list of extracted entities
        """
        logger.info("Starting extraction of all entity types")
        
        results = {}
        
        try:
            results['symptoms'] = self.extract_symptoms(text)
        except ExtractionError as e:
            logger.warning(f"Symptom extraction failed: {e}")
            results['symptoms'] = []
        
        try:
            results['medications'] = self.extract_medications(text)
        except ExtractionError as e:
            logger.warning(f"Medication extraction failed: {e}")
            results['medications'] = []
        
        try:
            results['diagnoses'] = self.extract_diagnoses(text)
        except ExtractionError as e:
            logger.warning(f"Diagnosis extraction failed: {e}")
            results['diagnoses'] = []
        
        try:
            results['vital_signs'] = self.extract_vital_signs(text)
        except ExtractionError as e:
            logger.warning(f"Vital signs extraction failed: {e}")
            results['vital_signs'] = []
        
        try:
            results['physical_exam'] = self.extract_physical_exam(text)
        except ExtractionError as e:
            logger.warning(f"Physical exam extraction failed: {e}")
            results['physical_exam'] = []
        
        try:
            results['red_flags'] = self.extract_red_flags(text)
        except ExtractionError as e:
            logger.warning(f"Red flags extraction failed: {e}")
            results['red_flags'] = []
        
        try:
            results['follow_up'] = self.extract_follow_up(text)
        except ExtractionError as e:
            logger.warning(f"Follow-up extraction failed: {e}")
            results['follow_up'] = []
        
        total_entities = sum(len(entities) for entities in results.values())
        logger.info(f"Extraction complete. Total entities extracted: {total_entities}")
        
        return results
