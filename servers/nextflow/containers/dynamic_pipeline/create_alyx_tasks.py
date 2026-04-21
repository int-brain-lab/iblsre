"""
this script
for a given session path
creates the tasks on alyx
writes a file "task_ids.txt" with the task ids of the newly created tasks
"""

import sys
from pathlib import Path
from one.api import ONE
from ibllib.pipes.dynamic_pipeline import make_pipeline

one = ONE(cache_rest=None)

match len(sys.argv):
    case 1:
        raise ValueError("no input argument (a path to a session) provided")
        # or, for debugging:
        # session_path = Path("/mnt/s0/Data/Subjects/ZFM-09140/2025-08-26/001")
    case 2:
        session_path = Path(sys.argv[1])
        assert session_path.exists(), f"session path {session_path} does not exist"
    case _:
        raise ValueError(f"too many input arguments: {sys.argv}")

# TODO proper logging
print(f" --- generating tasks for: {session_path} --- ")

# NOTE
# wrapping everything in a large try except block
# to have exit status available in nextflow
try:
    pipeline = make_pipeline(session_path, one=one)
    tasks_alyx = pipeline.create_alyx_tasks()

    # create task ids and write them to a file
    task_ids = [task["id"] for task in tasks_alyx]
    with open("task_ids.txt", "w") as fH:
        # NOTE it is necessary to write to the current working directory
        # to allow the file being passed between nextflow processes
        fH.writelines([t + "\n" for t in task_ids])
    sys.exit(0)
except Exception as e:
    # TODO proper logging
    # log exeption / error
    sys.exit(1)
