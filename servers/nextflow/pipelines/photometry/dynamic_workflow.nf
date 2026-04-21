process PARSE_EXPERIMENT_DESCRIPTION {
    container 'ibllib:nextflow'
    input:
    val(session_path)

    output:
    tuple val(session_path), stdout,
     emit: experiment_description_json

    script:
    """
    python3 -c "
    import yaml, json
    with open('${session_path}/_ibl_experiment.description.yaml') as f:
        cfg = yaml.safe_load(f)
    print(json.dumps(cfg))
    "
    """
}

process PHOTOMETRY_SYNC_DAQ {
    container 'iblphotometry:nextflow'
    input:
    tuple val(session_path), val(experiment_description)
    // script: "echo would run a daq sync on $session_path"
    script:
    """
    python /home/ubuntu/photometry_sync.py $session_path
    """

}

process PHOTOMETRY_SYNC_BPOD {
    container 'iblphotometry:nextflow'
    input:
    tuple val(session_path), val(experiment_description)
    script: "echo would run a bpod sync on $session_path"
}

process PHOTOMETRY_SYNC_PASSIVE {
    container 'iblphotometry:nextflow'
    input:
    tuple val(session_path), val(experiment_description)
    script: "echo would run a passive sync on $session_path"
}


workflow {
    if (params.file) {
        session_ch = Channel
            .fromPath(params.file)
            .splitText() { it.trim() }
            .filter { it }
            .view()
    }

    experiment_ch = PARSE_EXPERIMENT_DESCRIPTION(session_ch)
        .experiment_description_json
        .map { session_path, json_str ->
            [
                session_path: session_path,
                experiment_description: new groovy.json.JsonSlurper().parseText(json_str.trim())
            ]
        }
        .map { session ->
            def tasks = session.experiment_description.tasks
            def task_name = tasks[0] instanceof Map ? tasks[0].keySet()[0] : tasks[0].toString()
            session + [protocol_count: tasks.size(), is_passive: task_name.toLowerCase().contains('passive')]
        }
        .branch {
            chained: it.protocol_count > 1
            passive: it.is_passive
            regular: true
        }
        .set { session_types }

    session_types.regular
        .map { it.subMap(['session_path', 'experiment_description']) } // strips the protocol_count is_passive flag
        .branch {
            daqami: it.experiment_description.devices.neurophotometrics.sync_mode == 'daqami'
            bpod:   it.experiment_description.devices.neurophotometrics.sync_mode == 'bpod'
        }
        .set { mode_branches }

    PHOTOMETRY_SYNC_DAQ(mode_branches.daqami)
    PHOTOMETRY_SYNC_BPOD(mode_branches.bpod)
}