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
import shutil

LOCATION = "server"
REGISTER_DATASETS = False
DRY = True

match len(sys.argv):
    case 3:
        session_path = Path(sys.argv[1])
        task_id = Path(sys.argv[2])
    case _:
        raise ValueError(f"input arguments error: {sys.argv}")

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
# session_path = (
#     Path("/mnt/s0/Data/Subjects")
#     / one.eid2path(task_dict["session"]).session_path_short()
# )

# instantiate and run
task = task_class(
    session_path,
    **task_dict["arguments"],
    on_error="raise",
    one=one,
    location=LOCATION,
)
# find flagfile
flag_file = list(session_path.glob(f"task.{task_id}.*.ready"))
if len(flag_file) != 1:
    print(session_path)
    print(task_id)
flag_file = flag_file[0]

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
            shutil.move(flag_file, flag_file.with_suffix(".errored"))
            sys.exit(1)

shutil.move(flag_file, flag_file.with_suffix(".completed"))
sys.exit(0)

# does task.log exists?
