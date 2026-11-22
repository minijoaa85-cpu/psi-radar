"""Regression: legacy journal records can contain stale_reused=null.

This caused all manual V3.4 collection runs #316–#318 to fail before saving
the research_coverage payload.
"""
from scripts.collect import count_reused_papers

def test_reused_paper_counter_handles_missing_and_null_flags():
    records=[
       {"category":"GaN","kind":"paper","stale_reused":None},
       {"category":"GaN","kind":"paper"},
       {"category":"GaN","kind":"paper","stale_reused":False},
       {"category":"GaN","kind":"paper","stale_reused":True},
       {"category":"GaN","kind":"news","stale_reused":True},
       {"category":"SiC","kind":"paper","stale_reused":True},
    ]
    assert count_reused_papers(records,"GaN")==1
    assert count_reused_papers(records,"SiC")==1
    assert count_reused_papers(records,"IGBT")==0

def test_fresh_plus_reused_always_equals_published_paper_count():
    records=[
       {"category":"SiC","kind":"paper","stale_reused":None},
       {"category":"SiC","kind":"paper","stale_reused":True},
       {"category":"SiC","kind":"paper","stale_reused":False},
    ]
    reused=count_reused_papers(records,"SiC")
    published=len(records)
    assert published-reused==2
    assert (published-reused)+reused==published
