import logging
import sys
from pathlib import Path

import ibllib.io.session_params as sess_params
from ibllib.pipes.dynamic_pipeline import get_photometry_tasks
from ibllib.pipes.tasks import Pipeline, run_alyx_task
from iblutil.util import setup_logger
from one.api import ONE

# logs to stdout, with the same format and colors as the ibllib logs
_logger = setup_logger(name="photometry_sync", level=logging.INFO)

LOCATION = "server"
DRY = False
session_path = Path(sys.argv[1])

one = ONE(cache_rest=None)
experiment_description = sess_params.read_params(session_path)
eid = one.path2eid(session_path)
lab = one.alyx.rest("sessions", "read", eid)["lab"]
_logger.info("photometry sync on session %s (eid: %s, lab: %s)", session_path, eid, lab)

# the run_alyx_task approach - this keeps full compatibility with alyx
tasks = get_photometry_tasks(experiment_description, session_path=session_path, one=one)
_logger.info("photometry tasks for this session: %s", ", ".join(tasks))
pipeline = Pipeline(session_path=session_path, one=one)
pipeline.tasks = tasks
(task_dict,) = pipeline.create_alyx_tasks(rerun__status__in="__all__")

if DRY:
    _logger.info("dry run, not running task %s on session %s", task_dict["name"], session_path)
else:
    _logger.info("running task %s (id: %s) on session %s", task_dict["name"], task_dict["id"], session_path)
    task, registered_datasets = run_alyx_task(
        one=one,
        session_path=session_path,
        tdict=task_dict,
        location=LOCATION,
        mode="raise",
    )
    _logger.info(
        "task %s on session %s finished with status %s, %i datasets registered",
        task["name"],
        session_path,
        task["status"],
        len(registered_datasets or []),
    )
