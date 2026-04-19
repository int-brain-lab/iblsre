"""
for a given task ID
get the resources specifications from alyx
get the appropriate docker image
write it all to a json that will be parsed as process options for the nextflow process
"""

import sys
from pathlib import Path
from one.api import ONE
import json

LOCATION = "server"

match len(sys.argv):
    case 1:
        raise ValueError("no input task id provided")
    case 2:
        task_id = Path(sys.argv[1])
    case _:
        raise ValueError(f"too many input arguments: {sys.argv}")


def get_image(task_name):
    # to be implemented:
    # load the mapping, get the correct image
    return "iblphotometry:nextflow"


# get the task dict from alyx
one = ONE(cache_rest=None)
task_dict = one.alyx.rest("tasks", "read", task_id)

# resource specification
resources = {}

# CPU
resources["cpu"] = task_dict["cpu"]
# GPU
if task_dict["gpu"] > 0:
    # resources['gpu'] = task_dict['gpu]
    # TODO
    ...
# PRIORITY
resources["priority"] = task_dict["priority"]
# MEMORY
resources["memory"] = f"{task_dict['ram']} GB"
# IMAGE
resources["container"] = get_image(task_dict["name"])

# write json out
with open(f"{task_id}.requirements.json", "w") as fH:
    json.dump(resources, fH)
