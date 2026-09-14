# Nextflow pipelines

Session-level processing (photometry, behavior, video) run as Nextflow pipelines, with each
process executing inside a docker container. This document covers building the containers,
launching a pipeline, monitoring a run, and debugging a task.

Everything lives under `servers/nextflow/`:

```
containers/     docker images and the python entry scripts they ship
pipelines/      the nextflow workflows, one directory per modality
nf-debug.sh     recreate a failed task's container for interactive debugging
```


## Containers

### Layout

One directory per image, each holding a dockerfile, a `build.sh`, a `shell.sh`, and the python
entry scripts that the nextflow processes call.

| Directory | Image tag | Contents |
| --- | --- | --- |
| `containers/ibllib` | `internationalbrainlab/ibllib:nextflow` | base image: python venv, ibllib, vscode-server |
| `containers/iblphotometry` | `internationalbrainlab/iblphotometry:nextflow` | `ibl-photometry`, `photometry_sync.py` |
| `containers/behavior` | `internationalbrainlab/behavior:nextflow` | `behavior_extraction.py` |
| `containers/video` | `internationalbrainlab/video:nextflow` | ffmpeg, `video_extraction.py` |

All images derive `FROM internationalbrainlab/ibllib:nextflow`, so **build `ibllib` first** and
rebuild the derived images afterwards whenever the base changes.

The entry scripts are copied to `/home/ubuntu/` inside the image and all take a single session
path argument.

### build.sh

```shell
cd containers/ibllib
./build.sh                      # install the package from pypi
./build.sh my-feature-branch    # install from that git branch instead
./build.sh my-feature-branch --push
```

The optional positional argument is a git branch of the package the image is built around —
`ibllib` for the `ibllib` image, `ibl-photometry` for the `iblphotometry` image. Leave it out to
install the released version from pypi. It is passed to the dockerfile as a build arg.

`behavior` and `video` install no package of their own, so their `build.sh` takes `--push`
only — change their ibllib version by rebuilding the base image.

`--push` pushes to dockerhub after a successful build and requires an authenticated docker.

### shell.sh

Starts an interactive shell in the image with the same mounts the pipeline uses:

```shell
cd containers/iblphotometry
./shell.sh
```

- `-u $(id -u):$(id -g)` — run as the calling user, so files written to the data drive are not
  owned by root
- `-v /mnt/s0:/mnt/s0` — the data drive
- `-v /home/$USER/.one:/home/ubuntu/.one` — ONE credentials and config
- `-p 5678:5678` — the debug port

### VSCode version pin

`ibllib.dockerfile` installs a vscode-server at a pinned commit:

```dockerfile
ARG VSCODE_COMMIT=a44adf7f53e00964ab890f9f8758a334f1fc15bc
```

Attaching VSCode to a container only works if this matches your local VSCode build. Read the
current hash from Help → About, update the ARG, and rebuild when they drift apart.


## Pipeline

### Structure

Each modality has its own directory under `pipelines/` holding a `.nf` workflow and a
`nextflow.config`. The workflows follow the same three steps:

1. build a channel of session paths, from either `--file` or `--watch_dir`
2. `PARSE_EXPERIMENT_DESCRIPTION` reads `_ibl_experiment.description.yaml` in the container and
   emits it as json
3. filter on the parsed description, then run the extraction process for the sessions that pass

The photometry pipeline, for example, keeps only sessions whose description has a
`neurophotometrics` device, then calls `photometry_sync.py` on each.

`nextflow.config` enables docker and sets the run options — the same user mapping, data mount and
ONE config mount as `shell.sh`. Add environment variables for the containers there.

### Session input: --file or --watch_dir

Exactly one of the two is required; the workflow errors out if neither is given.

**`--file <path>`** — a text file with one session path per line. Batch mode: the run processes
those sessions and terminates.

```
/mnt/s0/Data/Subjects/CQ024/2026-08-14/001
/mnt/s0/Data/Subjects/CQ024/2026-08-15/001
```

**`--watch_dir <path>`** — watches the directory recursively for `**/raw_session.flag` files
being *created*, and takes the flag file's parent as the session path. Service mode: the run
does not terminate, it waits for new sessions indefinitely.

Two consequences of `watchPath` worth knowing: only files created *after* the run starts trigger
a task, and the run has to be stopped explicitly (Ctrl-C) — which also means `-resume` is for
`--file` runs.

### Launching

```shell
cd pipelines/photometry

# batch: process a list of sessions
nextflow run photometry_pipeline.nf --file sessions.txt

# service: watch for new sessions
nextflow run photometry_pipeline.nf --watch_dir /mnt/s0/Data/Subjects
```

Run from the pipeline's own directory so its `nextflow.config` is picked up. Useful flags:

| Flag | Effect |
| --- | --- |
| `-resume` | reuse cached results for tasks whose inputs are unchanged |
| `-with-tower` | stream execution data to Seqera Platform, see below |
| `-work-dir <path>` | put the `work/` directory elsewhere, e.g. on a scratch disk |
| `-bg` | detach, keep running after the terminal closes |

All processes use `errorStrategy 'ignore'`, so one failing session does not stop the run. Failed
tasks show up in the run report and their work directories stay on disk for debugging.


## Monitoring

### nextflow log

List past runs in the current directory:

```shell
nextflow log
```

Inspect the tasks of one run by its name (the `evil_darwin` style name from the launch output, or
`last` for the most recent):

```shell
nextflow log last -f name,status,exit,duration,workdir
nextflow log last -F "status == 'FAILED'" -f name,exit,workdir
```

`workdir` is what you feed to `nf-debug.sh`.

### Task output

Each task's work directory holds `.command.sh` (the script that ran), `.command.out` / `.command.err`
(its output), `.command.run` (the docker wrapper) and `.exitcode`.

`pipelines/combine_logs.sh` concatenates every `.command.out` of a run into one file with section
headers per task:

```shell
./combine_logs.sh ./work ./nf_logs_combined.txt
```

### Seqera Platform (-with-tower)

Add `-with-tower` to stream live execution data — per-task status, resource usage, logs — to a web
dashboard instead of reading the terminal.

```shell
export TOWER_ACCESS_TOKEN=<your token>
export TOWER_WORKSPACE_ID=<workspace id>     # omit for your personal workspace
nextflow run photometry_pipeline.nf --watch_dir /mnt/s0/Data/Subjects -with-tower
```

Generate the token under *Your tokens* in the Seqera Platform user menu. For a self-hosted
instance also set `TOWER_API_ENDPOINT` to its API url; it defaults to the public
`https://api.cloud.seqera.io`.

Note that this is not yet wired into the repo — no `tower` block exists in any `nextflow.config`.
To avoid exporting the variables on every launch, either put them in a shell profile or move the
settings into the config:

```groovy
tower {
    enabled = true
    accessToken = secrets.TOWER_ACCESS_TOKEN
}
```


## Debugging

### A python entry script, standalone

The quickest loop — no nextflow involved. Open a shell in the relevant container, attach VSCode
to it, and run the entry script on a session path.

1. **Open a shell** in the container:

   ```shell
   cd containers/iblphotometry
   ./shell.sh
   ```

2. **Connect VSCode**: Cmd/Ctrl+Shift+P → *Dev Containers: Attach to Running Container* → pick the
   container. Open the entry script under `/home/ubuntu/` and set breakpoints.

3. **Run the script** with a session path as its only argument, from the VSCode debugger (F5) or
   from the shell:

   ```shell
   python /home/ubuntu/photometry_sync.py /mnt/s0/Data/Subjects/CQ024/2026-08-14/001
   ```

### A failed nextflow task

`nf-debug.sh` rebuilds the container of a task that already ran, with its exact image, mounts and
working directory, and leaves it idling instead of executing the task:

```shell
./nf-debug.sh /path/to/work/4e/5f70e46e95bd16c38d331485533eb3
```

It reads `.command.run` for the docker invocation and `.command.sh` for the python call, writes a
matching `launch.json` into the container at `/home/ubuntu/.vscode/launch.json`, and starts the
container as `nf-debug`. Then attach VSCode as above and hit F5.

Environment variables it honours:

| Variable | Default | Effect |
| --- | --- | --- |
| `NF_DEBUG_NAME` | `nf-debug` | container name |
| `NF_DEBUG_PORT` | `5678` | published debug port |
| `NF_DEBUG_GIT_KEY` | unset | mount `~/.ssh` and set `GIT_SSH_COMMAND` with this key, for git inside the container |

When finished:

```shell
docker container stop nf-debug
```

### Gotcha: stopping inside debugpy at startup

If the debugger stops immediately with a `FileNotFoundError` on a path like
`/home/ubuntu/.local` or `<venv>/lib/python3.12/dist-packages`, with a stack ending in
`debugpy/common/log.py`, the exception is raised and handled *inside debugpy's own logging code* —
it is harmless.

You see it because **Raised Exceptions** is ticked in the BREAKPOINTS panel, and the generated
`launch.json` sets `"justMyCode": false` (needed to step into ibllib), which stops pydevd from
filtering out library frames. Untick *Raised Exceptions* and keep *Uncaught Exceptions*.
