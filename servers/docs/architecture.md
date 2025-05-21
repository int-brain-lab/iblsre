# Architecture

## Prefect Job Orchestration

A job orchestration system called `prefect` runs on each of the servers.

The orchestration consists in a **prefect server**, that runs within a docker container with a postgres container backend. The running of those processes is described in the [docker compose](../docker-compose.yaml) file.

This orchestration will run a **prefect worker** in a `tmux` (TODO: should be upgraded as a full blown-service). The worker is designed to deploy **flows** from the [iblserver_prefect.py](../containers/iblserver_prefect.py). Each flow will run at intervals in a **deployment**. Each **deployment** matches a single docker container:
    - `iblserver-create-jobs` in the `ibllib` container
    - `iblserver-dlc-jobs` in the `dlc` container
    - `iblserver-iblsorter-jobs` in the `iblsorter` container
    - `iblserver-large-jobs` in the `ibllib` container
    - `iblserver-small-jobs` in the `ibllib` container

Each **flow**, within its **deployment**, will run several **tasks** that correspond to our ibllib/alyx tasks. We control the **concurrency** of those executions at 2 levels:
- each **deployment** can only run one **flow** at a time
- each **task** has a label, and we control concurrency as follows:
   - `small-tasks` 10 concurrent runs
   - `large-tasks` 3 concurrent runs
   - `gpu` 1 concurrent run.
Note that the task level concurrency setting applies to all tasks within a **prefect worker**, regardless of its **deployment/container**.


## Docker images and containers

