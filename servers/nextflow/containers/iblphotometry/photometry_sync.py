import sys
from pathlib import Path
from ibllib.pipes.dynamic_pipeline import get_photometry_tasks
import ibllib.io.session_params as sess_params
from ibllib.pipes.tasks import Pipeline, run_alyx_task
from one.api import ONE

LOCATION = "server"
DRY = False
REGISTER_DATASETS = False

# TODO implement proper logging
if len(sys.argv) == 1:
    # DEBUGGING
    session_path = Path("/mnt/s0/georg/Data/Subjects/ZFM-09140/2025-08-26/001")
else:
    session_path = Path(sys.argv[1])

one = ONE(cache_rest=None)
experiment_description = sess_params.read_params(session_path)
eid = one.path2eid(session_path)
lab = one.alyx.rest("sessions", "read", eid)["lab"]

# the run_alyx_task approach - this keeps full compatibility with alyx
# should handle everything - but doesn't play nice with the debugger
tasks = get_photometry_tasks(experiment_description, session_path=session_path, one=one)
pipeline = Pipeline(session_path=session_path, one=one)
pipeline.tasks = tasks
task_dicts = pipeline.create_alyx_tasks(rerun__status__in="__all__")
assert len(task_dicts) == 1, "more than one sync task found"
task_dict = task_dicts[0]
if not DRY:
    task, registered_datasets = run_alyx_task(
        one=one,
        session_path=session_path,
        tdict=task_dict,
        location=LOCATION,
        mode="raise",
    )

# this works with the debugger
# assert len(tasks) == 1
# task = list(tasks.values())[0]
# task.setUp()
# if not DRY:
#     task._run()

#     # update task log
#     log = ""
#     one.alyx.rest("tasks", "partial_update", task_dict["id"], data={"log": log})

#     # update task status
#     status = "Complete"
#     one.alyx.rest("tasks", "partial_update", task_dict["id"], data={"status": status})

#     # register datasets
#     if REGISTER_DATASETS:
#         registered_dsets = task.register_datasets(
#             location=LOCATION,
#             labs=one.alyx.rest("sessions", "read", eid)["lab"],
#         )

# deal with return code
# if task.status == 0:
#     sys.exit(0)
# else:
#     sys.exit(1)
