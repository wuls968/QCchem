"""Owned process fixture: pause inside the sixth local backend call."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from qcchem.backends.statevector import StatevectorBackend
from qcchem.cli.main import main

original = StatevectorBackend.evaluate
calls = 0
gate = Path(os.environ["QCCHEM_TEST_GATE"])


def paused_evaluate(self, *args):
    global calls
    calls += 1
    if calls == 6:
        (gate / "ready").write_text("ready", encoding="utf-8")
        deadline = time.monotonic() + 25
        while not (gate / "release").exists():
            if time.monotonic() > deadline:
                raise TimeoutError("Owned checkpoint test gate timed out.")
            time.sleep(0.02)
    return original(self, *args)


StatevectorBackend.evaluate = paused_evaluate
raise SystemExit(main(sys.argv[1:]))
