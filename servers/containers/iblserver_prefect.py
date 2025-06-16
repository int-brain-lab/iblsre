"""Pipeline entry script.

This script searches for new sessions (those with a raw_session.flag file), and creates the pipeline
preprocessing tasks in Alyx. No file registration takes place in this script.
"""

import asyncio
import traceback
import datetime
import logging
from pathlib import Path
import subprocess

from pydantic import Field
from pydantic_settings import BaseSettings

from prefect import flow, task, deploy, get_client
from prefect.client.schemas.objects import ConcurrencyLimitConfig, ConcurrencyLimitStrategy
from prefect.client.schemas.filters import FlowRunFilter

from one.api import ONE
from one.webclient import AlyxClient
from one.remote.globus import get_local_endpoint_id

from ibllib.pipes.local_server import task_queue, report_health, job_creator
from ibllib.pipes.tasks import run_alyx_task
from ibllib.pipes.base_tasks import Task

MAX_TASKS = 10
_logger = logging.getLogger('ibllib')
subjects_path = Path('/mnt/s0/Data/Subjects/')




async def delete_cancelled_runs(max_duration_seconds=20):
    async with get_client() as client:
        # Fetch completed flow runs
        flow_runs = await client.read_flow_runs(
            flow_run_filter=FlowRunFilter(
                state=dict(type=dict(any_=["CANCELLED"]))
            )
        )
        for run in flow_runs:
            await client.delete_flow_run(flow_run_id=run.id)
            print(f"Deleted run {run.name} with state {run.state}")


async def delete_short_runs(max_duration_seconds=20):
    async with get_client() as client:
        # Fetch completed flow runs
        flow_runs = await client.read_flow_runs(
            flow_run_filter=FlowRunFilter(
                state=dict(type=dict(any_=["COMPLETED"]))
            )
        )
        for run in flow_runs:
            # Calculate run duration
            duration = run.end_time - run.start_time
            if duration < datetime.timedelta(seconds=max_duration_seconds):
                # Delete the short run
                await client.delete_flow_run(flow_run_id=run.id)
                print(f"Deleted run {run.name} with duration {duration.total_seconds()} seconds")



class JobCreator(Task):
    """A task for creating session preprocessing tasks."""
    level = 0
    priority = 100
    io_charge = 20

    def __init__(self, subjects_path, **kwargs):
        """A task for creating session preprocessing tasks.

        Parameters
        ----------
        subjects_path : pathlib.Path
            The root path containing the sessions to register.
        """
        self.subjects_path = subjects_path
        self.pipes = []
        super().__init__(None, **kwargs)

    def _run(self):
        # Label the lab endpoint json field with health indicators
        try:
            report_health(self.one.alyx)
            _logger.info('Reported health of local server')
        except BaseException:
            _logger.error(f'Error in report_health\n {traceback.format_exc()}')

        #  Create sessions: for this server, finds the extract_me flags, identify the session type,
        #  create the session on Alyx if it doesn't already exist, register the raw data and create
        #  the tasks backlog
        pipes, _ = job_creator(self.subjects_path, one=self.one, dry=False)
        self.pipes.extend(pipes)
        _logger.info('Ran job creator.')


def get_repo_from_endpoint_id(endpoint=None, alyx=None):
    """
    Extracts data repository name associated with a given a Globus endpoint UUID.

    Parameters
    ----------
    endpoint : uuid.UUID, str
        Endpoint UUID, optional if not given will get attempt to find local endpoint UUID.
    alyx : one.webclient.AlyxClient
        An instance of AlyxClient to use.

    Returns
    -------
    str
        The data repository name associated with the endpoint UUID.
    """
    alyx = alyx or AlyxClient(silent=True)
    if not endpoint:
        endpoint = get_local_endpoint_id()
    repo = alyx.rest('data-repository', 'list', globus_endpoint_id=endpoint)
    if any(repo):
        return repo[0]['name']


def run_job_creator_task(one=None, data_repository_name=None, root_path=subjects_path):
    """Run the JobCreator task.

    Parameters
    ----------
    one : one.api.OneAlyx
        An instance of ONE to use.
    data_repository_name : str
        The associated data repository name. If None, this is determined from the local Globus
        endpoint ID.
    root_path : pathlib.Path
        The root path containing the sessions to register.

    Returns
    -------
    JobCreator
        The run JobCreator task.
    """
    one = one or ONE(cache_rest=None, mode='remote')
    data_repository_name = data_repository_name or get_repo_from_endpoint_id(alyx=one.alyx)
    tasks = one.alyx.rest(
        'tasks', 'list', name='JobCreator', django=f'data_repository__name,{data_repository_name}', no_cache=True)
    assert len(tasks) < 2
    if not any(tasks):
        t = JobCreator(root_path, one=one, clobber=True)
        task_dict = {
            'executable': 'deploy.serverpc.crontab.report_create_jobs.JobCreator',
            'priority': t.priority, 'io_charge': t.io_charge, 'gpu': t.gpu, 'cpu': t.cpu,
            'ram': t.ram, 'module': 'deploy.serverpc.crontab.report_create_jobs',
            'parents': [], 'level': t.level, 'status': 'Empty', 'name': t.name, 'session': None,
            'graph': 'Base', 'arguments': {}, 'data_repository': data_repository_name}
        talyx = one.alyx.rest('tasks', 'create', data=task_dict)
    else:
        talyx = tasks[0]
        tkwargs = talyx.get('arguments') or {}  # if the db field is null it returns None
        t = JobCreator(root_path, one=one, taskid=talyx['id'], clobber=True, **tkwargs)

    one.alyx.rest('tasks', 'partial_update', id=talyx['id'], data={'status': 'Started'})
    status = t.run()
    patch_data = {
        'time_elapsed_secs': t.time_elapsed_secs, 'log': t.log, 'version': t.version,
        'status': 'Empty' if status == 0 else 'Errored'}
    t = one.alyx.rest('tasks', 'partial_update', id=talyx['id'], data=patch_data)
    return t


def _get_jobs(mode, env=(None,), max_tasks=MAX_TASKS):
    one = ONE(cache_rest=None)
    waiting_tasks = task_queue(mode=mode, lab=None, alyx=one.alyx, env=env)
    
    futures = []
    last_session = None
    c = 0
    for tdict in waiting_tasks:
        if c >= max_tasks:
            break
        # In the case of small tasks we run a set of them at a time before re-querying
        # Often they are from the same session, so we cache the session path between tasks
        if last_session != tdict['session']:
            ses = one.alyx.rest('sessions', 'list', django=f"pk,{tdict['session']}")[0]
            session_path = Path(subjects_path).joinpath(
                ses['subject'], ses['start_time'][:10], str(ses['number']).zfill(3))
            last_session = tdict['session']
        # Here we also want to make sure the task has no missing dependency
        if len(tdict['parents']):
            job_deck = one.alyx.rest('tasks', 'list', session=tdict['session'], no_cache=True)
            parent_tasks = filter(lambda x: x['id'] in tdict['parents'], job_deck)
            parent_statuses = [j['status'] for j in parent_tasks]
            # if any of the parent tasks is not complete, throw a warning
            if not set(parent_statuses) <= {'Complete', 'Incomplete'}:
                _logger.warning(f"{tdict['name']} has unmet dependencies")
                continue
        # It is useful to label each task as best we can to handle concurrency at a global level
        extra_tags = []
        if tdict['gpu'] > 0:
            extra_tags.append('gpu')
        job_name = f"{session_path.relative_to(subjects_path)} {tdict['name']} {tdict['id']}"
        _logger.info(f"Submitting task {job_name}")
        dynamic_task = task(
            name=job_name,
            tags=[f"{mode}_jobs"] + extra_tags,
            )(run_alyx_task)
        futures.append(dynamic_task.submit(tdict=tdict, session_path=session_path, one=one, mode='raise'))
        c += 1
    return futures


def list_available_envs(root=Path.home() / 'Documents/PYTHON/envs'):
    """
    List all the envs within `root` dir.

    Parameters
    ----------
    root : str, pathlib.Path
        The directory containing venvs.

    Returns
    -------
    list of str
        A list of envs, including None (assumed to be base iblenv).
    """
    try:
        envs = filter(Path.is_dir, Path(root).iterdir())
        return [None, *sorted(x.name for x in envs)]
    except FileNotFoundError:
        return [None]


@flow(log_prints=True)
def small_jobs():
    for future in _get_jobs(mode='small', max_tasks=120):
        future.wait()

@flow(log_prints=True)
def large_jobs():
    for future in _get_jobs(mode='large', max_tasks=25):
        future.wait()

@flow(log_prints=True)
def iblsorter_jobs():
    for future in _get_jobs(mode='large', env=['iblsorter'], max_tasks=1):
        future.wait()

@flow(log_prints=True)
def video_jobs():
    for future in _get_jobs(mode='large', env=['dlc'], max_tasks=1):
        future.wait()

@flow(log_prints=True)
def create_jobs():
    print('starting job creation task')
    run_job_creator_task()
    print('Clean up')
    asyncio.run(delete_short_runs())
    asyncio.run(delete_cancelled_runs())
    # # also remove all dangling containers older than one week
    # command = ["docker", "container", "prune", "--filter", "until=168h", "--force"]
    # subprocess.run(command, capture_output=True, text=True, check=True)
    # print('Pruned containers older than a week')


class CommandLineArguments(BaseSettings, cli_parse_args=True):
    """
    import sys
    sys.argv = ['iblserver_prefect.py', '--scratch_directory', '/home']
    print(CommandLineArguments().model_dump())
    """
    scratch_directory: Path = Field(description='Scratch directory - SSD drive', default='/mnt/s1')


if __name__ == "__main__":
    """
    python iblserver_prefect.py --scratch_directory /mnt/s1
    """
    args = CommandLineArguments()  # this parses input arguments
    kwargs_job_variables = dict(
        volumes=[
            '/mnt/s0:/mnt/s0',
            '/home/ibladmin/.one:/home/ibladmin/.one',
            '/home/ibladmin/.globusonline:/home/ibladmin/.globusonline',
            f'{args.scratch_directory}:/scratch',
            ],
        user='ibladmin',
        image_pull_policy='Never',  # this makes sure we use the local image, allowing for canaries
        run_config={'remove': True}  # this makes sure the containers are removed after a run. this doesn't work FIXME
        )
    kwargs_deploy = dict(
        work_pool_name="iblserver-docker-pool",
        push=False,
        build=False,
    )

    deploy(
        create_jobs.to_deployment(
            name="iblserver-create-jobs",
            job_variables=kwargs_job_variables,
            concurrency_limit=ConcurrencyLimitConfig(
                limit=1,
                collision_strategy=ConcurrencyLimitStrategy.CANCEL_NEW
                ),
            interval=datetime.timedelta(minutes=20)
            ),
        small_jobs.to_deployment(
            name='iblserver-small-jobs',
            job_variables=kwargs_job_variables,
            concurrency_limit=ConcurrencyLimitConfig(
                limit=1,
                collision_strategy=ConcurrencyLimitStrategy.CANCEL_NEW
                ),
            interval=datetime.timedelta(minutes=120)
            ),
        large_jobs.to_deployment(
            name='iblserver-large-jobs',
            job_variables=kwargs_job_variables,
            concurrency_limit=ConcurrencyLimitConfig(
                limit=1,
                collision_strategy=ConcurrencyLimitStrategy.CANCEL_NEW
                ),
            interval=datetime.timedelta(minutes=420)
            ),
        image="internationalbrainlab/ibllib:latest",
        **kwargs_deploy
    )
    deploy(
        iblsorter_jobs.to_deployment(
            name='iblserver-iblsorter-jobs',
            job_variables=kwargs_job_variables,
            concurrency_limit=ConcurrencyLimitConfig(
                limit=1,
                collision_strategy=ConcurrencyLimitStrategy.CANCEL_NEW
                ),
            interval=datetime.timedelta(minutes=60 * 4)
            ),
        image="internationalbrainlab/iblsorter:latest",
        **kwargs_deploy
        )
    deploy(
        video_jobs.to_deployment(
            name='iblserver-dlc-jobs',
            job_variables=kwargs_job_variables,
            concurrency_limit=ConcurrencyLimitConfig(
                limit=1,
                collision_strategy=ConcurrencyLimitStrategy.CANCEL_NEW
                ),
            # interval=datetime.timedelta(minutes=60 * 6)
            ),
        image="internationalbrainlab/dlc:latest",
        **kwargs_deploy
        )
