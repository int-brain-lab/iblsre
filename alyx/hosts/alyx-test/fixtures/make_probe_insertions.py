"""Build the probe insertion fixture for the alyx-test database.

The test database snapshot carries no probe insertions at all, which leaves ONE's insertion
tests with nothing to search. This adds a small set, attached to sessions that are already in
the snapshot, so no sessions, subjects or datasets are introduced and no existing counts move.

Every record is a real Open Alyx insertion - id, name, model and serial are taken verbatim.
Keeping the real ids matters: they are version 4, as Alyx generates, and `one.alf.spec.is_uuid`
accepts only versions 3 and 4, so a synthesised id (a uuid5, say) would be rejected as malformed
by ONE itself. Installing them as a fixture is what makes them stable - the id never changes.

Only the session is re-pointed, since the Open Alyx sessions these came from do not exist here.
"""
import json

# Probe models, from the init fixtures that load-init-fixtures.sh installs.
PROBE_MODEL = {
    '3A': '96dccdfe-7206-4b65-bb17-0743c842acd0',
    '3B2': '057d9a20-aaa9-4f79-8b0c-c8729b4cf160',
    'Fiber': '100fe998-986c-467d-aac8-a470e3a34341',
    'NP2.4': '6f586705-13a7-4c2a-ac4a-ef58b10d9bc4',
}
# Sessions already present in alyx_test.sql.
SESSION = {
    'ZFM-01935/2021-02-05/1': 'd3372b15-f696-4279-9be5-98f15783b5bb',   # mainenlab, ephys
    'KS005/2019-04-01/1': '01390fcc-4f86-4707-8a3b-4d9309feb0a1',       # cortexlab
    'KS005/2019-04-02/1': 'bc93a3b2-070d-47a8-a2b8-91b3b6e9f25c',       # cortexlab
    'KS005/2019-04-04/4': 'aaf101c3-2581-450a-8abd-ddb8f557a5ad',       # cortexlab
    'ZM_335/2019-07-17/1': 'dfe99506-b873-45db-bc93-731f9362e304',      # cortexlab
    'ZM_1743/2019-06-04/1': 'a9d89baf-9905-470c-8565-859ff212c7be',     # mainenlab
    'clns0730/2018-08-24/2': 'cf264653-2deb-44cb-aa84-89b82507028a',    # mainenlab
}
# (Open Alyx insertion id, name, model, serial, session to attach it to here). Eight is the
# floor rather than a preference: the pagination test needs more than five, then reaches
# pids[-2]. Two probes sit on the ephys session so that filtering by name has something to
# exclude; the rest spread across labs and models for the other filters.
ROWS = [
    ('47e735ca-f14a-44d3-bea0-0e6a5a771cd1', 'probe00', '3B2', '18194810662',
     'ZFM-01935/2021-02-05/1'),
    ('945ce18d-f27c-43cb-9341-a079090dd6b9', 'probe01', '3B2', '18194810662',
     'ZFM-01935/2021-02-05/1'),
    ('b83407f8-8220-46f9-9b90-a4c9f150c572', 'probe00', '3A', '641250420',
     'KS005/2019-04-01/1'),
    ('ad256265-03f2-4b4e-954b-0ba0c5cf6707', 'probe01', '3A', '641250947',
     'KS005/2019-04-02/1'),
    ('76ea0435-033c-4612-9e41-3241d9f283cd', 'probe00', '3B2', '18194810662',
     'KS005/2019-04-04/4'),
    ('6a45ae7c-490a-4814-9d77-583b3be3958d', 'probe00', '3B2', '18194810662',
     'ZM_335/2019-07-17/1'),
    ('bf746764-78e0-4b9c-bdf6-65b6ff45745d', 'probe00a', 'NP2.4', '20403320221',
     'ZM_1743/2019-06-04/1'),
    ('88c5b384-62d7-4bdc-a130-4883f210f018', 'fiber00', 'Fiber', 'fip_42_fiber00',
     'clns0730/2018-08-24/2'),
]

fixture = [
    {
        'model': 'experiments.probeinsertion',
        'pk': pk,
        'fields': {
            'name': name,
            'json': None,
            'session': SESSION[session],
            'model': PROBE_MODEL[model],
            'serial': serial,
            'chronic_insertion': None,
        },
    }
    for pk, name, model, serial, session in ROWS
]

if __name__ == '__main__':
    with open('probe_insertions.json', 'w') as f:
        json.dump(fixture, f, indent=2)
        f.write('\n')
    for pk, name, model, serial, session in ROWS:
        print(f'  {pk}  {session:<22} {name:<9} {model:<6} {serial}')
