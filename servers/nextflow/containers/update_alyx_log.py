import sys
from one.api import ONE

one = ONE(cache_rest=None)

task_id = sys.argv[1]
log_file = sys.argv[2]  # this will not work because of line breaks
with open(log_file, "r") as fH:
    log_lines = fH.readlines()
one.alyx.rest("tasks", "partial_update", task_id, data={"log": log_lines})
