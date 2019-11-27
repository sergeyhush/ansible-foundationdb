#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2019 Snowflake

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: fdb_cluster

short_description: Configure FDB cluster configuration file

description:
    - FDB cluster module that allows creation and modification of cluster file.
    
author: Sergey Sudakovich <sergey.sudakovich@snowflake.com>

options:
    src:
        description:
            - Cluster file location
        default: /etc/foundationdb/fdb.cluster
        type: str
        
    description:
        description:
            - Logical of a database
        type: str
        
    id:
        description:
            - Arbitrary cluster ID. When creating new cluster file, if not specified, it will be autogenerated
        type: str
        
    coordinators:
        description:
            - List of IP:PORT pairs of coordination servers.
        type: list
    
    state:
        description:
            - state of coordinators for the cluster. By default, coordinator list will be overwritten. 
              Use `append` to append them to the coordinator list.
        choices: ['absent', 'present', 'append']
        required: false
        default: present
'''

EXAMPLES = '''
# View FDB cluster values
- name: create/update cluster with description
  fdb_cluster:
    src: "{{ etc_foundationdb_fdb_cluster }}"
  register: result
- debug: msg="Created cluster {{result.cluster_description}}:{{result.cluster_id}} with {{result.cluster_coordinators|length}} coordinator(s)"

- name: set coordinators
  fdb_cluster:
    coordinators: ['10.1.2.3:4519', '10.1.2.4:4519']

- name: append new coordinator
  fdb_cluster:
    coordinators: ['10.1.2.5:4519']
    state: append
'''

RETURN = '''
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
cluster_description:
    description: cluster description
    returned: always
    type: str
    sample: testCluster1
cluster_id:
    description: cluster ID
    returned: always
    type: str
    sample: c0wTV5CQ
'''

import re
from collections import Iterable

CLUSTER_STR_PTRN = re.compile(r"(\w*):(\w*)@((?:[\d\\.]*:\d+,?)+)$")


class InvalidClusterFile(Exception):
    pass


def read_cluster_file(path):
    """
    Read FDB cluster file

    :param path: FDB cluster file
    :return: cluster description, cluster ID, set of host:port tuples
    :raises: InvalidClusterFile
    """
    cluster_str = None
    with open(path) as f:
        for line in f.readlines():
            if not line or line.startswith == '#':
                continue
            cluster_str = line
            break
        else:
            raise InvalidClusterFile("Cluster file {0}: pattern not found".format(path))
    cluster_match = CLUSTER_STR_PTRN.match(cluster_str)
    if not cluster_match:
        raise InvalidClusterFile("Cluster file {0}: invalid format.".format(path))
    return cluster_match.group(1), cluster_match.group(2), set([x for x in cluster_match.group(3).split(',')])


def write_cluster_file(path, **kwargs):
    """
    Write cluster file

    Acceptable key value arguments:
    * coordinators
    * description
    * id

    :param path:
    :param kwargs:
    :return: None
    """
    if 'coordinators' in kwargs and isinstance(kwargs['coordinators'], Iterable):
        kwargs['coordinators'] = ','.join(kwargs['coordinators'])
    with open(path, 'w') as fp:
        fp.write("{description}:{id}@{coordinators}".format(**kwargs) + os.linesep)


def random_str(length=8):
    """ Return random string of specified length """
    import string
    import random

    choose_from = string.ascii_letters + string.ascii_uppercase + string.digits
    return ''.join(random.choice(choose_from) for _ in range(length))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            src=dict(type='str', default="/etc/foundationdb/fdb.cluster"),
            description=dict(type='str'),
            id=dict(type='str'),
            coordinators=dict(type='list'),
            state=dict(default="present", choices=["absent", "append", "present"])
        ),
        supports_check_mode=True,
    )

    params = module.params

    src = os.path.expanduser(params['src'])
    state = params['state']
    new_description = params.get('description')
    new_cluster_id = params.get('id')
    new_coordinators = set(params['coordinators'] or [])

    cur_description, cur_cluster_id, cur_coordinators = None, None, []
    if os.path.exists(src):
        try:
            cur_description, cur_cluster_id, cur_coordinators = read_cluster_file(src)
        except InvalidClusterFile:
            pass
    else:
        if any(not x for x in [new_description, new_coordinators]):
            module.fail_json(
                msg="When creating new cluster file, fields 'description', 'coordinators' must have values")

    description = new_description or cur_description
    cluster_id = new_cluster_id or cur_cluster_id or random_str()

    if state == 'absent':
        coordinators = cur_coordinators - new_coordinators
    elif state == 'append':
        coordinators = new_coordinators | cur_coordinators
    else:
        coordinators = new_coordinators if new_coordinators else cur_coordinators

    view_only = os.path.exists(src) and not (new_description or new_cluster_id or new_coordinators)
    do_write_cluster_file = (not module.check_mode and
                             not view_only and
                             (new_description != cur_description or
                              new_cluster_id != cur_cluster_id or
                              set(coordinators) != set(cur_coordinators)))
    changed = False
    if do_write_cluster_file:
        try:
            write_cluster_file(module.params['src'],
                               description=description,
                               id=cluster_id,
                               coordinators=coordinators)
            changed = True
        except IOError as err:
            module.fail_json(msg=err)

    result = dict(
        changed=changed,
        cluster_src=src,
        cluster_description=description,
        cluster_id=cluster_id,
        cluster_coordinators=list(coordinators),
        # FIXME remove debugs
        debug_cur_description=cur_description,
        debug_cur_id=cur_cluster_id,
        debug_new_description=new_description,
        debug_new_id=new_cluster_id,
        debug_new_coordinators=list(new_coordinators),
    )

    module.exit_json(**result)


from ansible.module_utils.basic import *

main()