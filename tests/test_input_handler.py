"""Unit tests for input handling."""

import os
import tempfile

import pytest

from input_handler import InputError, InputHandler


class TestInputHandler:
    """Test cases for InputHandler class."""

    def test_read_transcript_success(self):
        """Test successful file reading."""
        # Create temporary file with sample content
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("**Patient**: I have a headache.\n**GP**: How long have you had it?")
            temp_path = f.name

        try:
            handler = InputHandler()
            content = handler.read_transcript(temp_path)

            assert "Patient" in content
            assert "headache" in content
            assert len(content) > 0
        finally:
            os.unlink(temp_path)

    def test_read_transcript_file_not_found(self):
        """Test file not found error handling."""
        handler = InputHandler()

        with pytest.raises(InputError) as exc_info:
            handler.read_transcript("/nonexistent/file.md")

        assert "not found" in str(exc_info.value).lower()

    def test_read_transcript_empty_file(self):
        """Test empty file error handling."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            temp_path = f.name

        try:
            handler = InputHandler()

            with pytest.raises(InputError) as exc_info:
                handler.read_transcript(temp_path)

            assert "empty" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_path)

    def test_read_transcript_directory_path(self):
        """Test error when path is a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = InputHandler()

            with pytest.raises(InputError) as exc_info:
                handler.read_transcript(temp_dir)

            assert "not a file" in str(exc_info.value).lower()

    def test_read_transcript_encoding_error(self):
        """Test encoding error handling."""
        # Create file with non-UTF-8 encoding
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".md", delete=False) as f:
            # Write invalid UTF-8 bytes
            f.write(b"\xff\xfe Invalid UTF-8")
            temp_path = f.name

        try:
            handler = InputHandler()

            with pytest.raises(InputError) as exc_info:
                handler.read_transcript(temp_path)

            assert "encoding" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_path)

    def test_validate_format_success_with_dialogue_markers(self):
        """Test successful validation with dialogue markers."""
        handler = InputHandler()
        content = """
        **Patient**: I've been experiencing lower back pain for the past three days.
        **GP**: Can you describe the pain? Is it sharp or dull?
        **Patient**: It's a dull, constant ache.
        """

        assert handler.validate_format(content) is True

    def test_validate_format_success_with_alternative_markers(self):
        """Test validation with alternative dialogue markers."""
        handler = InputHandler()
        content = """
        Doctor: What brings you in today?
        Patient: I have a sore throat and fever.
        Doctor: How long have you had these symptoms?
        """

        assert handler.validate_format(content) is True

    def test_validate_format_empty_content(self):
        """Test validation fails with empty content."""
        handler = InputHandler()

        with pytest.raises(InputError) as exc_info:
            handler.validate_format("")

        assert "empty" in str(exc_info.value).lower()

    def test_validate_format_too_short(self):
        """Test validation fails with too short content."""
        handler = InputHandler()

        with pytest.raises(InputError) as exc_info:
            handler.validate_format("Short text")

        assert "too short" in str(exc_info.value).lower()

    def test_validate_format_no_dialogue_structure(self):
        """Test validation fails without dialogue structure."""
        handler = InputHandler()
        content = "This is just a random paragraph without any consultation structure."

        with pytest.raises(InputError) as exc_info:
            handler.validate_format(content)

        assert "consultation transcript" in str(exc_info.value).lower()

    def test_validate_format_with_conversational_structure(self):
        """Test validation passes with conversational structure even without explicit markers."""
        handler = InputHandler()
        content = """
        The patient presents with complaints of persistent cough.
        Duration of symptoms is approximately two weeks.
        No fever or shortness of breath reported.
        Physical examination reveals clear lung sounds.
        Diagnosis: Upper respiratory tract infection.
        """

        # This should pass as it has multiple lines suggesting a consultation
        assert handler.validate_format(content) is True

    def test_read_and_validate_integration(self):
        """Test reading and validating a file end-to-end."""
        content = """
        **Patient**: I've been feeling very tired lately and have frequent headaches.
        **GP**: How long have you been experiencing these symptoms?
        **Patient**: About two weeks now.
        **GP**: Any other symptoms? Fever, nausea, vision changes?
        **Patient**: No, just the tiredness and headaches.
        """

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            handler = InputHandler()
            read_content = handler.read_transcript(temp_path)
            assert handler.validate_format(read_content) is True
        finally:
            os.unlink(temp_path)
