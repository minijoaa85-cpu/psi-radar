import datetime as dt
from unittest.mock import Mock
from scripts.research import make_record,crossref_search,openalex_search,collect_focused

NOW=dt.datetime(2026,11,11,tzinfo=dt.timezone.utc)
def test_journal_record_provenance():
 r=make_record("IGBT","Trench IGBT switching reliability","2026-09-01",
 "IEEE Transactions on Electron Devices","https://doi.org/10.1234/demo",
 "10.1234/demo","Measured switching losses","Crossref")
 assert r["kind"]=="paper" and r["metadata_provider"]=="Crossref"
 assert r["lookback_days"]==365 and "미검증" in r["summary_status"]

def test_crossref_relevance_and_date():
 fake=Mock()
 fake.get.return_value.json.return_value={"message":{"items":[
  {"title":["Improved trench IGBT switching loss"],"DOI":"10.1/abc","URL":"https://doi.org/10.1/abc","published":{"date-parts":[[2026,9,3]]},"container-title":["IEEE Transactions on Electron Devices"]},
  {"title":["IGBT modeling for an old design"],"DOI":"10.1/old","URL":"https://doi.org/10.1/old","published":{"date-parts":[[2019,1,3]]}},
  {"title":["Artificial intelligence text modeling"],"DOI":"10.1/no","URL":"https://doi.org/10.1/no","published":{"date-parts":[[2026,10,1]]}}
 ]}}
 rows=crossref_search(fake,"trench IGBT","IGBT","2025-11-11","2026-11-11")
 assert len(rows)==1 and rows[0]["doi"]=="10.1/abc"

def test_openalex_abstract_and_no_cross_topic():
 fake=Mock()
 fake.get.return_value.json.return_value={"results":[
  {"title":"Shielded gate trench MOSFET field control","publication_date":"2026-08-10",
   "doi":"https://doi.org/10.1/sgt","primary_location":{"source":{"display_name":"Solid-State Electronics","type":"journal"}},
   "abstract_inverted_index":{"Gate":[0],"shielding":[1],"reduces":[2],"capacitance":[3]}},
  {"title":"Generative adversarial network for image recognition","publication_date":"2026-08-10"}
 ]}
 rows=openalex_search(fake,"shielded gate MOSFET","SGT","2025-11-11","2026-11-11")
 assert len(rows)==1 and "Gate shielding" in rows[0]["abstract"]

def test_collection_failure_is_nonfatal():
 fake=Mock()
 fake.get.side_effect=ConnectionError("unavailable")
 rows,errs,stats=collect_focused(fake,NOW)
 assert not rows and errs and set(stats)=={"IGBT","SGT","SJ MOSFET"}

def test_crossref_429_backoff_once_then_success(monkeypatch):
 from scripts import research
 from requests import Response
 from unittest.mock import Mock
 pauses=[]
 monkeypatch.setattr(research.time,"sleep",lambda seconds:pauses.append(seconds))
 limited=Mock(status_code=429,headers={"Retry-After":"1"})
 success=Mock(status_code=200)
 success.json.return_value={"message":{"items":[]}}
 fake=Mock()
 fake.get.side_effect=[limited,success]
 rows=research.crossref_search(fake,"IGBT","IGBT","2025-11-11","2026-11-11")
 assert rows==[] and pauses==[1] and fake.get.call_count==2

def test_crossref_circuit_breaker_does_not_repeat_429(monkeypatch):
 from scripts import research
 import requests
 monkeypatch.setattr(research.time,"sleep",lambda _:None)
 limited=Mock(status_code=429,headers={})
 limited.raise_for_status.side_effect=requests.HTTPError(response=limited)
 success=Mock(status_code=200)
 success.json.return_value={"results":[]}
 fake=Mock()
 def get(url,**kwargs):
  return limited if "crossref" in url else success
 fake.get.side_effect=get
 rows,errors,stats=research.collect_focused(fake,NOW)
 assert rows==[] and len([x for x in errors if "Crossref" in x])==1
 assert len([x for x in fake.get.call_args_list if "crossref" in x.args[0]])==2
 assert set(stats)=={"IGBT","SGT","SJ MOSFET"}
