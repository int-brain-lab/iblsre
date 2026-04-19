from typing import List, Dict
import sys
import inotify.adapters
import shutil
from pathlib import Path
from one.api import ONE


def DependencyManager():
    def __init__(self, task_ids_file: str | Path, one: ONE = one):
        self.task_ids_file = Path(task_ids_file)
        if not task_ids_file.exists():
            raise ValueError("task_ids file not found")

        with open(self.task_ids_file, "r") as fH:
            task_ids = [line.strip() for line in fH.readlines()]

        self.session_path = self.task_ids_file.parent

        for task_id in task_ids:
            task_dict = one.alyx.rest("task", "read", task_id)
            status = "ready" if len(task_dict["parent"]) == 0 else "waiting_for_parents"
            task_flagfile = f"task.{task_dict['id']}.{task_dict['name']}.{status}"
            self.session_path / task_flagfile.touch

    def get_flag_files(self) -> List[Path]:
        return list(
            self.session_path.glob("task.????????-????-????-????-????????????.*.*")
        )

    def get_states(self) -> Dict[str, str]:
        # get the states from the files as they are on disk right now
        states = {}
        for flag_file in self.get_flag_files():
            _, _, task_id, status = flag_file.split(".")
            states[task_id] = status
        return states

    def get_parent_states(self, task_id) -> Dict[str, str]:
        # get the parents of a task from alyx
        # and the status from the flag files from disk
        # (not via alyx)
        parent_ids = self.tasks[task_id]["parents"]
        states = self.get_states(self.session_path)
        return {id: states[id] for id in parent_ids}

    def get_waiting_tasks(self) -> Dict[str, str]:
        states = self.get_states(self)
        return {
            id: state for id, state in states.items() if state == "waiting_for_parents"
        }

    def run(self):
        # TODO logging
        print(f"Watching: {self.session_path}")
        notifier = inotify.adapters.InotifyTree(self.session_path)

        # the main loop
        for event in notifier.event_gen(yield_nones=False):
            (_, type_names, path, filename) = event
            if filename.startswith("task."):  # TODO regexping a UUID
                if type_names == ["IN_CLOSE_WRITE"]:  # emitted when file is closed
                    _, task_id, task_name, status = filename.split(".")
                    if status == "completed":
                        # a task has finished. If so, check if this has any consequences for the
                        # ones that are waiting for parents
                        waiting_tasks_ids = self.get_waiting_tasks().keys()
                        for task_id in waiting_tasks_ids:
                            states = self.get_parent_states(task_id).values()
                            if all([state == "completed" for state in states]):
                                # set this task to ready
                                shutil.move(filename, filename.with_suffix(".ready"))

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
    case 1:
        raise ValueError("no input file providede")
    case 2:
        task_ids_file = Path(sys.argv[1])
    case _:
        raise ValueError(f"too many input arguments: {sys.argv}")


one = ONE(cache_rest=None)
dependency_manager = DependencyManager(task_ids_file, one=ONE)
dependency_manager.run()
