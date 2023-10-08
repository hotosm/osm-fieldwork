# Osmfile.py

Osmfile.py is a Python module that provides functionality for writing
OpenStreetMap (OSM) XML format output files. It is used as part of the
osm-fieldwork toolset, and can be used as part of a larger Python
application. Currently it is only used by the CSVDump.py program.

When used, osmfile.py takes a Python data structure containing OSM
data as input and generates an OSM XML format output file. The data
structure consists of nested Python dictionaries and lists, with each
dictionary representing an OSM node, way or relation, and each list
representing a set of nodes, ways or relations.

For example, consider the following Python data structure representing
a single OSM node:

    node = {
        'id': 1234,
        'lat': 51.5074,
        'lon': -0.1278,
        'tags': {
            'name': 'Big Ben',
            'amenity': 'clock'
        }
    }

To write this node to an OSM XML format output file using osmfile.py,
you would first create a new osmfile.OsmWriter object, and then call
the `write()` method, passing in the node dictionary as an
argument:

    from osmfile import OsmFile

    writer = OsmFile('output.osm')
    node_xml = writer.createNode(node)
    way_xml = writer.createWay(way)
    relation_xml = writer.createRelation(relation)
    writer.add_tag('1234', 'amenity', 'post_office')
    writer.write(node_xml)
    writer.write(way_xml)
    writer.write(relation_xml)
    writer.close()

This would create XML code for the node, way, and relation using
createNode(), createWay(), and createRelation() respectively. These
methods return a string of XML code which is then written to the
output file using _writer.write()_. The add_tag() method can be used to
add additional tags to any of the elements being written to the file.

    <node id="1234" lat="51.5074" lon="-0.1278">
    <tag k="name" v="Big Ben"/>
    <tag k="amenity" v="clock"/>
    </node>

Osmfile.py also provides methods for writing OSM ways and relations to
output files, and for adding tags to existing OSM nodes, ways and
relations.

To write an OSM way to an output file, you would create a dictionary
representing the way, with a `nodes` key containing a list of the node
IDs that make up the way. For example:

    way = {
        'id': 5678,
        'nodes': [1234, 5678, 9012],
        'tags': {
            'name': 'Oxford Street',
            'highway': 'primary'
        }
    }

    writer.write_way(way)

This would write the following XML code to the output file:

    <way id="5678">
        <nd ref="1234"/>
        <nd ref="5678"/>
        <nd ref="9012"/>
        <tag k="name" v="Oxford Street"/>
        <tag k="highway" v="primary"/>
    </way>

To write an OSM relation to an output file, you would create a
dictionary representing the relation, with a `members` key containing
a list of dictionaries representing the members of the relation. Each
member dictionary should have `type`, `ref` and `role` keys,
specifying the type of OSM object (node, way or relation), the ID of
the object, and the role of the object in the relation. For example:

    relation = {
        'id': 7890,
        'members': [
            {'type': 'way', 'ref': 5678, 'role': 'outer'},
            {'type': 'node', 'ref': 1234, 'role': 'admin_centre'}
        ],
        'tags': {
            'name': 'London Borough of Westminster',
            'type': 'boundary'
        }
    }

    writer.write_relation(relation)

This would write the following XML code to the output file:

    <relation id="7890">
        <member type="way" ref="5678" role="outer"/>
        <member type="node" ref="1234" role="admin_centre"/>
        <tag k="name" v="London Borough of Westminster"/>
        <tag k="type" v="boundary"/>
    </relation>

In addition to writing new OSM objects to an output file, osmfile.py
also provides methods for adding tags to existing objects. To add a
tag to an OSM object, you would call the `add_tag()` method, passing
in the object's ID, the tag key and the tag value:

    writer.add_tag('1234', 'amenity', 'post_office')

This would add the following XML code to the output file, as a child
of the existing `node` element with ID `1234`:

    <tag k="amenity" v="post_office"/>

Note that the `OsmWriter` class also provides methods for closing the
output file and flushing any buffered data to disk. You should call
the `close()` method once you have finished writing all of your OSM
data to the output file.
