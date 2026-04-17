import sys
from pathlib import Path
from iblphotometry.tasks import FibrePhotometryDAQSync
from one.api import ONE

# TODO implement proper logging
session_path = Path(sys.argv[1])

try:
    one = ONE()
    task = FibrePhotometryDAQSync(session_path, one=one)
    task.run(load_timestamps=True, on_error="raise")
    sys.exit(0)
except Exception as e:
    print(e)
    sys.exit(1)
