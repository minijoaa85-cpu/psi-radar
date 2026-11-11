import json
from unittest.mock import Mock
from scripts import ai_enrich

def test_news_prompt_enforces_evidence():
 row={"id":"x","title":"650V GaN HEMT for data center","category":"GaN","kind":"news"}
 p=ai_enrich.build_prompt(row)
 assert "제목만" in p and "제품 성능" in p

def test_paper_prompt_limits_claims():
 row={"id":"y","title":"SiC MOSFET gate oxide","category":"SiC","kind":"paper","abstract":"Reliability results were measured."}
 p=ai_enrich.build_prompt(row)
 assert "초록" in p and "수치" in p

def test_missing_key_never_calls_api():
 session=Mock()
 rows=[{"id":"x","title":"GaN","kind":"news"}]
 stats=ai_enrich.enrich(rows,session,"")
 assert not stats["enabled"] and stats["calls"]==0
 session.post.assert_not_called()

def test_cached_record_skips_api():
 session=Mock()
 rows=[{"id":"x","title":"GaN","title_ko":"질화갈륨","kind":"news"}]
 stats=ai_enrich.enrich(rows,session,"test-key")
 assert stats["calls"]==0 and stats["cache_hits"]==1
 session.post.assert_not_called()

def test_call_cap_prevents_any_calls(monkeypatch):
 monkeypatch.setattr(ai_enrich,"MAX_CALLS",0)
 session=Mock()
 rows=[{"id":"x","title":"GaN transistor","kind":"news"}]
 stats=ai_enrich.enrich(rows,session,"test-key")
 assert stats["calls"]==0
 session.post.assert_not_called()

def test_safeguards_default_limits():
 assert ai_enrich.MAX_CALLS<=30
 assert ai_enrich.MAX_ESTIMATED_USD<=1.0
 assert ai_enrich.MAX_OUTPUT_TOKENS<=12000
