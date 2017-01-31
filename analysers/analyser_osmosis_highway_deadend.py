#!/usr/bin/env python
#-*- coding: utf-8 -*-

###########################################################################
##                                                                       ##
## Copyrights Frédéric Rodrigo 2012                                      ##
##                                                                       ##
## This program is free software: you can redistribute it and/or modify  ##
## it under the terms of the GNU General Public License as published by  ##
## the Free Software Foundation, either version 3 of the License, or     ##
## (at your option) any later version.                                   ##
##                                                                       ##
## This program is distributed in the hope that it will be useful,       ##
## but WITHOUT ANY WARRANTY; without even the implied warranty of        ##
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         ##
## GNU General Public License for more details.                          ##
##                                                                       ##
## You should have received a copy of the GNU General Public License     ##
## along with this program.  If not, see <http://www.gnu.org/licenses/>. ##
##                                                                       ##
###########################################################################

from Analyser_Osmosis import Analyser_Osmosis

sql10 = """
CREATE TEMP TABLE way_ends AS
SELECT
    ends(nodes) AS nid,
    id,
    tags->'highway' AS highway,
    nodes
FROM
    {0}ways AS ways
WHERE
    tags != ''::hstore AND
    tags?'highway' AND
    tags->'highway' IN ('cycleway', 'motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link', 'secondary', 'secondary_link', 'tertiary_link')
"""

sql20 = """
SELECT
    MIN(way_ends.id),
    ST_AsText(nodes.geom),
    MIN(way_ends.highway)
FROM
    way_ends
    JOIN nodes ON
        nodes.id = ANY (way_ends.nodes)
WHERE
    NOT nodes.tags?'highway' OR nodes.tags->'highway' != 'turning_circle'
GROUP BY
    nodes.id,
    nodes.geom
HAVING
    COUNT(*) = 1
"""

sql30 = """
CREATE TEMP TABLE oneway AS
SELECT
  id,
  linestring,
  nodes[nid_index] AS nid,
  nid_index
FROM (
  SELECT
    id,
    linestring,
    nodes,
    generate_subscripts(nodes, 1, tags?'oneway' AND tags->'oneway' = '-1') AS nid_index
  FROM
    ways
  WHERE
    tags != ''::hstore AND
    tags?'highway' AND
    (
      tags?'oneway' AND
      tags->'oneway' IN ('yes', 'true', '1', '-1')
    ) OR (
      tags?'junction' AND
      tags->'junction' = 'roundabout'
    )
) AS t
"""

sql31 = """
CREATE TEMP TABLE input_nodes AS (
SELECT DISTINCT
  oneway.nid
FROM
  oneway
  JOIN way_nodes ON
    way_nodes.node_id = oneway.nid
  JOIN ways ON
    ways.id = way_nodes.way_id
WHERE
  ways.tags != ''::hstore AND
  (
    ways.tags?'highway' AND
    (NOT ways.tags?'oneway' OR ways.tags->'oneway' IN ('no', 'false')) AND
    (NOT ways.tags?'junction' OR ways.tags->'junction' != 'roundabout')
  ) OR (
    ways.tags?'amenity' AND ways.tags->'amenity' = 'parking'
  )
ORDER BY
  oneway.nid
) UNION (
SELECT
  oneway.nid
FROM
  oneway
  JOIN nodes ON
    nodes.id = oneway.nid
WHERE
  nodes.tags != ''::hstore AND
  nodes.tags?'amenity' AND
  nodes.tags->'amenity' = 'parking_entrance' -- entrance and/or exit
)
"""

sql32 = """
WITH RECURSIVE t AS (
  SELECT * FROM input_nodes
UNION
  SELECT
    oneway_next.nid AS nid
  FROM
    t
    JOIN oneway AS oneway_input ON
      oneway_input.nid = t.nid
    JOIN oneway AS oneway_next ON
      oneway_next.id = oneway_input.id AND
      oneway_next.nid_index > oneway_input.nid_index
)
SELECT
  DISTINCT ON (oneway.id)
  oneway.id,
  oneway.nid,
  (SELECT ST_AsText(geom) FROM nodes WHERE id = oneway.nid)
FROM
  oneway
  LEFT JOIN t ON
    t.nid = oneway.nid
WHERE
  t.nid IS NULL
ORDER BY
  oneway.id,
  oneway.nid_index DESC
"""

class Analyser_Osmosis_Highway_DeadEnd(Analyser_Osmosis):

    def __init__(self, config, logger = None):
        Analyser_Osmosis.__init__(self, config, logger)
        self.classs_change[1] = {"item":"1210", "level": 1, "tag": ["highway", "cycleway", "fix:chair"], "desc": T_(u"Unconnected cycleway") }
        self.classs_change[2] = {"item":"1210", "level": 1, "tag": ["highway", "fix:chair"], "desc": T_(u"Unconnected way") }
        self.classs[3] = {"item":"1210", "level": 1, "tag": ["highway", "fix:chair"], "desc": T_(u"One way inaccessible or missing parking or parking entrance") }
        self.callback20 = lambda res: {"class":1 if res[2]=='cycleway' else 2, "data":[self.way_full, self.positionAsText]}

    def analyser_osmosis_all(self):
        self.run(sql10.format(""))
        self.run(sql20, self.callback20)
        self.run(sql30)
        self.run(sql31)
        self.run(sql32, lambda res: {"class":3, "data":[self.way_full, self.node, self.positionAsText]})

    def analyser_osmosis_touched(self):
        self.run(sql10.format("touched_"))
        self.run(sql20, self.callback20)