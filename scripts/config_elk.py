#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import yaml
import os


class CustomDumper(yaml.Dumper):
    def represent_data(self, data):
        if isinstance(data, str) and data.isdigit():
            return self.represent_scalar('tag:yaml.org,2002:str', data, style="'")

        return super(CustomDumper, self).represent_data(data)


with open('/etc/elasticsearch/elasticsearch.yml', 'r') as f:
    data = dict(yaml.load(f, Loader=yaml.FullLoader))
    '''
    network.host: localhost
    http.host: localhost
    http.port: 9200
    '''
    data.update({
        'network.host': 'localhost',
        'network.publish_host': '0.0.0.0',
        'http.host': '0.0.0.0',
        'http.port': 9200,
        'cluster.name': 'filecrawler',
        'node.name': 'filecrawler',
        'cluster.initial_master_nodes': ['filecrawler'],
        'path.data': '/u01/es_data/',
        'cluster.routing.allocation.disk.watermark.high.max_headroom': '6gb',
        'cluster.routing.allocation.disk.watermark.flood_stage.max_headroom': '6gb',
        'search.max_async_search_response_size': '100mb',
        'xpack.security.enabled': False,
        'xpack.security.enrollment.enabled': False,
        'xpack.security.http.ssl': {'enabled': False},
        'xpack.security.transport.ssl': {'enabled': False}
    })

with open('/etc/elasticsearch/elasticsearch.yml', 'w') as f:
    yaml.dump(data, f, sort_keys=False, default_flow_style=False, Dumper=CustomDumper)

for kb in ["/opt/kibana/config/kibana.yml", "/etc/kibana/kibana.yml"]:
    if os.path.exists(kb):
        with open(kb, 'r') as f:
            kibana = dict(yaml.load(f, Loader=yaml.FullLoader))
            kibana.update({
                'server.host': '0.0.0.0',
                'xpack.reporting.kibanaServer.hostname': 'localhost',
                'server.maxPayload': 104857600,
                'savedObjects.maxImportPayloadBytes': 104857600,
                'server.name': 'FileCrawler',
                'elasticsearch.hosts': ["http://localhost:9200"],
                'i18n.locale': 'en',
                'server.port': 5601,
            })

        with open(kb, 'w') as f:
            yaml.dump(kibana, f, sort_keys=False, default_flow_style=False, Dumper=CustomDumper)

