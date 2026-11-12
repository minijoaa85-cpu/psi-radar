import datetime as dt
from scripts.official_sources import SOURCES,PORTALS,build_official_records
from scripts.competitors import tag_records,summarize_companies

def test_curated_sources_have_exact_date_and_verified_https():
 entries=build_official_records(dt.date(2026,11,12))
 assert len(entries)>=7
 assert all(r["source_type"]=="manufacturer_official" for r in entries)
 assert all(r["url"].startswith("https://") for r in entries)
 assert all(r["company_attribution"]=="publisher_official" for r in entries)
 assert all(r["kind"]=="official" for r in entries)
 assert {"st","rohm","innoscience"}<=set(r["companies"][0] for r in entries)

def test_official_company_source_status_persists_after_tagging():
 rec=build_official_records(dt.date(2026,11,12))
 original=[dict(r["company_source_status"]) for r in rec]
 tag_records(rec)
 assert original==[r["company_source_status"] for r in rec]
 stats=summarize_companies(rec)
 assert stats["st"]["official"]>=1 and stats["rohm"]["official"]>=3
 assert stats["innoscience"]["official"]>=1

def test_future_dated_official_announcement_is_never_shown():
 rec=build_official_records(dt.date(2026,5,1))
 assert all(r["date"]<="2026-05-01" for r in rec)

def test_portal_is_not_misrepresented_as_announcement():
 assert "basicsemi" in PORTALS
 assert all(r["companies"]!=["basicsemi"] for r in build_official_records(dt.date(2026,11,12)))
