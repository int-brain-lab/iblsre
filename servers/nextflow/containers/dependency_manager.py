"""
this python program
monitors the subjects folder
whenenver a raw_session.flag is created
creates all alyx tasks for the session in the structure:

task.task_id.task_name.status

these are the statuses:
creates a file task.task_name.task_id.waiting_for_parents if the task has parents
creates a file task.task_name.ready if the task has no parents

whenever a task.task_name.task_id.completed is written
loop over all tasks that have .waiting_for_parents status
see if all their dependencies are matched
if yes, change status to .ready

nextflow looks for task.task_id.task_name.ready files
runs the task
writes to task.task_name.task_id.completed


if all are with .completed or .errored, exit
"""

import sys
import inotify.adapters
import shutil
from pathlib import Path
from one.api import ONE

one = ONE(cache_rest=None)

session_path = sys.argv[1]
notifier = inotify.adapters.InotifyTree(session_path)

eid = one.path2eid(session_path)
tasks = one.alyx.rest("tasks", "list", django=f"session__id,{eid}")
for task_dict in tasks:
    status = "ready" if len(task_dict["parent"]) == 0 else "waiting_for_parents"
    task_flagfile = f"task.{task_dict['id']}.{task_dict['name']}.{status}"
    Path(session_path) / task_flagfile.touch

print(f"Watching: {session_path}")


def get_flag_files(session_path):
    # TODO make that glob pattern robust (UUID)
    return list(session_path.glob("task.*.*.*"))


def get_parent_statuses(task_id, session_path):
    # get the parent statuses of a task id
    # on from disk, and not via alyx
    parent_ids = tasks[task_id]["parents"]
    statuses = []
    for flag_file in get_flag_files(session_path):
        _, name, task_id, status = flag_file.split(".")
        if task_id in parent_ids:
            statuses.append(status)
    # more compact, less readable

    # return [f.split('.')[2] for f in filter(lambda f: f.split('.')[2] in parent_ids, get_flag_files(session_path))]
    return statuses


# the main loop
for event in notifier.event_gen(yield_nones=False):
    (_, type_names, path, filename) = event
    if filename.startswith("task."):  # TODO better to a proper glob
        if type_names == ["IN_CLOSE_WRITE"]:  # emitted when file is closed
            _, task_id, task_name, status = filename.split(".")
            if status == "completed":
                # a task has finished. If so, check if this has any consequences for the
                # ones that are waiting for parents
                waiting_tasks = session_path.glob("task.*.*.waiting_for_parents")
                for waiting_task in waiting_tasks:
                    _, name, task_id, status = waiting_task.split(".")
                    if all(
                        [
                            status == "completed"
                            for status in get_parent_statuses(task_id, session_path)
                        ]
                    ):
                        # set this task to ready
                        shutil.move(filename, filename.with_suffix(".ready"))

            if status == "completed" or status == "errored":
                # a task completed or errored out
                # check if all are completed or errored
                # if so, quit
                all_statuses = [
                    flag_file.split(".")[2]
                    for flag_file in get_flag_files(session_path)
                ]
                if all([status in ["completed", "errored"] for status in all_statuses]):
                    sys.exit(0)
