"""Clinical entity extraction using LangExtract.

This module extracts structured clinical entities from consultation transcripts
using LangExtract with few-shot learning examples.
"""

# pylint: disable=too-many-branches,too-many-locals,too-many-statements,too-many-nested-blocks,too-many-return-statements,broad-exception-caught,too-few-public-methods,inconsistent-return-statements

import json
import logging
import re
import time
from pathlib import Path
from types import SimpleNamespace

import yaml

try:
    import langextract as lx
except ImportError:
    # For testing without langextract installed
    lx = None

from .llm_provider import LLMProviderManager

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Raised when entity extraction fails."""


class ClinicalEntityExtractor:
    """Extracts structured clinical entities using LangExtract."""

    def __init__(
        self,
        llm_provider: LLMProviderManager,
        few_shot_config_path: str = "config/few_shot_examples.yaml",
    ):
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
        # Default retry attempts - can be overridden
        self.retry_attempts = 1
        self.retry_delay = 1  # seconds

    def _load_few_shot_examples(self, config_path: str) -> dict:
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
            with open(path, encoding="utf-8") as f:
                examples = yaml.safe_load(f)

            if not examples:
                raise ExtractionError("Few-shot examples file is empty")

            return examples
        except yaml.YAMLError as e:
            raise ExtractionError(f"Failed to parse few-shot examples: {e}") from e
        except OSError as e:
            raise ExtractionError(f"Failed to load few-shot examples: {e}") from e

    def _convert_to_langextract_examples(self, examples_config: list[dict]) -> list:
        """Convert YAML examples to LangExtract ExampleData format.

        Args:
            examples_config: List of example dictionaries from YAML

        Returns:
            List of LangExtract ExampleData objects
        """
        langextract_examples = []

        for example in examples_config:
            text = example.get("text", "")
            extractions_config = example.get("extractions", [])

            extractions = []
            for ext in extractions_config:
                extraction = lx.data.Extraction(
                    extraction_class=ext.get("class"),
                    extraction_text=ext.get("text"),
                    attributes=ext.get("attributes", {}),
                )
                extractions.append(extraction)

            example_data = lx.data.ExampleData(text=text, extractions=extractions)
            langextract_examples.append(example_data)

        return langextract_examples

    def _extract_with_retry(
        self, text: str, prompt_description: str, examples: list, entity_type: str
    ) -> list[dict]:
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
                if provider == "gemini":
                    api_key = credentials["api_key"]
                    model_id = credentials.get("model", "gemini-2.5-pro")

                    result = lx.extract(
                        text_or_documents=text,
                        prompt_description=prompt_description,
                        examples=examples,
                        api_key=api_key,
                        model_id=model_id,
                    )

                elif provider == "bedrock":
                    model_id = credentials.get("model_id")

                    # Use langextract-bedrock plugin for standard Bedrock.
                    # For custom endpoints, use manual API approach and convert to
                    # LangExtract format.

                    if credentials.get("use_custom_endpoint"):
                        # Custom endpoint: Manual API approach since the plugin does not
                        # support custom endpoints. Build the extraction request manually
                        # and call the custom endpoint, then convert response to
                        # LangExtract result format.

                        # Build user message content with text, prompt, and examples
                        user_content_parts = []

                        # Add the prompt description
                        if prompt_description:
                            user_content_parts.append(f"Task: {prompt_description.strip()}")

                        # Add few-shot examples if available
                        if examples:
                            user_content_parts.append("\nExamples:")
                            for ex in examples:
                                example_text = (
                                    ex.text if hasattr(ex, "text") else ex.get("text", "")
                                )
                                extractions_list = []
                                if hasattr(ex, "extractions"):
                                    for e in ex.extractions:
                                        ext_class = getattr(e, "extraction_class", "")
                                        ext_text = getattr(e, "extraction_text", "")
                                        extractions_list.append(f"  - {ext_class}: {ext_text}")
                                elif isinstance(ex, dict) and "extractions" in ex:
                                    for e in ex["extractions"]:
                                        ext_class = e.get("class") or e.get("extraction_class", "")
                                        ext_text = e.get("text") or e.get("extraction_text", "")
                                        extractions_list.append(f"  - {ext_class}: {ext_text}")

                                if extractions_list:
                                    user_content_parts.append(f"\nExample text: {example_text}")
                                    user_content_parts.append("Extractions:")
                                    user_content_parts.extend(extractions_list)

                        # Add the actual text to extract from
                        user_content_parts.append(f"\n\nText to extract from:\n{text}")

                        instruction_text = (
                            "\n\nIMPORTANT: Return your response as a JSON object with an "
                            "'extractions' array. Each extraction should have 'class', 'text', "
                            "and optionally 'attributes' fields."
                        )
                        user_content_parts.append(instruction_text)

                        user_message_content = "\n".join(user_content_parts)

                        # Construct messages array
                        messages = [{"role": "user", "content": user_message_content}]

                        # Extract system content for top-level parameter
                        base_system = (
                            prompt_description.strip()
                            if prompt_description
                            else "Extract structured entities from the provided text."
                        )
                        system_content = (
                            f"{base_system}\n\nReturn your response as valid JSON with an "
                            "'extractions' array. Each extraction must have 'class' and 'text' "
                            "fields, and optionally 'attributes'."
                        )

                        payload = {
                            "team_id": credentials.get("team_id"),
                            "api_token": credentials.get("api_token") or credentials.get("api_key"),
                            "model": model_id,
                            "system": system_content,
                            "messages": messages,
                        }

                        # Validate required fields
                        if not payload.get("team_id"):
                            raise ExtractionError(
                                "team_id is required for custom Bedrock endpoint. "
                                "Set BEDROCK_TEAM_ID environment variable."
                            )
                        if not payload.get("api_token"):
                            raise ExtractionError(
                                "api_token is required for custom Bedrock endpoint. "
                                "Set BEDROCK_API_KEY environment variable."
                            )
                        if not payload.get("model"):
                            raise ExtractionError(
                                "model is required for custom Bedrock endpoint. "
                                "Set MODEL_ID environment variable."
                            )

                        # Invoke custom endpoint
                        response = self.llm_provider.invoke_custom_endpoint(payload)

                        parsed_response = self._parse_bedrock_response(response, entity_type)

                        result = self._build_langextract_result(parsed_response)
                    else:
                        # Standard Bedrock: Use langextract-bedrock plugin
                        # Plugin auto-detects Bedrock models via model_id and uses boto3 credentials
                        result = lx.extract(
                            text_or_documents=text,
                            prompt_description=prompt_description,
                            examples=examples,
                            model_id=model_id,  # e.g., "anthropic.claude-sonnet-4-5-20250929-v1:0"
                            # AWS credentials from boto3 default chain (env vars,
                            # ~/.aws/credentials, IAM role)
                        )

                else:
                    raise ExtractionError(f"Unsupported provider: {provider}")

                logger.info("Successfully extracted %s entities", entity_type)
                # Reset retry delay on success
                self.retry_delay = 1
                return self._parse_extraction_result(result)

            except ExtractionError:
                # Allow ExtractionError to propagate without retry
                raise
            except (OSError, ValueError, RuntimeError) as e:
                is_last_attempt = attempt >= self.retry_attempts

                if not is_last_attempt:
                    logger.warning(
                        "Extraction attempt %d failed for %s: %s. Retrying in %ds...",
                        attempt + 1,
                        entity_type,
                        e,
                        self.retry_delay,
                    )
                    time.sleep(self.retry_delay)
                    self.retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(
                        "Extraction failed for %s after %d attempts: %s",
                        entity_type,
                        self.retry_attempts + 1,
                        e,
                    )
                    raise ExtractionError(f"Failed to extract {entity_type}: {e}") from e
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch any other unexpected exceptions and wrap them
                # This handles cases where API libraries raise generic exceptions
                is_last_attempt = attempt >= self.retry_attempts

                if not is_last_attempt:
                    logger.warning(
                        "Extraction attempt %d failed for %s (unexpected error): %s. "
                        "Retrying in %ds...",
                        attempt + 1,
                        entity_type,
                        e,
                        self.retry_delay,
                    )
                    time.sleep(self.retry_delay)
                    self.retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(
                        "Extraction failed for %s after %d attempts (unexpected error): %s",
                        entity_type,
                        self.retry_attempts + 1,
                        e,
                    )
                    raise ExtractionError(f"Failed to extract {entity_type}: {e}") from e

    def _build_langextract_result(self, extractions_data: dict | list) -> SimpleNamespace:
        """Convert custom endpoint response into LangExtract-compatible result."""
        result = SimpleNamespace(extractions=[])
        extractions_list = (
            extractions_data.get("extractions", [])
            if isinstance(extractions_data, dict)
            else extractions_data
        )

        if isinstance(extractions_list, list):
            for extraction in extractions_list:
                if isinstance(extraction, dict):
                    result.extractions.append(
                        lx.data.Extraction(
                            extraction_class=extraction.get("class", ""),
                            extraction_text=extraction.get("text", ""),
                            attributes=extraction.get("attributes", {}),
                        )
                    )
        return result

    def _parse_bedrock_response(self, response: dict, entity_type: str) -> dict:
        """Parse Bedrock custom endpoint response.

        Claude Messages API returns responses in this format:
        {
            "content": [
                {"type": "text", "text": "..."}
            ],
            ...
        }

        The text content may be JSON that needs to be parsed.

        Args:
            response: Raw response from Bedrock endpoint
            entity_type: Type of entity being extracted (for logging)

        Returns:
            Parsed result in LangExtract-compatible format
        """
        # Log the response structure for debugging (first 500 chars to avoid log spam)
        logger.info(
            "Bedrock response structure for %s: keys=%s, type=%s",
            entity_type,
            list(response.keys()) if isinstance(response, dict) else "N/A",
            type(response).__name__,
        )
        if isinstance(response, dict):
            logger.debug(
                "Full Bedrock response for %s: %s",
                entity_type,
                json.dumps(response, indent=2)[:1000],
            )

        # Check if response has content blocks (Claude Messages API format)
        if isinstance(response, dict) and "content" in response:
            content_blocks = response["content"]
            if isinstance(content_blocks, list) and len(content_blocks) > 0:
                # Extract text from content blocks
                text_content = ""
                for block in content_blocks:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_content += block.get("text", "")

                if text_content:
                    # Try to parse as JSON (LangExtract format)
                    try:
                        # Try to extract JSON from text if it's wrapped in markdown code blocks
                        json_text = text_content
                        if "```json" in text_content:
                            # Extract JSON from markdown code block
                            start = text_content.find("```json") + 7
                            end = text_content.find("```", start)
                            if end > start:
                                json_text = text_content[start:end].strip()
                        elif "```" in text_content:
                            # Extract from generic code block
                            start = text_content.find("```") + 3
                            end = text_content.find("```", start)
                            if end > start:
                                json_text = text_content[start:end].strip()

                        parsed = json.loads(json_text)
                        if isinstance(parsed, dict):
                            # Ensure it has extractions key
                            if "extractions" not in parsed:
                                # If the parsed dict itself looks like an extraction, wrap it
                                if "class" in parsed or "text" in parsed:
                                    return {"extractions": [parsed]}
                                # Otherwise wrap the whole dict as a single extraction
                                return {"extractions": [parsed]}
                            return parsed
                        if isinstance(parsed, list):
                            # If it's a list, assume it's a list of extractions
                            return {"extractions": parsed}
                    except json.JSONDecodeError as e:
                        # If not JSON, might be plain text - log for debugging
                        logger.warning(
                            "Response text is not valid JSON for %s. Error: %s. Text preview: %s",
                            entity_type,
                            str(e),
                            text_content[:300],
                        )
                        # Try to extract JSON-like structure from text
                        # Look for JSON-like patterns
                        json_match = re.search(
                            r'\{[^{}]*"extractions"[^{}]*\[.*?\]', text_content, re.DOTALL
                        )
                        if json_match:
                            try:
                                parsed = json.loads(json_match.group(0))
                                if isinstance(parsed, dict) and "extractions" in parsed:
                                    return parsed
                            except json.JSONDecodeError:
                                pass
                        # Return empty result structure
                        return {"extractions": []}

        # Check if response already has extractions key (direct LangExtract format)
        if isinstance(response, dict) and "extractions" in response:
            return response

        # Check if response is a direct list of extractions
        if isinstance(response, list):
            return {"extractions": response}

        # If response has other structure, try to extract from common fields
        if isinstance(response, dict):
            # Check for common alternative keys
            for key in ["data", "result", "output", "response"]:
                if key in response:
                    nested = response[key]
                    if isinstance(nested, dict) and "extractions" in nested:
                        return nested
                    if isinstance(nested, list):
                        return {"extractions": nested}

        # Log the full response structure for debugging
        logger.warning(
            "Unexpected response format for %s. Response keys: %s, Response type: %s",
            entity_type,
            list(response.keys()) if isinstance(response, dict) else "N/A",
            type(response).__name__,
        )

        # Return empty result structure
        return {"extractions": []}

    def _parse_extraction_result(self, result) -> list[dict]:
        """Parse LangExtract result into list of dictionaries.

        Handles both LangExtract result objects (with .extractions attribute)
        and dict responses from custom endpoints (with 'extractions' key).

        Args:
            result: LangExtract extraction result (object or dict)

        Returns:
            List of extracted entities as dictionaries
        """
        entities = []

        # Handle LangExtract result object (has .extractions attribute)
        if hasattr(result, "extractions"):
            for extraction in result.extractions:
                entity = {
                    "class": extraction.extraction_class,
                    "text": extraction.extraction_text,
                    "attributes": extraction.attributes
                    if hasattr(extraction, "attributes")
                    else {},
                }
                entities.append(entity)

        # Handle dict response from custom endpoint (has 'extractions' key)
        elif isinstance(result, dict) and "extractions" in result:
            for extraction in result["extractions"]:
                # Extraction can be a dict or an object
                if isinstance(extraction, dict):
                    entity = {
                        "class": extraction.get("class") or extraction.get("extraction_class", ""),
                        "text": extraction.get("text") or extraction.get("extraction_text", ""),
                        "attributes": extraction.get("attributes", {}),
                    }
                else:
                    # Extraction is an object (fallback)
                    entity = {
                        "class": getattr(
                            extraction, "extraction_class", getattr(extraction, "class", "")
                        ),
                        "text": getattr(
                            extraction, "extraction_text", getattr(extraction, "text", "")
                        ),
                        "attributes": getattr(extraction, "attributes", {})
                        if hasattr(extraction, "attributes")
                        else {},
                    }
                entities.append(entity)

        # Log warning if result format is unexpected
        if not entities:
            logger.warning(
                "No extractions found in result. Result type: %s, Has extractions attr: %s, "
                "Is dict with extractions key: %s",
                type(result).__name__,
                hasattr(result, "extractions") if not isinstance(result, dict) else False,
                isinstance(result, dict) and "extractions" in result,
            )

        return entities

    def extract_symptoms(self, text: str) -> list[dict]:
        """Extract symptoms with attributes.

        Args:
            text: Consultation transcript text

        Returns:
            List of symptom dictionaries with grouping attributes
        """
        examples_config = self.few_shot_examples.get("symptoms", [])
        examples = self._convert_to_langextract_examples(examples_config)

        prompt_description = """
        Extract symptom information including symptom name, severity, duration,
        onset, and temporal pattern.
        Use 'symptom_group' attribute to link related information about the same symptom.
        Extract entities in the order they appear in the text.
        """

        return self._extract_with_retry(text, prompt_description, examples, "symptoms")

    def extract_medications(self, text: str) -> list[dict]:
        """Extract medications with grouping.

        Args:
            text: Consultation transcript text

        Returns:
            List of medication dictionaries with grouping attributes
        """
        examples_config = self.few_shot_examples.get("medications", [])
        examples = self._convert_to_langextract_examples(examples_config)

        prompt_description = """
        Extract medication information including medication name, dosage, route,
        frequency, duration, and indication.
        Use 'medication_group' attribute to group related information about the same medication.
        Extract entities in the order they appear in the text.
        """

        return self._extract_with_retry(text, prompt_description, examples, "medications")

    def extract_diagnoses(self, text: str) -> list[dict]:
        """Extract diagnoses with certainty.

        Args:
            text: Consultation transcript text

        Returns:
            List of diagnosis dictionaries with grouping attributes
        """
        examples_config = self.few_shot_examples.get("diagnoses", [])
        examples = self._convert_to_langextract_examples(examples_config)

        prompt_description = """
        Extract diagnosis information including diagnosis name, diagnostic certainty,
        and clinical features.
        Use 'diagnosis_group' attribute to link related information about the same diagnosis.
        Extract entities in the order they appear in the text.
        """

        return self._extract_with_retry(text, prompt_description, examples, "diagnoses")

    def extract_vital_signs(self, text: str) -> list[dict]:
        """Extract vital signs measurements.

        Args:
            text: Consultation transcript text

        Returns:
            List of vital sign dictionaries
        """
        examples_config = self.few_shot_examples.get("vital_signs", [])
        examples = self._convert_to_langextract_examples(examples_config)

        prompt_description = """
        Extract vital signs measurements including temperature, blood pressure,
        heart rate, oxygen saturation, and respiratory rate.
        Extract entities in the order they appear in the text.
        """

        return self._extract_with_retry(text, prompt_description, examples, "vital_signs")

    def extract_physical_exam(self, text: str) -> list[dict]:
        """Extract physical examination findings.

        Args:
            text: Consultation transcript text

        Returns:
            List of physical exam dictionaries with grouping attributes
        """
        examples_config = self.few_shot_examples.get("physical_exam", [])
        examples = self._convert_to_langextract_examples(examples_config)

        prompt_description = """
        Extract physical examination findings including examination type,
        anatomical site, findings, and severity.
        Use 'exam_group' attribute to link related information about the same examination.
        Extract entities in the order they appear in the text.
        """

        return self._extract_with_retry(text, prompt_description, examples, "physical_exam")

    def extract_red_flags(self, text: str) -> list[dict]:
        """Extract warning signs.

        Args:
            text: Consultation transcript text

        Returns:
            List of red flag dictionaries with grouping attributes
        """
        examples_config = self.few_shot_examples.get("red_flags", [])
        examples = self._convert_to_langextract_examples(examples_config)

        prompt_description = """
        Extract red flags and warning signs including warning description,
        warning type, and severity.
        Use 'warning_group' attribute to link related information about the same warning.
        Extract entities in the order they appear in the text.
        """

        return self._extract_with_retry(text, prompt_description, examples, "red_flags")

    def extract_follow_up(self, text: str) -> list[dict]:
        """Extract follow-up plans.

        Args:
            text: Consultation transcript text

        Returns:
            List of follow-up dictionaries with grouping attributes
        """
        examples_config = self.few_shot_examples.get("follow_up", [])
        examples = self._convert_to_langextract_examples(examples_config)

        prompt_description = """
        Extract follow-up plan information including follow-up type, timing,
        condition, action, and priority.
        Use 'followup_group' attribute to link related information about the same follow-up item.
        Extract entities in the order they appear in the text.
        """

        return self._extract_with_retry(text, prompt_description, examples, "follow_up")

    def extract_all(self, text: str) -> dict[str, list[dict]]:
        """Extract all entity types in one pass.

        Args:
            text: Consultation transcript text

        Returns:
            Dictionary mapping entity type to list of extracted entities
        """
        logger.info("Starting extraction of all entity types")

        results = {}

        try:
            results["symptoms"] = self.extract_symptoms(text)
        except ExtractionError as e:
            logger.warning("Symptom extraction failed: %s", e)
            results["symptoms"] = []

        try:
            results["medications"] = self.extract_medications(text)
        except ExtractionError as e:
            logger.warning("Medication extraction failed: %s", e)
            results["medications"] = []

        try:
            results["diagnoses"] = self.extract_diagnoses(text)
        except ExtractionError as e:
            logger.warning("Diagnosis extraction failed: %s", e)
            results["diagnoses"] = []

        try:
            results["vital_signs"] = self.extract_vital_signs(text)
        except ExtractionError as e:
            logger.warning("Vital signs extraction failed: %s", e)
            results["vital_signs"] = []

        try:
            results["physical_exam"] = self.extract_physical_exam(text)
        except ExtractionError as e:
            logger.warning("Physical exam extraction failed: %s", e)
            results["physical_exam"] = []

        try:
            results["red_flags"] = self.extract_red_flags(text)
        except ExtractionError as e:
            logger.warning("Red flags extraction failed: %s", e)
            results["red_flags"] = []

        try:
            results["follow_up"] = self.extract_follow_up(text)
        except ExtractionError as e:
            logger.warning("Follow-up extraction failed: %s", e)
            results["follow_up"] = []

        total_entities = sum(len(entities) for entities in results.values())
        logger.info("Extraction complete. Total entities extracted: %d", total_entities)

        return results
