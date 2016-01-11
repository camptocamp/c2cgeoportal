# -*- coding: utf-8 -*-

# Copyright (c) 2012-2016, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.


# file taken from http://indiemaps.com/blog/2008/03/easy-shapefile-loading-in-python/

import math

from struct import unpack
import dbfutils


XY_POINT_RECORD_LENGTH = 16
db = []


def load_shapefile(file_name):
    global db
    file_name = file_name
    records = []
    # open dbf file and get records as a list
    dbf_file = file_name[0:-4] + ".dbf"
    dbf = open(dbf_file, "rb")
    db = list(dbfutils.dbfreader(dbf))
    dbf.close()
    fp = open(file_name, "rb")

    # get basic shapefile configuration
    fp.seek(32)
    read_and_unpack("i", fp.read(4))
    read_bounding_box(fp)

    # fetch Records
    fp.seek(100)
    while True:
        shp_record = create_record(fp)
        if not shp_record:
            break
        records.append(shp_record)

    return records


record_class = {
    0: "RecordNull",
    1: "RecordPoint",
    8: "RecordMultiPoint",
    3: "RecordPolyLine",
    5: "RecordPolygon"
}


def create_record(fp):
    # read header
    record_number = read_and_unpack(">L", fp.read(4))
    if record_number == "":
        return False
    read_and_unpack(">L", fp.read(4))
    record_shape_type = read_and_unpack("<L", fp.read(4))

    shp_data = read_record_any(fp, record_shape_type)
    dbf_data = {}
    for i in range(0, len(db[record_number + 1])):
        dbf_data[db[0][i]] = db[record_number + 1][i]

    return {"shp_data": shp_data, "dbf_data": dbf_data}


# Reading defs


def read_record_any(fp, type):
    if type == 0:
        return read_record_null(fp)
    elif type == 1:
        return read_record_point(fp)
    elif type == 8:
        return read_record_multi_point(fp)
    elif type == 3 or type == 5:
        return read_record_poly_line(fp)
    else:
        return False


def read_record_null(fp):
    data = {}
    return data


point_count = 0


def read_record_point(fp):
    global point_count
    data = {}
    data["x"] = read_and_unpack("d", fp.read(8))
    data["y"] = read_and_unpack("d", fp.read(8))
    point_count += 1
    return data


def read_record_multi_point(fp):
    data = read_bounding_box(fp)
    data["numpoints"] = read_and_unpack("i", fp.read(4))
    for i in range(0, data["numpoints"]):
        data["points"].append(read_record_point(fp))
    return data


def read_record_poly_line(fp):
    data = read_bounding_box(fp)
    data["numparts"] = read_and_unpack("i", fp.read(4))
    data["numpoints"] = read_and_unpack("i", fp.read(4))
    data["parts"] = []
    for i in range(0, data["numparts"]):
        data["parts"].append(read_and_unpack("i", fp.read(4)))
    points_initial_index = fp.tell()
    points_read = 0
    for part_index in range(0, data["numparts"]):
        # if(!isset(data["parts"][part_index]["points"]) or
        # !is_array(data["parts"][part_index]["points"])):
        data["parts"][part_index] = {}
        data["parts"][part_index]["points"] = []

        # while( ! in_array( points_read, data["parts"]) and
        # points_read < data["numpoints"] and !feof(fp)):
        check_point = []
        while (points_read < data["numpoints"]):
            curr_point = read_record_point(fp)
            data["parts"][part_index]["points"].append(curr_point)
            points_read += 1
            if points_read == 0 or check_point == []:
                check_point = curr_point
            elif curr_point == check_point:
                check_point = []
                break

    fp.seek(points_initial_index + (points_read * XY_POINT_RECORD_LENGTH))
    return data


# General defs


def read_bounding_box(fp):
    data = {}
    data["xmin"] = read_and_unpack("d", fp.read(8))
    data["ymin"] = read_and_unpack("d", fp.read(8))
    data["xmax"] = read_and_unpack("d", fp.read(8))
    data["ymax"] = read_and_unpack("d", fp.read(8))
    return data


def read_and_unpack(type, data):
    if data == "":
        return data
    return unpack(type, data)[0]


# ###
# ### additional functions
# ###


def get_centroids(records, projected=False):
    # for each feature
    if projected:
        points = "projectedPoints"
    else:
        points = "points"

    for feature in records:
        numpoints = cx = cy = 0
        for part in feature["shp_data"]["parts"]:
            for point in part[points]:
                numpoints += 1
                cx += point["x"]
                cy += point["y"]
        cx /= numpoints
        cy /= numpoints
        feature["shp_data"]["centroid"] = {"x": cx, "y": cy}


def get_bound_centers(records):
    for feature in records:
        cx = .5 * (feature["shp_data"]["xmax"] - feature["shp_data"]["xmin"]) + \
            feature["shp_data"]["xmin"]
        cy = .5 * (feature["shp_data"]["ymax"] - feature["shp_data"]["ymin"]) + \
            feature["shp_data"]["ymin"]
        feature["shp_data"]["boundCenter"] = {"x": cx, "y": cy}


def get_true_centers(records, projected=False):
    # gets the true polygonal centroid for each feature (uses largest ring)
    # should be spherical, but isn't

    if projected:
        points = "projectedPoints"
    else:
        points = "points"

    for feature in records:
        maxarea = 0
        for ring in feature["shp_data"]["parts"]:
            ring_area = get_area(ring, points)
            if ring_area > maxarea:
                maxarea = ring_area
                biggest = ring
            # now get the true centroid
        temp_point = {"x": 0, "y": 0}
        if biggest[points][0] != biggest[points][len(biggest[points]) - 1]:
            print  \
                "mug", biggest[points][0], \
                biggest[points][len(biggest[points]) - 1]
        for i in range(0, len(biggest[points]) - 1):
            j = (i + 1) % (len(biggest[points]) - 1)
            temp_point["x"] -= \
                (biggest[points][i]["x"] + biggest[points][j]["x"]) * \
                (
                    (biggest[points][i]["x"] * biggest[points][j]["y"]) -
                    (biggest[points][j]["x"] * biggest[points][i]["y"]))
            temp_point["y"] -= \
                (biggest[points][i]["y"] + biggest[points][j]["y"]) * \
                (
                    (biggest[points][i]["x"] * biggest[points][j]["y"]) -
                    (biggest[points][j]["x"] * biggest[points][i]["y"]))

        temp_point["x"] = temp_point["x"] / ((6) * maxarea)
        temp_point["y"] = temp_point["y"] / ((6) * maxarea)
        feature["shp_data"]["truecentroid"] = temp_point


def get_area(ring, points):
    # returns the area of a polygon
    # needs to be spherical area, but isn"t
    area = 0
    for i in range(0, len(ring[points]) - 1):
        j = (i + 1) % (len(ring[points]) - 1)
        area += ring[points][i]["x"] * ring[points][j]["y"]
        area -= ring[points][i]["y"] * ring[points][j]["x"]

    return math.fabs(area / 2)


def get_neighbors(records):
    # for each feature
    for i in range(len(records)):
        if "neighbors" not in records[i]["shp_data"]:
            records[i]["shp_data"]["neighbors"] = []

        # for each other feature
        for j in range(i + 1, len(records)):
            numcommon = 0
            # first check to see if the bounding boxes overlap
            if overlap(records[i], records[j]):
                # if so, check every single point in this feature
                # to see if it matches a point in the other feature

                # for each part:
                for part in records[i]["shp_data"]["parts"]:

                    # for each point:
                    for point in part["points"]:

                        for otherPart in records[j]["shp_data"]["parts"]:
                            if point in otherPart["points"]:
                                numcommon += 1
                                if numcommon == 2:
                                    if "neighbors" not in records[j]["shp_data"]:
                                        records[j]["shp_data"]["neighbors"] = []
                                    records[i]["shp_data"]["neighbors"].append(j)
                                    records[j]["shp_data"]["neighbors"].append(i)
                                    # now break out to the next j
                                    break
                        if numcommon == 2:
                            break
                    if numcommon == 2:
                        break


def project_shapefile(records, what_projection, lon_center=0, lat_center=0):
    print "projecting to ", what_projection
    for feature in records:
        for part in feature["shp_data"]["parts"]:
            part["projectedPoints"] = []
            for point in part["points"]:
                temp_point = project_point(
                    point, what_projection, lon_center, lat_center)
                part["projectedPoints"].append(temp_point)


def project_point(from_point, what_projection, lon_center, lat_center):
    lat_radians = from_point["y"] * math.pi / 180
    if lat_radians > 1.5:
        lat_radians = 1.5
    if lat_radians < -1.5:
        lat_radians = -1.5
    lon_radians = from_point["x"] * math.pi / 180
    lon_center = lon_center * math.pi / 180
    lat_center = lat_center * math.pi / 180
    new_point = {}
    if what_projection == "MERCATOR":
        new_point["x"] = (180 / math.pi) * (lon_radians - lon_center)
        new_point["y"] = (180 / math.pi) * math.log(
            math.tan(lat_radians) + (1 / math.cos(lat_radians)))
        if new_point["y"] > 200:
            new_point["y"] = 200
        if new_point["y"] < -200:
            new_point["y"] = 200
        return new_point
    if what_projection == "EQUALAREA":
        new_point["x"] = 0
        new_point["y"] = 0
        return new_point


def overlap(feature1, feature2):
    if (feature1["shp_data"]["xmax"] > feature2["shp_data"]["xmin"] and
            feature1["shp_data"]["ymax"] > feature2["shp_data"]["ymin"] and
            feature1["shp_data"]["xmin"] < feature2["shp_data"]["xmax"] and
            feature1["shp_data"]["ymin"] < feature2["shp_data"]["ymax"]):
        return True
    else:
        return False
