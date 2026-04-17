"""
this python program
monitors the subjects folder
whenenver a raw_session.flag is created
creates all alyx tasks for the session in the structure:
task.task_name.task_id.status

these are the statuses:
creates a file task.task_name.task_id.waiting_for_parents if the task has parents
creates a file task.task_name.ready if the task has no parents

whenever a task.task_name.task_id.completed is written
loop over all tasks that have .waiting_for_parents status
see if all their dependencies are matched
if yes, change status to .ready

nextflow looks for task.task_name.task_id.ready files
runs the task
writes to task.task_name.task_id.completed
"""

import inotify.adapters
import sys
from pathlib import Path
from one.api import ONE
from ibllib.pipes.dynamic_pipeline import make_pipeline

one = ONE(cache_rest=None)

notifier = inotify.adapters.InotifyTree("/mnt/s0/georg/Data/Subjects/")

print("Watching... now touch a file")
for event in notifier.event_gen(yield_nones=False):
    (_, type_names, path, filename) = event
    if type_names == ["IN_CLOSE_WRITE"] and filename == "raw_session.flag":
        # raw_session.flag was created:
        pipeline = make_pipeline(path, one=one)
        tasks_alyx = pipeline.create_alyx_tasks()

        # create task ids and write them to a file
        task_ids = [task["id"] for task in tasks_alyx]
