import logging

from sickle import Sickle
from sickle.oaiexceptions import NoRecordsMatch, NoSetHierarchy

logger = logging.getLogger(__name__)

SUPPORTED_PREFIXES = {"oai_dc", "oai_datacite"}

LOG_INTERVAL = 500


def harvest(
    base_url: str,
    metadata_prefix: str,
    set: str | None = None,
    from_date: str | None = None,
    until_date: str | None = None,
    max_records: int = 0,
) -> dict:
    if metadata_prefix not in SUPPORTED_PREFIXES:
        raise ValueError(f"Unsupported metadata prefix: {metadata_prefix}")

    sickle = Sickle(base_url)
    params = {"metadataPrefix": metadata_prefix}
    if set:
        params["set"] = set
    if from_date:
        params["from"] = from_date
    if until_date:
        params["until"] = until_date

    logger.info(
        "harvest start: base_url=%s metadata_prefix=%s params=%s", base_url, metadata_prefix, params
    )

    records = []
    try:
        iterator = sickle.ListRecords(**params)
    except NoRecordsMatch:
        logger.info("harvest empty: no records match query")
        return {"records": [], "total": 0, "metadata_format": metadata_prefix}
    for i, rec in enumerate(iterator, start=1):
        if max_records and i > max_records:
            logger.info("harvest stop: reached max_records=%d", max_records)
            break
        if i % LOG_INTERVAL == 0:
            logger.info("harvest progress: %d records fetched so far", i)
        if rec.header.deleted:
            continue
        record = {
            "identifier": rec.header.identifier,
            "datestamp": rec.header.datestamp,
            "set_spec": list(rec.header.setSpecs) if rec.header.setSpecs else [],
            "metadata": rec.metadata,
            "metadata_format": metadata_prefix,
        }
        records.append(record)

    logger.info("harvest complete: total=%d", len(records))
    return {
        "records": records,
        "total": len(records),
        "metadata_format": metadata_prefix,
    }


def list_sets(base_url: str) -> list[dict]:
    sickle = Sickle(base_url)
    sets = []
    try:
        iterator = sickle.ListSets()
    except NoSetHierarchy:
        logger.info("list_sets: repository has no set hierarchy")
        return []
    for s in iterator:
        sets.append(
            {
                "spec": s.setSpec,
                "name": s.setName,
            }
        )
    logger.info("list_sets: base_url=%s count=%d", base_url, len(sets))
    return sets
