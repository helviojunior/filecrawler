#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import yaml

with open('/etc/elasticsearch/elasticsearch.yml', 'r') as f:
    data = dict(yaml.load(f, Loader=yaml.FullLoader))
    '''
    network.host: 127.0.0.1
    http.host: 127.0.0.1
    http.port: 9200
    '''
    data.update({
        'network.host': '0.0.0.0',
        'network.publish_host': '127.0.0.1',
        'http.host': '0.0.0.0',
        'http.port': 9200,
        'cluster.name': 'filecrawler',
        'node.name': 'elk',
        'path.data': '/u01/es_data/',
        'xpack.security.enabled': False,
        'xpack.security.enrollment.enabled': False,
        'xpack.security.http.ssl': {'enabled': False},
        'xpack.security.transport.ssl': {'enabled': False}
    })

with open('/etc/elasticsearch/elasticsearch.yml', 'w') as f:
    yaml.dump(data, f, sort_keys=False, default_flow_style=False)

with open('/opt/kibana/config/kibana.yml', 'r') as f:
    kibana = dict(yaml.load(f, Loader=yaml.FullLoader))
    kibana.update({
        'server.host': '0.0.0.0',
        'server.port': 80,
    })

with open('/opt/kibana/config/kibana.yml', 'w') as f:
    yaml.dump(kibana, f, sort_keys=False, default_flow_style=False)

