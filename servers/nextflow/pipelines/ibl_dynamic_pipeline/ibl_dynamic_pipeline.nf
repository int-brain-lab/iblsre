params.file      = null
params.watch_dir = null

process CREATE_ALYX_TASKS {
    priority = 0
    cpus 1
    memory '4 GB'
    container 'internationalbrainlab/iblphotometry:nextflow'
    // keeping stopped containers, verify if this works
    // afterScript 'if [ $? -eq 0 ]; then docker rm $NXF_BOXID; fi'

    input:
    val(session_path)

    output:
    tuple val(session_path), path("task_ids.txt"), emit: out

    script:
    """
    python /home/ubuntu/create_alyx_tasks.py $session_path
    """
}

process LAUNCH_DEPEDENCY_MANAGER {
    priority = 0
    cpus 4
    memory '4 GB'
    container 'internationalbrainlab/iblphotometry:nextflow'
    input:
    tuple val(session_path), path(task_ids_file)

    output:
    tuple val(session_path), path(task_ids_file), emit: out

    script:
    """
    python /home/ubuntu/dependency_manager.py $session_path $task_ids_file
    """
}

process GET_ALYX_TASK_REQUIREMENTS {
    priority = 0
    cpus 1
    memory '4 GB'
    container 'internationalbrainlab/iblphotometry:nextflow'
    input:
    tuple val(session_path), val(task_id)

    output:
    tuple val(session_path), val(task_id), path("${task_id}.requirements.json"), emit: out

    script:
    """
    python /home/ubuntu/get_alyx_task_requirements.py $task_id
    """
}

process WAIT_FOR_FLAG {
    container 'internationalbrainlab/iblphotometry:nextflow'
    input:
    tuple val(session_path), val(task_id), val(resources)

    output:
    tuple val(session_path), val(task_id), val(resources), emit:out

    script:
    """
    while ! ls ${session_path}/task.${task_id}.*.ready 1>/dev/null 2>&1; do
        sleep 1
    done
    """
}

process RUN_ALYX_TASK {
    memory { resources.memory as nextflow.util.MemoryUnit }
    cpus   { resources.cpus }
    time   { resources.time as nextflow.util.Duration }
    container { resources.container }
    containerOptions "--cpus ${task.cpus}"
    // TODO
    // this was suggested but doesn't work
    // afterScript 'if [ $? -eq 0 ]; then docker rm $NXF_BOXID; fi'

    input:
    tuple val(session_path), val(task_id), val(resources)

    output:
    stdout // to be determined how to deal with the logging

    script:
    """
    python /home/ubuntu/run_single_alyx_task.py $session_path $task_id
    """
}

// process UPDATE_ALYX_TASK_LOG {
//     input:
//     val(task_id), val(log_lines)

//     script:
//     """
//     python /home/ubuntu/update_alyx_task.py $task_id $log_file
//     """
// }

workflow {
    // Watch for raw_session.flag creation, emit the parent folder
    // pitfall: if the watch folder is passed with a trailing / this won't work
    if (params.file) {
        session_ch = Channel
            .fromPath(params.file)
            .splitText() { it.trim() }
            .filter { it }
            .map { session_path -> file(session_path).toString() }
    } else if (params.watch_dir) {
        session_ch = Channel
            .watchPath("${params.watch_dir}/**/raw_session.flag", 'create')
            .map { session_path -> file(session_path).parent.toString() }
    } else {
        error "Either --file or --watch_dir must be provided"
    }

    session_ch.view {"processing session at: $it" }

    // For each session folder
    // create the alyx tasks -> outputs a file with the task_ids
    // launch the dependency manager -> reads the file and manages those tasks

    create_ch = CREATE_ALYX_TASKS(session_ch)
    manager_ch = LAUNCH_DEPEDENCY_MANAGER(create_ch.out)

    // Split task_ids.txt into one channel item per ID
    tasks_ch = create_ch.out
        .flatMap { session_path, task_ids_file ->
            task_ids_file.readLines()
                .collect { it.trim() }
                .findAll { it }
                .collect { task_id -> [session_path, task_id] }
        }

    // For each ID, first get the required resources from alyx
    tasks_resources_ch = GET_ALYX_TASK_REQUIREMENTS(tasks_ch).out
        .map { session_path, task_id, requirements_file ->
            def resources = new groovy.json.JsonSlurper().parseText(requirements_file.text)
            return [session_path, task_id, resources]
        }

    // For each task_id, create a watch for its specific flag file
    // flag_ch = tasks_resources_ch
    //     .flatMap { session_path, task_id, resources ->
    //         Channel.watchPath("${session_path}/task.${task_id}.*.ready")
    //             .take(1)
    //             .map { flag_file -> [session_path, task_id, resources] }
    //     }

    flag_ch = WAIT_FOR_FLAG(tasks_resources_ch)
    RUN_ALYX_TASK(flag_ch.out)

    // UPDATE_ALYX_TASK_LOG(tasks_run_ch)

    // get the logs from the work folder
    // TODO figure out when the alyx task log is written in the normal case

}
