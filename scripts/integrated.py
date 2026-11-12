"""PSI Radar V2.0: source-separated, evidence-linked integrated analysis.

Assembles existing curated datasets. No AI calls, inferred device performance,
research-to-product causality or manufactured measurements.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
TECHNOLOGIES = ("GaN", "SiC", "IGBT", "SJ MOSFET", "SGT")
METRICS = ("rds_on", "rds_on_max", "qg", "qgd", "qoss", "eoss", "vce_sat", "qrr")
MAX_BRIEFS = 12
MAX_TOPIC_EVIDENCE = 5


def safe_https(url):
    if not isinstance(url, str):
        return False
    parsed = urlparse(url)
    return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password


def read_json(path):
    return json.loads((SITE / path).read_text(encoding="utf-8"))


def public_specs(row):
    result = {}
    for key in METRICS:
        entry = (row.get("specs") or {}).get(key)
        if not isinstance(entry, dict):
            continue
        result[key] = {
            "value": entry.get("value"), "unit": entry.get("unit"),
            "kind": entry.get("kind"),
            "condition": str(entry.get("condition") or "상세 시험 조건 미확인"),
            "test_conditions": entry.get("test_conditions") or {},
        }
    return result


def make_integrated(briefing, topics, architecture, benchmark):
    brief_by_cat = {c.get("category"): c for c in briefing.get("categories", [])}
    arch_by_cat = {c.get("category"): c for c in architecture.get("categories", [])}
    topic_rows = topics.get("topics", [])
    devices = benchmark.get("devices", [])
    categories = []
    for category in TECHNOLOGIES:
        archive = brief_by_cat.get(category, {})
        arch = arch_by_cat.get(category, {})
        briefs = []
        seen_urls = set()
        for r in archive.get("items", []):
            url = r.get("url")
            if not safe_https(url) or url in seen_urls:
                continue
            seen_urls.add(url)
            level = r.get("source_level")
            if level not in ("official", "research", "news"):
                continue
            briefs.append({
                "title": str(r.get("title") or "")[:260],
                "date": str(r.get("date") or ""),
                "source": str(r.get("source") or "")[:100],
                "url": url,
                "source_level": level,
                "summary": str(r.get("summary") or "")[:250],
                "topic_ids": [x for x in r.get("topic_ids", []) if isinstance(x, str)],
                "companies": [x for x in r.get("companies", []) if isinstance(x, str)],
                "change_candidate": bool(r.get("change_candidate")),
                "evidence_status": r.get("evidence_status") or "metadata_only",
            })
            if len(briefs) >= MAX_BRIEFS:
                break

        selected_topics = []
        for t in topic_rows:
            if t.get("category") != category:
                continue
            article_refs = []
            seen_refs = set()
            for r in t.get("article_candidates", []):
                url = r.get("url")
                if not safe_https(url) or url in seen_refs:
                    continue
                seen_refs.add(url)
                article_refs.append({
                    "title": str(r.get("title") or "")[:220],
                    "date": str(r.get("date") or ""),
                    "source": str(r.get("publisher") or "")[:100],
                    "url": url,
                    "kind": r.get("kind"),
                    "confidence": "title_keyword_match",
                })
                if len(article_refs) >= MAX_TOPIC_EVIDENCE:
                    break
            selected_topics.append({
                "id": t["id"], "name": t["name"], "simple": t.get("simple") or "",
                "why": t.get("why") or "",
                "evidence_count_sample": len(t.get("article_candidates", [])),
                "evidence": article_refs
            })

        products = []
        for r in devices:
            if r.get("category") != category or not safe_https(r.get("url")):
                continue
            products.append({
                "id": r["id"], "company": r["company"], "part": r["part"],
                "structure": r.get("structure") or "구조 미확인",
                "package": r.get("package") or "",
                "voltage": r.get("voltage") or {},
                "verification": r.get("verification") or "unverified",
                "datasheet_revision": r.get("datasheet_revision"),
                "architecture": r.get("architecture") or "unknown",
                "specs": public_specs(r), "url": r["url"],
            })
        company_names = sorted({r["company"] for r in products})
        source_counts = {k: sum(r["source_level"] == k for r in briefs) for k in ("official", "research", "news")}
        categories.append({
            "category": category,
            "intro": arch.get("intro") or "공식 구조 분류 정보가 아직 없습니다.",
            "physics": arch.get("physics") or [],
            "watch": arch.get("watch") or [],
            "topics": selected_topics,
            "articles": briefs,
            "article_count_sample": len(briefs),
            "source_counts_sample": source_counts,
            "products": products,
            "product_count": len(products),
            "companies": company_names,
            "datasheet_table_verified_count": sum(r["verification"] == "datasheet_table_verified" for r in products),
            "structured_test_conditions_count": sum(any(v.get("test_conditions") for v in r["specs"].values()) for r in products),
        })

    return {
        "schema_version": 1,
        "version": "2.0",
        "generated_at": briefing.get("generated_at"),
        "benchmark_reviewed_on": benchmark.get("reviewed_on"),
        "categories": categories,
        "method": "Curated manufacturer specs plus category-matched public article metadata and title-keyword topics.",
        "warning": (
            "자료는 기술군별 공개 메타데이터와 공식 제품 자료를 함께 보여주는 참고용입니다. "
            "논문/기사와 제품 사이의 인과관계, 성능 개선, 기술력 순위는 검증하지 않았습니다. "
            "FOM 숫자는 VGS/ID/Tj 및 정격·통계 기준이 동일한 경우에만 전문가가 원문을 확인한 뒤 비교해야 합니다. "
            "자료 0건은 연구 부재를 의미하지 않습니다."
        ),
    }


def main():
    out = make_integrated(
        read_json("briefing.json"),
        read_json("topic_map.json"),
        read_json("architecture.json"),
        read_json("benchmark.json"),
    )
    (SITE / "integrated.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        "Integrated V2.0:", len(out["categories"]), "technologies,",
        sum(x["article_count_sample"] for x in out["categories"]), "source candidates,",
        sum(x["product_count"] for x in out["categories"]), "official product records"
    )


if __name__ == "__main__":
    main()
