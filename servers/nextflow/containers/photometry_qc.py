import sys
from pathlib import Path
from iblphotometry.tasks import FibrePhotometryQC

# TODO implement proper logging
session_path = Path(sys.argv[1])
try:
    task = FibrePhotometryQC(session_path)
    task.run(on_error="raise")
    sys.exit(0)
except Exception as e:
    print(e)
    sys.exit(1)
