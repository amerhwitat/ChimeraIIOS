from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/watchdog/chimera-watchdog.conf"
def test_watchdog_policy():
    rows=[line.split() for line in CFG.read_text().splitlines() if line.strip() and not line.lstrip().startswith("#")]
    names={r[0] for r in rows}
    assert {"koronos","kore","microkernel","mobile-init"} <= names
    assert all(len(r)==2 and 0<int(r[1])<=3600000 for r in rows)
