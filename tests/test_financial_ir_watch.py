"""V2.3 IR discovery must NEVER automatically rewrite official monetary values."""
import copy
import datetime as dt
import json

from scripts.financial_ir_watch import (
    SOURCES, candidates_from_html, normalize_url, allowed_url, run_watch,
)
from scripts.validate_financials import PATH


class Response:
    status_code=200
    content=b"<html></html>"
    headers={"Content-Type":"text/html; charset=utf-8"}

    def __init__(self,url,html):
        self.url=url
        self.text=html
        self.content=html.encode("utf-8")

    def raise_for_status(self):
        pass


class StubSession:
    def __init__(self,by_url):
        self.by_url=by_url
    def get(self,url,**kwargs):
        import requests
        value=self.by_url.get(url,requests.ConnectionError("Official fallback temporarily unavailable"))
        if isinstance(value,Exception):
            raise value
        return Response(url,value)


def finance():
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_reject_spoofed_link_and_external_url():
    html="""<a href="https://www.infineon.com/press-release/2027/fy27-q1">FY 2027 Q1 financial results</a>
    <a href="https://infineon.com.evil.test/earnings">FY 2027 Q2 financial results</a>
    <a href="javascript:alert(1)">FY 2027 Q3 results</a>
    <a href="/about/investor/news">Quarterly Report Archive</a>"""
    rows=candidates_from_html(html,"infineon")
    assert len(rows)==1
    assert rows[0]["url"]=="https://www.infineon.com/press-release/2027/fy27-q1"
    assert not allowed_url("https://investor.onsemi.com.evil.test/news","onsemi")
    assert normalize_url("https://www.infineon.com:bad/thing") is None


def test_discover_without_changing_any_financial_metric():
    snapshot=finance()
    original=copy.deepcopy(snapshot)
    pages={conf["landing"]:"<a href='/'>Not relevant</a>" for conf in SOURCES.values()}
    pages[SOURCES["onsemi"]["landing"]]=(
        '<a href="/news-releases/news-release-details/onsemi-reports-fourth-quarter-2026-results">'
        "onsemi Reports Fourth Quarter 2026 Results</a>"
    )
    res=run_watch(snapshot,session=StubSession(pages),
        now=dt.datetime(2026,11,12,8,0,tzinfo=dt.timezone.utc))
    assert snapshot==original
    assert res["automatic_metric_updates"] is False
    assert res["candidate_count"]==1
    assert res["candidates"][0]["company"]=="onsemi"
    assert res["candidates"][0]["review_status"]=="human_review_required"
    assert res["candidates"][0]["source_publication_date"] is None
    assert res["candidates"][0]["first_observed_at"].startswith("2026-11-12")
    assert all(item["status"]=="ok" for item in res["sources"])


def test_first_seen_is_not_rewritten_on_second_run_and_known_is_not_new():
    snapshot=finance()
    pages={conf["landing"]:"" for conf in SOURCES.values()}
    old_url=snapshot["companies"][0]["periods"][-1]["source"]
    pages[SOURCES["infineon"]["landing"]]=(
        f'<a href="{old_url}">FY 2026 financial results</a>'
    )
    first=run_watch(snapshot,session=StubSession(pages),
        now=dt.datetime(2026,11,12,tzinfo=dt.timezone.utc))
    second=run_watch(snapshot,first,session=StubSession(pages),
        now=dt.datetime(2026,11,13,tzinfo=dt.timezone.utc))
    assert first["candidate_count"]==0
    assert first["candidates"][0]["review_status"]=="already_in_verified_financials"
    assert second["candidates"][0]["first_observed_at"]==first["candidates"][0]["first_observed_at"]


def test_source_failure_does_not_claim_no_new_announcements():
    import requests
    snapshot=finance()
    pages={conf["landing"]:"" for conf in SOURCES.values()}
    pages[SOURCES["rohm"]["landing"]]=requests.ConnectionError("Unavailable")
    prior={"candidates":[{
      "company":"rohm","url":"https://www.rohm.com/ir/financial/fy2027q3",
      "title":"Financial Results FY 2027",
      "review_status":"human_review_required","first_observed_at":"2026-11-11T00:00:00+00:00",
      "last_observed_at":"2026-11-11T00:00:00+00:00"
    }]}
    res=run_watch(snapshot,prior,StubSession(pages),
        now=dt.datetime(2026,11,12,tzinfo=dt.timezone.utc))
    rohm=next(r for r in res["sources"] if r["company"]=="rohm")
    assert rohm["status"]=="source_unavailable"
    old=next(r for r in res["candidates"] if r["company"]=="rohm")
    assert old["listed_on_official_ir"] is False
    assert old["first_observed_at"]=="2026-11-11T00:00:00+00:00"
    assert "발표일이 아니" in res["warning"]


def test_untrusted_redirect_is_rejected():
    snapshot=finance()
    class RedirectSession(StubSession):
        def get(self,url,**kwargs):
            r=super().get(url,**kwargs)
            if url==SOURCES["st"]["landing"]:r.url="https://phishing.example/earnings"
            return r
    pages={conf["landing"]:"" for conf in SOURCES.values()}
    res=run_watch(snapshot,session=RedirectSession(pages),
        now=dt.datetime(2026,11,12,tzinfo=dt.timezone.utc))
    st=next(r for r in res["sources"] if r["company"]=="st")
    assert st["status"]=="source_unavailable"


def test_daily_monitor_and_ui_present():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    page=(root/"site"/"index.html").read_text(encoding="utf-8")
    workflow=(root/".github"/"workflows"/"finance-ir.yml").read_text(encoding="utf-8")
    assert 'id="finance-ir-items"' in page
    assert 'id="finance-ir-sources"' in page
    assert 'id="finance-show-known"' in page
    assert "financial_ir_watch.json?nocache=" in page
    assert "listed_on_official_ir" in page
    assert "financial_ir_watch" in workflow
    assert "30 23 * * *" in workflow
    assert "git add site/financial_ir_watch.json" in workflow
    assert "site/financials.json" not in workflow.split("git add ",1)[1]
