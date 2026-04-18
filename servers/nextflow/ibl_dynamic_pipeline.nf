params.file      = null
params.watch_dir = null

process CREATE_ALYX_TASKS {
    priority = 0
    cpus 4
    memory '4 GB'
    container 'iblphotometry:nextflow'
    containerOptions "--cpus ${task.cpus}"
    // keeping stopped containers, verify if this works
    // afterScript 'if [ $? -eq 0 ]; then docker rm $NXF_BOXID; fi'

    input:
    val(session_path)

    output:
    path("task_ids.txt"), emit: ids_file

    script:
    """
    python /home/ubuntu/create_alyx_tasks.py $session_path
    """
}

process LAUNCH_DEPEDENCY_MANAGER {
    input:
    val(session_path)

    script:
    """
    python /home/ubuntu/dependency_manager.py $session_path
    """
}

process RUN_ALYX_TASK {
    cpus 8
    container 'ibllib:nextflow'
    containerOptions "--cpus ${task.cpus}"
    // keeping stopped containers, verify if this works
    // afterScript 'if [ $? -eq 0 ]; then docker rm $NXF_BOXID; fi'

    input:
    val(task_id)

    output:
    stdout

    script:
    """
    python /home/ubuntu/run_single_alyx_task.py $task_id
    """
}

process UPDATE_ALYX_TASK_LOG {
    input:
    val(task_id), val(log_lines)

    script:
    """
    python /home/ubuntu/update_alyx_task.py $task_id $log_file
    """
}

workflow {
    // Watch for raw_session.flag creation, emit the parent folder
    // pitfall: if the watch folder is passed with a trailing / this won't work
    if (params.file) {
        folders = Channel
            .fromPath(params.file)
            .splitText() { it.trim() }
            .filter { it }  // drop empty lines
            .map { session_path -> file(session_path) }
    } else if (params.watch_dir) {
        folders = Channel
            .watchPath("${params.watch_dir}/**/raw_session.flag", 'create')
            .map { flagFile -> file(flagFile).parent }
    } else {
        error "Either --file or --watch_dir must be provided"
    }

    folders.view {"processing session at: $it" }


    // For each session folder, create the alyx tasks, and the
    // task_ids.txt file
    // some clarification here:
    // the file is being copied out of the container into the nextflow working directory
    ids_file = CREATE_ALYX_TASKS(folders)

    // TODO here: integrate the dependency manager (on a session level)
    LAUNCH_DEPEDENCY_MANAGER(folders)

    // Split task_ids.txt into one channel item per ID
    task_ids = ids_file
        .splitText() { it.trim() }
        .filter { it }

    // For each ID, launch launch the alyx task

    // TODO get resources from alyx task dict and feed them into the RUN_ALYX_TASK call here
    // discovery process that looks for .ready tasks, and then feeds them to RUN_ALYX_TASK with
    // the resource and image specification

    RUN_ALYX_TASK(task_ids)

    // get the logs from the work folder
    // TODO figure out when the alyx task log is written in the normal case
    UPDATE_ALYX_TASK_LOG()
}

// we also needs 1 file that determines alyx_task:image (map)