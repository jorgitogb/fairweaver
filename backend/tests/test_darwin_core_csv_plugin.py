import pytest
from formats.darwin_core_csv_plugin import FORMAT_ID, LABEL, EXTENSIONS, load, write


class TestConstants:
    def test_format_id(self):
        assert FORMAT_ID == "darwin_core_csv"

    def test_label(self):
        assert LABEL == "Darwin Core CSV"

    def test_extensions(self):
        assert EXTENSIONS == [".csv"]


SAMPLE_CSV = """scientificName,basisOfRecord,eventDate,institutionCode,collectionCode,catalogNumber,decimalLatitude,decimalLongitude,country,stateProvince,locality,kingdom,phylum,class,order,family,genus,specificEpithet,recordedBy,identifiedBy
Ursus arctos,PRESERVED_SPECIMEN,2020-06-15,INAT,INAT-obs,12345,48.8566,2.3522,France,Île-de-France,Paris,Animalia,Chordata,Mammalia,Carnivora,Ursidae,Ursus,arctos,Jane Doe,John Smith"""

SAMPLE_HEADER_ONLY = """scientificName,basisOfRecord,eventDate,institutionCode,collectionCode,catalogNumber,decimalLatitude,decimalLongitude,country,stateProvince,locality,kingdom,phylum,class,order,family,genus,specificEpithet,recordedBy,identifiedBy"""


class TestLoad:
    def test_load_full_record(self):
        result = load(SAMPLE_CSV.encode("utf-8"))
        assert result["scientificName"] == "Ursus arctos"
        assert result["basisOfRecord"] == "PRESERVED_SPECIMEN"
        assert result["eventDate"] == "2020-06-15"
        assert result["institutionCode"] == "INAT"
        assert result["catalogNumber"] == "12345"
        assert result["decimalLatitude"] == "48.8566"
        assert result["decimalLongitude"] == "2.3522"
        assert result["country"] == "France"
        assert result["kingdom"] == "Animalia"
        assert result["family"] == "Ursidae"
        assert result["genus"] == "Ursus"
        assert result["specificEpithet"] == "arctos"
        assert result["recordedBy"] == "Jane Doe"
        assert result["identifiedBy"] == "John Smith"

    def test_load_header_only(self):
        result = load(SAMPLE_HEADER_ONLY.encode("utf-8"))
        for v in result.values():
            assert v == ""

    def test_load_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            load(b"")


class TestWrite:
    def test_write_full(self):
        json_ld = {
            "name": "Ursus arctos",
            "description": "A brown bear observation",
            "identifier": "12345",
            "datePublished": "2020-06-15",
            "creator": "Jane Doe",
            "license": "CC0 1.0",
            "url": "https://example.org/12345",
        }
        result = write(json_ld)
        assert result["scientificName"] == "Ursus arctos"
        assert result["description"] == "A brown bear observation"
        assert result["catalogNumber"] == "12345"
        assert result["eventDate"] == "2020-06-15"
        assert result["recordedBy"] == "Jane Doe"
        assert result["license"] == "CC0 1.0"
        assert result["url"] == "https://example.org/12345"

    def test_write_empty(self):
        result = write({})
        for v in result.values():
            assert v == ""
