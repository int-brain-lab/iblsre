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
# session_path = Path(sys.argv[1])
session_path = Path("/mnt/s0/georg/Data/Subjects/ZFM-09140/2025-08-28/001")

# if successful, register datasets

try:
    one = ONE(cache_rest=None)
    experiment_description = sess_params.read_params(session_path)

    tasks = get_photometry_tasks(
        experiment_description, session_path=session_path, one=one
    )
    pipeline = Pipeline(session_path=session_path, one=one)
    pipeline.tasks = tasks
    for task_dict in pipeline.create_alyx_tasks():
        run_alyx_task(
            one=one,
            session_path=session_path,
            tdict=task_dict,
            location=LOCATION,
            mode="raise",
        )
    # or
    # tasks = get_photometry_tasks(experiment_description)
    # for task in tasks:
    #     if not DRY:
    #         task.run()
    #     if REGISTER_DATASETS:
    #         if task.status == 0:
    #             registered_dsets = task.register_datasets(
    #                 location=LOCATION,
    #                 labs=one.alyx.rest("sessions", "read", task_dict["session"])["lab"],
    #         )
    # log and status

    sys.exit(0)
except Exception as e:
    print(e)
    sys.exit(1)
