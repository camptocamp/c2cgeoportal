#! /usr/bin/env python

from subprocess import check_call
from sys import argv
import psycopg2

# should also be the instance id
schemas = ["ai", "az", "bb", "bn", "br", "bu", "cb", "cn", "co", "cr", "ct", "ec", "ee", "epa", "ep", "es", "ey", "gg", "gn", "gr", "gv", "jp", "lc", "lr", "ly", "md", "nstcm", "ol", "oo", "ou", "pe", "px", "pz", "tr", "ts", "tz", "vc", "vy"]
# numer instance
instances = range(int(argv[1]))
instance_schema = [(str(instance), schemas[instance % len(schemas)]) for instance in instances]

def main():

    layers = {}
    layers_rules = {}
    p_n = {}

    for instance, schema in instance_schema):
        conn = psycopg2.connect("dbname=geoportal_dev")
        cur = conn.cursor()
        cur.execute("select t.name from {schema}.layer as l, {schema}.treeitem as t where l.id = t.id and l.\"layerType\" = 'internal WMS'".format(schema=schema))
        layers[schema] = []
        for record in cur:
            layers[schema].append(record[0])

        cur.execute("select t.name, l.\"legendRule\" from {schema}.layer as l, {schema}.treeitem as t where l.id = t.id and l.\"layerType\" = 'internal WMS' and  l.\"legendRule\" IS NOT NULL".format(schema=schema))
        layers_rules[schema] = []
        for record in cur:
            print record
            layers_rules[schema].append(record)

    layers_str = [
        '    "%s" => Array("%s")' % (schema, '", "'.join(layers[schema]))
        for instance, schema in instance_schema
    ]
    print "val layers = Map(\n" + ",\n".join(layers_str) + "\n)\n"

    layers_rules_str = [
        '    "%s" => Array("%s"),' % (instance, ', '.join(['("%s", "%s")' % l for l in layers_rules[schema]]))
        if len(layers_rules[schema]) else '    "%s" => Array[(String, String)](),' % (instance)
        '    "%s" => Array("%s")' % (instance, '", "'.join(layers[schema]))
        for instance, schema in instance_schema
    ]
    print "val layers_rules = Map(\n" + ",\n".join(layers_rules_str) + "\n)\n"


if __name__ == "__main__":
    main()
