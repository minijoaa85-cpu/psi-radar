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

def test_focused_paper_priority():
 rows=[
  {"id":"n","title":"GaN power device","kind":"news","category":"GaN","score":95},
  {"id":"s","title":"SJ MOSFET charge balance","kind":"paper","category":"SJ MOSFET","score":30},
  {"id":"i","title":"Trench IGBT short circuit","kind":"paper","category":"IGBT","score":30},
  {"id":"g","title":"GaN journal","kind":"paper","category":"GaN","score":90},
  {"id":"t","title":"Shielded gate trench MOSFET","kind":"paper","category":"SGT","score":30},
 ]
 assert [x["category"] for x in ai_enrich.prioritized(rows)[:3]]==["IGBT","SGT","SJ MOSFET"]

def test_ai_reports_invalid_json_without_leaking_secret(monkeypatch):
 from unittest.mock import Mock
 monkeypatch.setattr(ai_enrich,"MAX_CALLS",1)
 fake=Mock()
 fake.post.return_value.json.return_value={"choices":[{"message":{"content":"incomplete"}}],"usage":{"prompt_tokens":100,"completion_tokens":100}}
 rows=[{"id":"e","title":"IGBT trench power module","kind":"news","category":"IGBT","score":30}]
 stats=ai_enrich.enrich(rows,fake,"private-secret")
 assert stats["calls"]==1 and stats["failures"]==1 and stats["successes"]==0
 assert "Invalid/short JSON" in stats["failure_reasons"]
 assert "private-secret" not in str(stats["errors"])

def test_competitor_ai_priority_stays_within_existing_quota():
 rows=[
  {"id":"high","kind":"news","category":"GaN","title":"General GaN HEMT","score":99},
  {"id":"in","kind":"news","category":"SiC","title":"Infineon SiC MOSFET","score":60,"companies":["infineon"]},
  {"id":"ro","kind":"news","category":"SiC","title":"ROHM SiC MOSFET","score":55,"companies":["rohm"]},
  {"id":"cn","kind":"news","category":"GaN","title":"Innoscience GaN HEMT","score":50,"companies":["innoscience"]},
  {"id":"jp","kind":"news","category":"IGBT","title":"Fuji Electric IGBT","score":40,"companies":["fuji"]},
 ]
 selected=ai_enrich.prioritized(rows)
 assert [r["id"] for r in selected[:4]]==["in","ro","cn","jp"]
 assert len(selected)==len(rows) and len(set(r["id"] for r in selected))==len(rows)
