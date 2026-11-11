from scripts.collect import classify, classify_topics, score, unique
def test_classify():
 assert classify("650V GaN HEMT","기타")=="GaN"
 assert classify("silicon carbide","기타")=="SiC"
def test_topics():
 assert "데이터센터" in classify_topics("800VDC AI data center")
def test_unique():
 r={"title":"Same Paper","doi":"10.1234/ABC"}
 assert len(unique([r,r]))==1
def test_score():
 assert score("GaN data center reliability","GaN")>score("GaN","GaN")
