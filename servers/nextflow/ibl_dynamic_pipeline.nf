params.file      = null
params.watch_dir = null

process CREATE_ALYX_TASKS {
    priority = 0
    cpus 1
    memory '4 GB'
    container 'ibllib:nextflow'
    // keeping stopped containers, verify if this works
    // afterScript 'if [ $? -eq 0 ]; then docker rm $NXF_BOXID; fi'

    input:
    val(session_path)

    output:
    tuple val(session_path), path("task_ids.txt")

    script:
    """
    python /home/ubuntu/create_alyx_tasks.py $session_path
    """
}

process LAUNCH_DEPEDENCY_MANAGER {
    input:
    tuple val(session_path), path(task_ids_file)

    output:
    tuple val(session_path), path(task_ids_file)

    script:
    """
    python /home/ubuntu/dependency_manager.py $task_ids_file
    """
}

process GET_ALYX_TASK_REQUIREMENTS {
    input:
    tuple val(session_path), val(task_id)

    output:
    tuple val(session_path), val(task_id), path("${task_id}.requirements.json")

    script:
    """
    python /home/ubuntu/get_task_requirements.py $task_id
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
    python /home/ubuntu/run_single_alyx_task.py $task_id
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
            .map { session_path -> file(flagFile).parent.toString() }
    } else {
        error "Either --file or --watch_dir must be provided"
    }

    session_ch.view {"processing session at: $it" }

    // For each session folder
    // create the alyx tasks -> outputs a file with the task_ids
    // launch the dependency manager -> reads the file and manages those tasks

    create_ch = CREATE_ALYX_TASKS(session_ch)    
    manager_ch = LAUNCH_DEPEDENCY_MANAGER(create_ch.out)

    // NOTE?? to not forget here: the dependency manager acutally needs to
    // "pass through" the task_ids file because I need to split them into tasks
    // AFTER the manager has been created

    // Split task_ids.txt into one channel item per ID
    tasks_ch = manager_ch.out
        .flatMap { session_path, task_ids_file ->
            task_ids_file.readLines()
                .collect { it.trim() }
                .findAll { it }
                .collect { task_id -> [session_path, task_id] }
        }

    // For each ID, first get the required resources from alyx
    // stores in a json, but is emitted 
    tasks_resources_ch = GET_ALYX_TASK_REQUIREMENTS(tasks_ch).out
        .map { session_path, task_id, requirements_file ->
            def resources = new groovy.json.JsonSlurper().parseText(requirements_file.text)
            return [session_path, task_id, resources]
        }

    // For each task_id, create a watch for its specific flag file
    flag_ch = tasks_resources_ch
        .flatMap { session_path, task_id, resources ->
            Channel.watchPath("${session_path}/task.${task_id}.*.ready")
                .take(1)
                .map { flag_file -> [session_path, task_id, resources] }
        }

    tasks_run_ch = RUN_ALYX_TASK(flag_ch) 

    // UPDATE_ALYX_TASK_LOG(tasks_run_ch)

    // get the logs from the work folder
    // TODO figure out when the alyx task log is written in the normal case

}
