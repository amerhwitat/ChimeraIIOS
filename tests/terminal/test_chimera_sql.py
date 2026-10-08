import sqlite3,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SQL=ROOT/'tools/terminal/chimera-sql'
def test_real_sqlite_file(tmp_path):
 db=tmp_path/'x.sqlite3'
 subprocess.run([sys.executable,str(SQL),'--db',str(db),'-c','CREATE TABLE t(x INTEGER); INSERT INTO t VALUES(7);'],check=True)
 out=subprocess.check_output([sys.executable,str(SQL),'--db',str(db),'-c','SELECT x FROM t;'],text=True)
 assert '7' in out
def test_attach_denied(tmp_path):
 db=tmp_path/'x.sqlite3'
 p=subprocess.run([sys.executable,str(SQL),'--db',str(db),'-c',"ATTACH ':memory:' AS other;"],text=True,capture_output=True)
 assert p.returncode != 0
