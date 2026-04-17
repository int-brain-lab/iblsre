import sys
from pathlib import Path
from ibllib.pipes.dynamic_pipeline import make_pipeline

# wrap everything in a big try/except to catch return values

session_path = Path(sys.argv[1])
# session_path = "/mnt/s0/Data/Subjects/ZFM-09140/2025-08-28/001"

print(f" --- processing folder {session_path} --- ")
pipeline = make_pipeline(session_path)
for name, task in pipeline.tasks.items():
    if name == "FibrePhotometryDAQSync":
        task.run(load_timestamps=True)
