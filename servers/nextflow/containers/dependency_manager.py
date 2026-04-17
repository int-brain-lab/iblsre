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
from ibllib.pipes.dynamic_pipeline import make_pipeline

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

# needs to look for

for event in notifier.event_gen(yield_nones=False):
    (_, type_names, path, filename) = event
    if filename.startswith("task."):  # TODO better to a proper glob
        if type_names == ["IN_CLOSE_WRITE"]:
            _, task_id, task_name, status = filename.split(".")
            # check if this leads to any of the child tasks with .waiting_for_parents -> .ready
            if status == ".waiting_for_parents":
                # check if all
                parent_statuses = []
                for parent_id in tasks[task_id]["parents"]:
                    for flagfile in session_path.glob("task.*"):
                        if parent_id in flagfile:
                            parent_statuses.append(flagfile.split(".")[-1])
                if all(parent_statuses):
                    shutil.move(filename, filename.with_suffix(".ready"))

            # check if all are either .completed or .errored
            # -> exit
