"""
this script takes a take a task_id as a first argument (as registered on alyx)
instantiates the appropriate task
runs it
optionally registers the output data
"""

import sys
from pathlib import Path
from one.api import ONE
import importlib

LOCATION = "server"
REGISTER_DATASETS = False
DRY = True

match len(sys.argv):
    case 1:
        raise ValueError("no input task id provided")
    case 2:
        task_id = Path(sys.argv[1])
    case _:
        raise ValueError(f"too many input arguments: {sys.argv}")

# get the task dict from alyx
one = ONE(cache_rest=None)
task_dict = one.alyx.rest("tasks", "read", task_id)

# TODO logging
print(f" --- processing task: {task_id} --- ")

# get the task class
task_name = task_dict["executable"].split(".")[-1]
module = ".".join(task_dict["executable"].split(".")[:-1])
task_class = getattr(importlib.import_module(module), task_name)

# get local path of the session
# handle this more properly
session_path = (
    Path("/mnt/s0/Data/Subjects")
    / one.eid2path(task_dict["session"]).session_path_short()
)

# instantiate and run
task = task_class(
    session_path,
    **task_dict["arguments"],
    on_error="raise",
    one=one,
    location=LOCATION,
)
if not DRY:
    task.run()

    # if successful, register datasets
    if REGISTER_DATASETS:
        if task.status == 0:
            registered_dsets = task.register_datasets(
                location=LOCATION,
                labs=one.alyx.rest("sessions", "read", task_dict["session"])["lab"],
            )
            one.alyx.rest(
                "tasks", "partial_update", task_id, data={"status": "Complete"}
            )
            sys.exit(0)
        else:
            one.alyx.rest(
                "tasks", "partial_update", task_id, data={"status": "Errored"}
            )
            sys.exit(1)

sys.exit(0)

# does task.log exists?
