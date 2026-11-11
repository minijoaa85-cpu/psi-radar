import datetime as dt
from unittest.mock import Mock
from scripts.competitors import COMPANIES, mentions,devices,assess_source,tag_records,summarize_companies,fetch_company_news,collect_competitors

def test_multilingual_attribution():
 assert "infineon" in mentions("英飞凌 推出 新型 SiC MOSFET")
 assert "rohm" in mentions("ローム、新型SiC MOSFETを発表")
 assert "crmicro" in mentions("华润微电子 IGBT")
 assert "onsemi" not in mentions("on the road with GaN")
 assert "st" not in mentions("STEM research in power materials")
def test_official_evidence_never_inferred_from_name():
 assert assess_source("https://news.google.com/rss/articles/abc","Infineon","infineon")=="news_index_unverified"
 assert assess_source("https://evilinfineon.com/abc","Infineon","infineon")=="news_index_unverified"
 assert assess_source("https://www.infineon.com/abc","Infineon","infineon")=="official_verified_url"
def test_structured_tags_and_company_stats():
 rows=[{"title":"Mitsubishi Electric demonstrates GaN transistor","category":"GaN","kind":"news","date":"2026-11-10","url":"https://news.google.com/rss/a"},
       {"title":"ROHM SiC MOSFET technical announcement","category":"SiC","kind":"news","date":"2026-11-10","url":"https://rohm.com/news"}]
 tag_records(rows)
 assert rows[0]["companies"]==["mitsubishi"]
 assert rows[0]["device_mentions"]==["GaN"]
 assert rows[1]["company_source_status"]["rohm"]=="official_verified_url"
 stats=summarize_companies(rows)
 assert stats["mitsubishi"]["items"]==1 and stats["rohm"]["by_device"]["SiC"]==1
 assert stats["onsemi"]["items"]==0
def test_feed_rejects_unrelated_results(monkeypatch):
 import scripts.competitors as c
 xml="""<rss><channel><item><title>Infineon GaN power semiconductor</title><link>https://news.google.com/rss/articles/1</link><pubDate>Wed, 11 Nov 2026 12:00:00 GMT</pubDate><source>Example Media</source></item><item><title>Infineon quarterly earnings forecast</title><link>https://news.google.com/rss/articles/2</link><pubDate>Wed, 11 Nov 2026 12:00:00 GMT</pubDate></item></channel></rss>"""
 fake=Mock()
 fake.get.return_value.content=xml.encode()
 monkeypatch.setattr(c.dt,"datetime",type("FakeDatetime",(),{"now":staticmethod(lambda tz=None:dt.datetime(2026,11,12,tzinfo=dt.timezone.utc))}))
 rows=fetch_company_news(fake,"infineon")
 assert len(rows)==1 and rows[0]["company_source_status"]["infineon"]=="news_index_unverified"
def test_competitor_fetch_failure_is_non_fatal():
 fake=Mock()
 fake.get.side_effect=ConnectionError("offline")
 rows,errs=collect_competitors(fake)
 assert rows==[] and len(errs)==len(COMPANIES)
