"""PSI Radar V3.3: validate an exact published snapshot and disclose evidence limits.

Structural correctness is not evidence of independent scientific verification.
Run with --write to atomically publish site/source_health.json; --check revalidates it.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
CATEGORIES = ("GaN", "SiC", "IGBT", "SJ MOSFET", "SGT")
KINDS = ("news", "paper", "official")
WEEK_RE = re.compile(r"^(\d{4})-W(\d{2})$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _date(value):
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        raise ValueError("date must be ISO YYYY-MM-DD")
    return dt.date.fromisoformat(value)


def _datetime(value):
    timestamp = dt.datetime.fromisoformat(value)
    if not timestamp.tzinfo or timestamp.utcoffset() is None:
        raise ValueError("generated_at must include UTC offset")
    return timestamp


def verify(site: Path = SITE):
    errors, warnings = [], []
    dataset = _read(site / "data.json")
    index = _read(site / "reports" / "index.json")
    benchmark = _read(site / "benchmark.json")
    financials = _read(site / "financials.json")
    records = dataset.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("data.json records must be a nonempty array")

    stamp = _datetime(dataset["generated_at"])
    if index.get("generated_at") != dataset["generated_at"]:
        errors.append("weekly index generated_at does not match published data.json")
    category_counts = {c: {k: 0 for k in KINDS} for c in CATEGORIES}
    evidence = {"manufacturer_statement": 0, "journal_metadata": 0, "news_index": 0}
    relevance = {"높음": 0, "보통": 0, "낮음": 0, "미분류": 0}
    ids = set()
    reused = 0
    for position, r in enumerate(records):
        ident = r.get("id")
        if not isinstance(ident, str) or not ident.strip() or ident in ids:
            errors.append(f"missing or duplicate record id at position {position}")
        ids.add(ident)
        category, kind = r.get("category"), r.get("kind")
        if category not in category_counts or kind not in KINDS:
            errors.append(f"invalid category/kind at record {position}")
            continue
        category_counts[category][kind] += 1
        if not all(isinstance(r.get(field), str) and r[field].strip() for field in ("title", "source", "url")):
            errors.append(f"missing title/source/url at record {position}")
        u = urlparse(str(r.get("url") or ""))
        if u.scheme != "https" or not u.netloc:
            errors.append(f"non-https original link at record {position}")
        try:
            published = _date(r.get("date"))
            if published > stamp.astimezone(dt.timezone(dt.timedelta(hours=9))).date():
                errors.append(f"future publication date at record {position}")
        except (ValueError, TypeError):
            errors.append(f"invalid publication date at record {position}")
        if kind == "official":
            evidence["manufacturer_statement"] += 1
            if r.get("source_type") != "manufacturer_official":
                errors.append(f"official source attribution unsupported at record {position}")
            from scripts.competitors import COMPANIES
            owners = r.get("companies") or []
            owner = owners[0] if isinstance(owners, list) and len(owners) == 1 else None
            domains = COMPANIES.get(owner, {}).get("domains", ())
            hostname = (u.hostname or "").lower()
            if not domains or not any(hostname == domain or hostname.endswith("." + domain) for domain in domains):
                errors.append(f"official URL domain is not registered to its manufacturer at record {position}")
        elif kind == "paper":
            evidence["journal_metadata"] += 1
        else:
            evidence["news_index"] += 1
        level = r.get("relevance_level", "미분류")
        relevance[level if level in relevance else "미분류"] += 1
        reused += bool(r.get("stale_reused"))

    if sum(evidence.values()) != len(records):
        errors.append("record type counts do not sum to dataset size")
    # Counts displayed by the frontend must describe the published, capped
    # record array, not the larger pre-publication provider response.
    published_counts = dataset.get("counts")
    expected_counts = {tech: sum(category_counts[tech].values()) for tech in CATEGORIES}
    if published_counts != expected_counts:
        errors.append("data.json counts differ from the published records array")

    entries = index.get("reports")
    if not isinstance(entries, list) or not entries:
        errors.append("weekly index contains no archive entries")
        entries = []
    archive_hashes, archive_weeks = {}, set()
    for item in entries:
        week, name = item.get("week"), item.get("file")
        match = WEEK_RE.fullmatch(str(week))
        if not match or name != "reports/" + str(week) + ".json" or week in archive_weeks:
            errors.append("invalid or repeated archive filename/week")
            continue
        archive_weeks.add(week)
        path = site / name
        if not path.is_file():
            errors.append(f"missing archived weekly report {name}")
            continue
        report = _read(path)
        archive_hashes[name] = _sha(path)
        try:
            expected = dt.date.fromisocalendar(int(match[1]), int(match[2]), 1)
            if _date(report.get("week_start")) != expected:
                errors.append(f"week_start mismatch: {week}")
        except (TypeError, ValueError):
            errors.append(f"invalid ISO week date: {week}")
        if report.get("week") != week or report.get("generated_at") != item.get("generated_at"):
            errors.append(f"week metadata/index mismatch: {week}")
        summary = report.get("by_category")
        weekly_total = report.get("published_this_week_count")
        if not isinstance(summary, dict) or set(summary) != set(CATEGORIES):
            errors.append(f"missing category counts: {week}")
        elif not all(type(summary[c]) is int and summary[c] >= 0 for c in CATEGORIES):
            errors.append(f"noninteger category counts: {week}")
        elif type(weekly_total) is not int or sum(summary.values()) != weekly_total:
            errors.append(f"category counts not equal published_this_week_count: {week}")
        if not isinstance(report.get("weekly_items"), list):
            errors.append(f"weekly_items not a list: {week}")
        if week == entries[0].get("week"):
            if report.get("generated_at") != dataset["generated_at"]:
                errors.append("latest weekly report does not match data snapshot timestamp")
            if report.get("total_collection_count") != len(records):
                errors.append("latest weekly report total_collection_count differs from data")
            if report.get("research_reference_count") != evidence["journal_metadata"]:
                errors.append("latest weekly research reference count differs from data")

    if not isinstance(benchmark.get("devices"), list) or not benchmark["devices"]:
        errors.append("benchmark catalog missing")
    if len(financials.get("companies", [])) != 4:
        errors.append("financials manual company baseline incomplete")

    if dataset.get("errors"):
        warnings.append(f"collection/AI warnings reported: {len(dataset['errors'])}")
    for tech in ("GaN", "SiC", "IGBT", "SJ MOSFET", "SGT"):
        if category_counts[tech]["paper"] == 0:
            warnings.append(f"{tech}: no paper metadata in current collection sample")
    verified = sum(r.get("verification") == "datasheet_table_verified"
                   for r in benchmark.get("devices", []))
    if verified < len(benchmark.get("devices", [])):
        warnings.append(f"benchmark: {verified}/{len(benchmark.get('devices', []))} datasheet-table verified")
    if reused:
        warnings.append(f"{reused} paper metadata items reused from prior successful collection")
    low_news = sum(r.get("kind") == "news" and r.get("relevance_level") == "낮음"
                   for r in records)
    if low_news:
        warnings.append(f"news technical-keyword relevance low: {low_news} items; not a credibility rating")

    hashed = {}
    for name in ("data.json", "reports/index.json", "benchmark.json", "financials.json"):
        hashed[name] = _sha(site / name)
    return {
        "schema_version": 1,
        "snapshot_generated_at": dataset["generated_at"],
        "validation_status": "failed" if errors else ("passed_with_warnings" if warnings else "passed"),
        "structural_integrity": "failed" if errors else "passed",
        "scientific_verification": "not_independently_verified",
        "technical_relevance_method": "metadata-rule-v1 (keyword heuristic; not source credibility)",
        "records": len(records),
        "counts_by_kind": {k: evidence[v] for k, v in (
            ("official", "manufacturer_statement"), ("paper", "journal_metadata"), ("news", "news_index"))},
        "source_evidence_tiers": evidence,
        "relevance": relevance,
        "category_counts": category_counts,
        "reused_metadata": reused,
        "benchmark": {"products": len(benchmark.get("devices", [])), "datasheet_table_verified": verified},
        "archived_weeks": [r.get("week") for r in entries],
        "files_sha256": hashed,
        "archives_sha256": archive_hashes,
        "warnings": warnings,
        "errors": errors,
        "interpretation": "Integrity checks verify published metadata consistency only; manufacturer statements, journal metadata, news-index titles and AI summaries are not independently validated scientific claims."
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write source_health.json from currently validated source files")
    parser.add_argument("--check", action="store_true", help="verify existing source_health.json matches current source files")
    opts = parser.parse_args()
    result = verify()
    target = SITE / "source_health.json"
    if result["errors"]:
        raise SystemExit("DATA INTEGRITY FAIL: " + "; ".join(result["errors"]))
    if opts.write:
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if opts.check and _read(target) != result:
        raise SystemExit("DATA INTEGRITY FAIL: source_health.json not equal to current source snapshot")
    print("Source quality:", result["validation_status"], "records:", result["records"],
          "archived_weeks:", len(result["archived_weeks"]), "warnings:", len(result["warnings"]))


if __name__ == "__main__":
    main()
