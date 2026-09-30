from pathlib import Path
import subprocess, sys
ROOT=Path(__file__).resolve().parents[2]

def run(*args): return subprocess.run([sys.executable,"run_chapter.py",*args],cwd=ROOT,text=True,capture_output=True)

def test_default_runs_all_cases():
    r=run("chapter01")
    assert r.returncode==0
    assert "PASS       chapter-i-sender-conjuration" in r.stdout
    assert "UNVERIFIED printed-prayer-word-initials" in r.stdout

def test_trace_available():
    r=run("chapter01","--case","chapter-i-sender-conjuration","--trace")
    assert r.returncode==0
    assert "[select]" in r.stderr

def test_old_interpretation_flag_is_rejected():
    r=run("chapter01","--interpretation","x")
    assert r.returncode!=0
