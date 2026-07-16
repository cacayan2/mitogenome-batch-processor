from pathlib import Path
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio import SeqIO
from mitopipeline.rescue.assembly_rescue import Candidate, score_candidate, terminal_overlap

def test_terminal_overlap_detects_duplicate_ends():
    record=SeqRecord(Seq("ACGT"*100+"TTTT"+"ACGT"*20),id="x")
    assert terminal_overlap(record,40,100,1.0)==80

def test_complete_circular_candidate_scores_above_fragmented():
    complete=Candidate("complete","test","x",16500,1,circular=True,covered_fraction=1.0)
    fragmented=Candidate("fragmented","test","y",16500,4,covered_fraction=1.0)
    assert score_candidate(complete,14000,22000)>score_candidate(fragmented,14000,22000)

def test_reference_guided_candidate_is_penalized():
    de_novo=Candidate("de_novo","test","x",16500,1,reference_coverage=0.9)
    guided=Candidate("guided","reference_guided_scaffolding","y",16500,1,reference_coverage=0.9)
    assert score_candidate(de_novo,14000,22000)>score_candidate(guided,14000,22000)
