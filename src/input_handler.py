"""Input handling for GP Consultation Extractor.

This module handles reading and validating Markdown consultation transcript files.
"""

from pathlib import Path
from typing import Optional


class InputError(Exception):
    """Raised when input file cannot be read or is invalid."""
    pass


class InputHandler:
    """Handles reading and validating consultation transcript files."""
    
    def read_transcript(self, file_path: str) -> str:
        """Read Markdown file and return content.
        
        Args:
            file_path: Path to Markdown consultation transcript file
            
        Returns:
            File content as string
            
        Raises:
            InputError: If file cannot be read or doesn't exist
        """
        path = Path(file_path)
        
        if not path.exists():
            raise InputError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise InputError(f"Path is not a file: {file_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                raise InputError(f"File is empty: {file_path}")
            
            return content
            
        except UnicodeDecodeError as e:
            raise InputError(f"File encoding error (expected UTF-8): {file_path}") from e
        except IOError as e:
            raise InputError(f"Failed to read file: {file_path}") from e
    
    def validate_format(self, content: str) -> bool:
        """Validate that content is properly formatted consultation transcript.
        
        Performs basic validation to ensure the content appears to be a consultation
        transcript with dialogue structure.
        
        Args:
            content: Transcript content to validate
            
        Returns:
            True if content appears valid
            
        Raises:
            InputError: If content format is invalid
        """
        if not content or not content.strip():
            raise InputError("Content is empty")
        
        # Check minimum length (at least 50 characters for a meaningful consultation)
        if len(content.strip()) < 50:
            raise InputError("Content is too short to be a valid consultation transcript")
        
        # Check for dialogue indicators (common patterns in consultation transcripts)
        # Look for patterns like "Patient:", "GP:", "Doctor:", or dialogue markers
        content_lower = content.lower()
        has_dialogue = any(marker in content_lower for marker in [
            'patient:', 'gp:', 'doctor:', 'dr:', 'physician:',
            '**patient', '**gp', '**doctor', '**dr'
        ])
        
        if not has_dialogue:
            # If no explicit dialogue markers, check for conversational structure
            # (questions, statements, etc.)
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            if len(lines) < 3:
                raise InputError(
                    "Content does not appear to be a consultation transcript "
                    "(no dialogue markers or conversational structure found)"
                )
        
        return True
