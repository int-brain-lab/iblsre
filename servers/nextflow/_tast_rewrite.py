# %%
from pathlib import Path
from one.api import ONE
from ibllib.pipes.dynamic_pipeline import make_pipeline

BASE_FOLDER = Path("/mnt/s0/Data/Subjects")
one = ONE()
eid = "9119755e-39e0-43dd-a8ad-6313ead84092"
session_path = BASE_FOLDER / one.eid2path(eid).session_path_short()

pipe = make_pipeline(session_path, one=one)

# %%
for k, v in pipe.tasks.items():
    print(k, v)
