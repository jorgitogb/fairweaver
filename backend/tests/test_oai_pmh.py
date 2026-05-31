from unittest.mock import patch
import pytest
from oai_pmh import harvest, list_sets
from sickle.oaiexceptions import NoRecordsMatch, NoSetHierarchy


class FakeHeader:
    def __init__(self, identifier, datestamp, set_spec, deleted=False):
        self.identifier = identifier
        self.datestamp = datestamp
        self.setSpecs = set_spec
        self.deleted = deleted


class FakeRecord:
    def __init__(self, identifier, datestamp, set_spec, metadata, deleted=False):
        self.header = FakeHeader(identifier, datestamp, set_spec, deleted=deleted)
        if not deleted:
            self.metadata = metadata


@pytest.fixture
def mock_sickle():
    with patch("oai_pmh.Sickle") as mock:
        yield mock


class TestHarvest:
    def test_returns_records(self, mock_sickle):
        fake_records = [
            FakeRecord(
                identifier="oai:test:1",
                datestamp="2023-01-01",
                set_spec=["public"],
                metadata={
                    "title": ["Test Dataset"],
                    "creator": ["Author One"],
                    "date": ["2023"],
                },
            ),
            FakeRecord(
                identifier="oai:test:2",
                datestamp="2023-06-15",
                set_spec=["public", "restricted"],
                metadata={
                    "title": ["Dataset Two"],
                    "creator": ["Author Two"],
                    "date": ["2023"],
                },
            ),
        ]
        instance = mock_sickle.return_value
        instance.ListRecords.return_value = iter(fake_records)

        result = harvest(
            base_url="https://example.org/oai",
            metadata_prefix="oai_dc",
        )

        assert result["metadata_format"] == "oai_dc"
        assert result["total"] == 2
        assert len(result["records"]) == 2

        r0 = result["records"][0]
        assert r0["identifier"] == "oai:test:1"
        assert r0["datestamp"] == "2023-01-01"
        assert r0["set_spec"] == ["public"]
        assert r0["metadata"]["title"] == ["Test Dataset"]
        assert r0["metadata_format"] == "oai_dc"

        r1 = result["records"][1]
        assert r1["identifier"] == "oai:test:2"
        assert r1["datestamp"] == "2023-06-15"
        assert r1["set_spec"] == ["public", "restricted"]

    def test_skips_deleted_records(self, mock_sickle):
        fake_records = [
            FakeRecord(
                identifier="oai:live:1",
                datestamp="2023-01-01",
                set_spec=["public"],
                metadata={"title": ["Live Dataset"]},
            ),
            FakeRecord(
                identifier="oai:dead:1",
                datestamp="2022-01-01",
                set_spec=["public"],
                metadata=None,
                deleted=True,
            ),
            FakeRecord(
                identifier="oai:live:2",
                datestamp="2023-06-15",
                set_spec=["public"],
                metadata={"title": ["Another Live"]},
            ),
        ]
        instance = mock_sickle.return_value
        instance.ListRecords.return_value = iter(fake_records)

        result = harvest(
            base_url="https://example.org/oai",
            metadata_prefix="oai_dc",
        )

        assert result["total"] == 2
        ids = [r["identifier"] for r in result["records"]]
        assert "oai:dead:1" not in ids
        assert "oai:live:1" in ids
        assert "oai:live:2" in ids

    def test_empty_result(self, mock_sickle):
        instance = mock_sickle.return_value
        instance.ListRecords.return_value = iter([])

        result = harvest(
            base_url="https://example.org/oai",
            metadata_prefix="oai_dc",
        )

        assert result["total"] == 0
        assert result["records"] == []

    def test_passes_params_to_sickle(self, mock_sickle):
        instance = mock_sickle.return_value
        instance.ListRecords.return_value = iter([])

        harvest(
            base_url="https://example.org/oai",
            metadata_prefix="oai_dc",
            set="public",
            from_date="2020-01-01",
            until_date="2024-12-31",
        )

        _, kwargs = instance.ListRecords.call_args
        assert kwargs["metadataPrefix"] == "oai_dc"
        assert kwargs["set"] == "public"
        assert kwargs["from"] == "2020-01-01"
        assert kwargs["until"] == "2024-12-31"

    def test_network_error(self, mock_sickle):
        instance = mock_sickle.return_value
        instance.ListRecords.side_effect = ConnectionError("Connection refused")

        with pytest.raises(ConnectionError, match="Connection refused"):
            harvest(
                base_url="https://example.org/oai",
                metadata_prefix="oai_dc",
            )

    def test_no_records_match(self, mock_sickle):
        instance = mock_sickle.return_value
        instance.ListRecords.side_effect = NoRecordsMatch("No records match")

        result = harvest(
            base_url="https://example.org/oai",
            metadata_prefix="oai_dc",
        )

        assert result["total"] == 0
        assert result["records"] == []
        assert result["metadata_format"] == "oai_dc"


class FakeSet:
    def __init__(self, spec, name):
        self.setSpec = spec
        self.setName = name


class TestListSets:
    def test_returns_sets(self, mock_sickle):
        fake_sets = [
            FakeSet("public", "Public datasets"),
            FakeSet("restricted", "Restricted datasets"),
        ]
        instance = mock_sickle.return_value
        instance.ListSets.return_value = iter(fake_sets)

        result = list_sets(base_url="https://example.org/oai")

        assert len(result) == 2
        assert result[0] == {"spec": "public", "name": "Public datasets"}
        assert result[1] == {"spec": "restricted", "name": "Restricted datasets"}

    def test_empty_sets(self, mock_sickle):
        instance = mock_sickle.return_value
        instance.ListSets.return_value = iter([])

        result = list_sets(base_url="https://example.org/oai")

        assert result == []

    def test_no_set_hierarchy(self, mock_sickle):
        instance = mock_sickle.return_value
        instance.ListSets.side_effect = NoSetHierarchy("No sets")

        result = list_sets(base_url="https://example.org/oai")

        assert result == []
