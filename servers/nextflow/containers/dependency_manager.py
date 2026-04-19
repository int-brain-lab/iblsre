from typing import List, Dict
import sys
import inotify.adapters
import shutil
from pathlib import Path
from one.api import ONE
import pandas as pd
import time


class DependencyManager:
    def __init__(
        self,
        session_path: str | Path,
        task_ids_file: str | Path,
        one: ONE,
    ):
        self.session_path = Path(session_path)
        self.task_ids_file = Path(task_ids_file)
        if not task_ids_file.exists():
            raise ValueError("task_ids file not found")

        with open(self.task_ids_file, "r") as fH:
            task_ids = [line.strip() for line in fH.readlines()]

        self.task_dicts = {}
        for task_id in task_ids:
            task_dict = one.alyx.rest("tasks", "read", task_id)
            self.task_dicts[task_id] = task_dict
            status = (
                "ready" if len(task_dict["parents"]) == 0 else "waiting_for_parents"
            )
            task_flagfile = f"task.{task_dict['id']}.{task_dict['name']}.{status}"
            (self.session_path / task_flagfile).touch()

    def get_flag_files(self) -> List[Path]:
        return list(
            self.session_path.glob("task.????????-????-????-????-????????????.*.*")
        )

    def get_states(self) -> Dict[str, str]:
        # get the states from the files as they are on disk right now
        states = {}
        for flag_file in self.get_flag_files():
            _, task_id, _, status = str(flag_file).split(".")
            states[task_id] = status
        return states

    def run_polling(self):
        while True:
            states = self.get_states()
            waiting_task_ids = [
                task_id
                for task_id, task_status in states.items()
                if task_status == "waiting_for_parents"
            ]
            # get parents and check their states
            for waiting_task_id in waiting_task_ids:
                parent_ids = self.task_dicts[waiting_task_id]["parents"]
                if all([states[parent_id] == "completed" for parent_id in parent_ids]):
                    flag_file = next(
                        self.session_path.glob(
                            f"task.{waiting_task_id}.*.waiting_for_parents"
                        )
                    )
                    shutil.move(flag_file, flag_file.with_suffix(".ready"))

            # a task completed or errored out
            # check if all are completed or errored
            # if so, quit
            # states = self.get_states()
            if all([status in ["completed", "errored"] for status in states.values()]):
                self.shutdown()

            time.sleep(5)

    def run(self):
        # TODO logging
        print(f"Watching: {self.session_path}")
        notifier = inotify.adapters.InotifyTree(str(self.session_path))

        # the main loop
        for event in notifier.event_gen(yield_nones=False):
            if "IN_MOVED_TO" in event[1]:
                _, _, folder, filename = event
                if filename.startswith("task."):  # TODO regexping a UUID
                    _, task_id, task_name, status = filename.split(".")
                    if status == "completed":
                        # a task has finished. If so, check if this has any consequences for the
                        # ones that are waiting for parents
                        states = self.get_states()
                        waiting_task_ids = [
                            task_id
                            for task_id, task_status in states.items()
                            if task_status == "waiting_for_parents"
                        ]
                        # get parents and check their states
                        for waiting_task_id in waiting_task_ids:
                            parent_ids = self.task_dicts[waiting_task_id]["parents"]
                            if all(
                                [
                                    states[parent_id] == "completed"
                                    for parent_id in parent_ids
                                ]
                            ):
                                flag_file = next(
                                    self.session_path.glob(
                                        f"task.{waiting_task_id}.*.waiting_for_parents"
                                    )
                                )
                                shutil.move(flag_file, flag_file.with_suffix(".ready"))

                    if status == "completed" or status == "errored":
                        # a task completed or errored out
                        # check if all are completed or errored
                        # if so, quit
                        states = self.get_states()
                        if all(
                            [
                                status in ["completed", "errored"]
                                for status in states.values()
                            ]
                        ):
                            self.shutdown()

    def shutdown(self):
        sys.exit(0)


match len(sys.argv):
    # case 1:
    #     raise ValueError("no input file providede")
    case 3:
        session_path = Path(sys.argv[1])
        task_ids_file = Path(sys.argv[2])
    case _:
        raise ValueError(f"input arguments error: {sys.argv}")

# session_path = Path("/mnt/s0/georg/Data/Subjects/ZFM-09140/2025-08-26/001")
# task_ids_file = session_path / "task_ids.txt"
one = ONE(cache_rest=None)
dependency_manager = DependencyManager(session_path, task_ids_file, one)
dependency_manager.run_polling()
