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

process PHOTOMETRY_SYNC {
    container 'iblphotometry:nextflow'
    input:
    tuple val(session_path), val(experiment_description)
    script:
    """
    python /home/ubuntu/photometry_sync.py $session_path
    """
}


workflow {
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

    photometry_session_ch = PARSE_EXPERIMENT_DESCRIPTION(session_ch)
        .experiment_description_json
        .map { session_path, json_str ->
            [
                session_path: session_path,
                experiment_description: new groovy.json.JsonSlurper().parseText(json_str.trim())
            ]
        }
        .filter { it.experiment_description.devices?.containsKey('neurophotometrics') }

    PHOTOMETRY_SYNC(photometry_session_ch)
}