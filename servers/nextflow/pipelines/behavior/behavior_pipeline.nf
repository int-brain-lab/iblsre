// Run the behaviour extraction of a session, modelled after photometry_pipeline.nf:
// the task graph is generated inside the container by the respective ibllib function
// (ibllib.pipes.dynamic_pipeline._get_trials_tasks), created on alyx and run there.
//
// This is the counterpart of resolve_trials_tasks.nf, which resolves the same task graph as
// native nextflow processes instead of leaving the loop to ibllib.

params.file      = null
params.watch_dir = null

// image that ships ibllib and behavior_extraction.py under /home/ubuntu/
params.container = 'internationalbrainlab/behavior:nextflow'

process PARSE_EXPERIMENT_DESCRIPTION {
    errorStrategy 'ignore'
    container params.container
    tag "${session_path}"

    input:
    val(session_path)

    output:
    tuple val(session_path), stdout, emit: experiment_description_json

    script:
    """
    python3 -c "
    import yaml, json
    with open('${session_path}/_ibl_experiment.description.yaml') as f:
        experiment_description = yaml.safe_load(f)
    print(json.dumps(experiment_description))
    "
    """
}

process BEHAVIOR_EXTRACTION {
    errorStrategy 'ignore'
    container params.container
    tag "${session_path}"

    input:
    tuple val(session_path), val(experiment_description)

    script:
    """
    python3 /home/ubuntu/behavior_extraction.py ${session_path}
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

    behavior_session_ch = PARSE_EXPERIMENT_DESCRIPTION(session_ch)
        .experiment_description_json
        .map { session_path, json_str ->
            [
                session_path: session_path,
                experiment_description: new groovy.json.JsonSlurper().parseText(json_str.trim())
            ]
        }
        // only sessions that actually have a behaviour protocol
        .filter { it.experiment_description.tasks }
        .map { session -> tuple(session.session_path, session.experiment_description) }

    BEHAVIOR_EXTRACTION(behavior_session_ch)
}
