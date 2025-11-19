"""Unit tests for CSVExporter."""

# pylint: disable=protected-access

import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from csv_exporter import CSVExporter


class TestCSVExporter:
    """Test cases for CSVExporter class."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def exporter(self, temp_output_dir):
        """Create a CSVExporter instance for testing."""
        return CSVExporter(temp_output_dir)

    def test_initialization(self, temp_output_dir):
        """Test CSVExporter initialization."""
        exporter = CSVExporter(temp_output_dir)

        assert exporter.output_dir == Path(temp_output_dir)
        assert exporter.output_dir.exists()
        assert not exporter.exported_files

    def test_export_table_with_data(self, exporter):
        """Test exporting a table with data."""
        df = pd.DataFrame(
            {"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"], "value": [10.5, 20.3, 30.1]}
        )

        filepath = exporter.export_table(df, "test_table")

        # Check file was created
        assert os.path.exists(filepath)
        assert filepath.endswith("test_table.csv")

        # Check file content
        df_read = pd.read_csv(filepath)
        assert len(df_read) == 3
        assert list(df_read.columns) == ["id", "name", "value"]

        # Check exported_files tracking
        assert len(exporter.exported_files) == 1
        assert exporter.exported_files[0]["table"] == "test_table"
        assert exporter.exported_files[0]["row_count"] == 3

    def test_export_table_empty(self, exporter):
        """Test exporting an empty table."""
        df = pd.DataFrame(columns=["id", "name", "value"])

        filepath = exporter.export_table(df, "empty_table")

        # Check file was created with headers
        assert os.path.exists(filepath)

        df_read = pd.read_csv(filepath)
        assert len(df_read) == 0
        assert list(df_read.columns) == ["id", "name", "value"]

        # Check exported_files tracking
        assert exporter.exported_files[0]["row_count"] == 0

    def test_export_table_with_null_values(self, exporter):
        """Test exporting table with NULL values."""
        df = pd.DataFrame(
            {"id": [1, 2, 3], "name": ["Alice", None, "Charlie"], "value": [10.5, None, 30.1]}
        )

        filepath = exporter.export_table(df, "null_table")

        # Read and check NULL handling
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        # NULL values should be empty strings
        assert ",," in content  # Empty field for NULL

    def test_export_table_with_special_characters(self, exporter):
        """Test exporting table with special characters."""
        df = pd.DataFrame(
            {
                "id": [1, 2],
                "text": ["Hello, World!", "Line1\nLine2"],
                "quote": ['He said "hello"', "It's fine"],
            }
        )

        filepath = exporter.export_table(df, "special_chars")

        # Read back and verify
        df_read = pd.read_csv(filepath)
        assert len(df_read) == 2
        assert df_read.iloc[0]["text"] == "Hello, World!"

    def test_serialize_jsonb_columns(self, exporter):
        """Test JSONB column serialization."""
        df = pd.DataFrame(
            {
                "id": [1, 2],
                "data": [
                    {"key": "value1", "nested": {"a": 1}},
                    {"key": "value2", "nested": {"b": 2}},
                ],
                "list_data": [["item1", "item2"], ["item3", "item4"]],
                "text": ["normal", "text"],
            }
        )

        df_serialized = exporter._serialize_jsonb_columns(df)

        # Check dict column is serialized
        assert isinstance(df_serialized.iloc[0]["data"], str)
        data_dict = json.loads(df_serialized.iloc[0]["data"])
        assert data_dict["key"] == "value1"

        # Check list column is serialized
        assert isinstance(df_serialized.iloc[0]["list_data"], str)
        list_data = json.loads(df_serialized.iloc[0]["list_data"])
        assert list_data == ["item1", "item2"]

        # Check text column is unchanged
        assert df_serialized.iloc[0]["text"] == "normal"

    def test_serialize_jsonb_with_null(self, exporter):
        """Test JSONB serialization with NULL values."""
        df = pd.DataFrame({"id": [1, 2, 3], "data": [{"key": "value"}, None, {}]})

        df_serialized = exporter._serialize_jsonb_columns(df)

        # First row should be serialized
        assert isinstance(df_serialized.iloc[0]["data"], str)

        # Second row (NULL) should be empty string
        assert df_serialized.iloc[1]["data"] == ""

        # Third row (empty dict) should be serialized
        assert df_serialized.iloc[2]["data"] == "{}"

    def test_export_all(self, exporter):
        """Test exporting multiple tables."""
        mapped_data = {
            "symptoms": pd.DataFrame(
                {"symptom_id": ["uuid1", "uuid2"], "symptom_name": ["headache", "fever"]}
            ),
            "medications": pd.DataFrame(
                {"prescription_id": ["uuid3"], "medication_name": ["Aspirin"]}
            ),
            "diagnoses": pd.DataFrame({"diagnosis_id": ["uuid4"], "diagnosis_name": ["flu"]}),
        }

        file_paths = exporter.export_all(mapped_data)

        # Check all files were created
        assert len(file_paths) == 3
        assert all(os.path.exists(fp) for fp in file_paths)

        # Check exported_files tracking
        assert len(exporter.exported_files) == 3

        # Verify file names
        file_names = [Path(fp).name for fp in file_paths]
        assert "symptoms.csv" in file_names
        assert "medications.csv" in file_names
        assert "diagnoses.csv" in file_names

    def test_create_manifest(self, exporter):
        """Test manifest file creation."""
        # Export some tables first
        mapped_data = {
            "symptoms": pd.DataFrame({"symptom_id": ["uuid1"], "symptom_name": ["headache"]}),
            "medications": pd.DataFrame(
                {"prescription_id": ["uuid2"], "medication_name": ["Aspirin"]}
            ),
        }
        exporter.export_all(mapped_data)

        # Create manifest
        consultation_session_id = "test-uuid-123"
        total_entities = 42
        processing_time = 15.3

        manifest_path = exporter.create_manifest(
            consultation_session_id, total_entities, processing_time
        )

        # Check manifest file exists
        assert os.path.exists(manifest_path)
        assert manifest_path.endswith("manifest.json")

        # Read and verify manifest content
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["consultation_session_id"] == consultation_session_id
        assert manifest["total_entities_extracted"] == total_entities
        assert manifest["processing_time_seconds"] == 15.3
        assert "extraction_timestamp" in manifest
        assert "files" in manifest
        assert len(manifest["files"]) == 2

        # Check file entries
        file_tables = [f["table"] for f in manifest["files"]]
        assert "symptoms" in file_tables
        assert "medications" in file_tables

    def test_manifest_with_no_exports(self, exporter):
        """Test manifest creation with no prior exports."""
        manifest_path = exporter.create_manifest("uuid", 0, 1.0)

        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["files"] == []
        assert manifest["total_entities_extracted"] == 0

    def test_utf8_encoding(self, exporter):
        """Test UTF-8 encoding for international characters."""
        df = pd.DataFrame({"id": [1, 2, 3], "text": ["Hello", "Héllo", "你好"]})

        filepath = exporter.export_table(df, "utf8_test")

        # Read with UTF-8 encoding
        df_read = pd.read_csv(filepath, encoding="utf-8")
        assert df_read.iloc[1]["text"] == "Héllo"
        assert df_read.iloc[2]["text"] == "你好"

    def test_csv_format_compliance(self, exporter):
        """Test CSV format compliance."""
        df = pd.DataFrame({"id": [1], "text": ["value"]})

        filepath = exporter.export_table(df, "format_test")

        # Check file format
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()

        # Should have header + 1 data row
        assert len(lines) == 2

        # Header should be comma-separated
        assert "id,text" in lines[0]

        # No index column
        assert not lines[0].startswith("Unnamed")

    def test_multiple_exports_same_exporter(self, exporter):
        """Test multiple exports with same exporter instance."""
        df1 = pd.DataFrame({"id": [1]})
        df2 = pd.DataFrame({"id": [2]})

        exporter.export_table(df1, "table1")
        exporter.export_table(df2, "table2")

        # Both should be tracked
        assert len(exporter.exported_files) == 2
        assert exporter.exported_files[0]["table"] == "table1"
        assert exporter.exported_files[1]["table"] == "table2"
