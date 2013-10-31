#  - * -  coding:  utf - 8 - * -

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
    dbf_file = file_name[0:-4] + '.dbf'
    dbf = open(dbf_file, 'rb')
    db = list(dbfutils.dbfreader(dbf))
    dbf.close()
    fp = open(file_name, 'rb')

    # get basic shapefile configuration
    fp.seek(32)
    read_and_unpack('i', fp.read(4))
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
    0: 'RecordNull',
    1: 'RecordPoint',
    8: 'RecordMultiPoint',
    3: 'RecordPolyLine',
    5: 'RecordPolygon'
}


def create_record(fp):
# read header
    record_number = read_and_unpack('>L', fp.read(4))
    if record_number == '':
        return False
    read_and_unpack('>L', fp.read(4))
    record_shape_type = read_and_unpack('<L', fp.read(4))

    shp_data = read_record_any(fp, record_shape_type)
    dbf_data = {}
    for i in range(0, len(db[record_number + 1])):
        dbf_data[db[0][i]] = db[record_number + 1][i]

    return {'shp_data': shp_data, 'dbf_data': dbf_data}


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
    data['x'] = read_and_unpack('d', fp.read(8))
    data['y'] = read_and_unpack('d', fp.read(8))
    point_count += 1
    return data


def read_record_multi_point(fp):
    data = read_bounding_box(fp)
    data['numpoints'] = read_and_unpack('i', fp.read(4))
    for i in range(0, data['numpoints']):
        data['points'].append(read_record_point(fp))
    return data


def read_record_poly_line(fp):
    data = read_bounding_box(fp)
    data['numparts'] = read_and_unpack('i', fp.read(4))
    data['numpoints'] = read_and_unpack('i', fp.read(4))
    data['parts'] = []
    for i in range(0, data['numparts']):
        data['parts'].append(read_and_unpack('i', fp.read(4)))
    points_initial_index = fp.tell()
    points_read = 0
    for part_index in range(0, data['numparts']):
        # if(!isset(data['parts'][part_index]['points']) or
        # !is_array(data['parts'][part_index]['points'])):
        data['parts'][part_index] = {}
        data['parts'][part_index]['points'] = []

        # while( ! in_array( points_read, data['parts']) and
        # points_read < data['numpoints'] and !feof(fp)):
        checkPoint = []
        while (points_read < data['numpoints']):
            currPoint = read_record_point(fp)
            data['parts'][part_index]['points'].append(currPoint)
            points_read += 1
            if points_read == 0 or checkPoint == []:
                checkPoint = currPoint
            elif currPoint == checkPoint:
                checkPoint = []
                break

    fp.seek(points_initial_index + (points_read * XY_POINT_RECORD_LENGTH))
    return data


# General defs


def read_bounding_box(fp):
    data = {}
    data['xmin'] = read_and_unpack('d', fp.read(8))
    data['ymin'] = read_and_unpack('d', fp.read(8))
    data['xmax'] = read_and_unpack('d', fp.read(8))
    data['ymax'] = read_and_unpack('d', fp.read(8))
    return data


def read_and_unpack(type, data):
    if data == '':
        return data
    return unpack(type, data)[0]


####
#### additional functions
####


def get_centroids(records, projected=False):
# for each feature
    if projected:
        points = 'projectedPoints'
    else:
        points = 'points'

    for feature in records:
        numpoints = cx = cy = 0
        for part in feature['shp_data']['parts']:
            for point in part[points]:
                numpoints += 1
                cx += point['x']
                cy += point['y']
        cx /= numpoints
        cy /= numpoints
        feature['shp_data']['centroid'] = {'x': cx, 'y': cy}


def get_bound_centers(records):
    for feature in records:
        cx = .5 * (feature['shp_data']['xmax'] - feature['shp_data']['xmin']) + \
            feature['shp_data']['xmin']
        cy = .5 * (feature['shp_data']['ymax'] - feature['shp_data']['ymin']) + \
            feature['shp_data']['ymin']
        feature['shp_data']['boundCenter'] = {'x': cx, 'y': cy}


def get_true_centers(records, projected=False):
#gets the true polygonal centroid for each feature (uses largest ring)
#should be spherical, but isn't

    if projected:
        points = 'projectedPoints'
    else:
        points = 'points'

    for feature in records:
        maxarea = 0
        for ring in feature['shp_data']['parts']:
            ringArea = get_area(ring, points)
            if ringArea > maxarea:
                maxarea = ringArea
                biggest = ring
            #now get the true centroid
        tempPoint = {'x': 0, 'y': 0}
        if biggest[points][0] != biggest[points][len(biggest[points]) - 1]:
            print  \
                "mug", biggest[points][0], \
                biggest[points][len(biggest[points]) - 1]
        for i in range(0, len(biggest[points]) - 1):
            j = (i + 1) % (len(biggest[points]) - 1)
            tempPoint['x'] -= (biggest[points][i]['x'] + biggest[points][j]['x']) * \
                ((biggest[points][i]['x'] * biggest[points][j]['y']) -
                (biggest[points][j]['x'] * biggest[points][i]['y']))
            tempPoint['y'] -= (biggest[points][i]['y'] + biggest[points][j]['y']) * \
                ((biggest[points][i]['x'] * biggest[points][j]['y']) -
                (biggest[points][j]['x'] * biggest[points][i]['y']))

        tempPoint['x'] = tempPoint['x'] / ((6) * maxarea)
        tempPoint['y'] = tempPoint['y'] / ((6) * maxarea)
        feature['shp_data']['truecentroid'] = tempPoint


def get_area(ring, points):
#returns the area of a polygon
#needs to be spherical area, but isn't
    area = 0
    for i in range(0, len(ring[points]) - 1):
        j = (i + 1) % (len(ring[points]) - 1)
        area += ring[points][i]['x'] * ring[points][j]['y']
        area -= ring[points][i]['y'] * ring[points][j]['x']

    return math.fabs(area / 2)


def get_neighbors(records):

#for each feature
    for i in range(len(records)):
    #print i, records[i]['dbf_data']['ADMIN_NAME']
        if not 'neighbors' in records[i]['shp_data']:
            records[i]['shp_data']['neighbors'] = []

        #for each other feature
        for j in range(i + 1, len(records)):
            numcommon = 0
            #first check to see if the bounding boxes overlap
            if overlap(records[i], records[j]):
            #if so, check every single point in this feature
            #to see if it matches a point in the other feature

            #for each part:
                for part in records[i]['shp_data']['parts']:

                #for each point:
                    for point in part['points']:

                        for otherPart in records[j]['shp_data']['parts']:
                            if point in otherPart['points']:
                                numcommon += 1
                                if numcommon == 2:
                                    if not 'neighbors' in records[j]['shp_data']:
                                        records[j]['shp_data']['neighbors'] = []
                                    records[i]['shp_data']['neighbors'].append(j)
                                    records[j]['shp_data']['neighbors'].append(i)
                                    #now break out to the next j
                                    break
                        if numcommon == 2:
                            break
                    if numcommon == 2:
                        break


def projectShapefile(records, whatProjection, lonCenter=0, latCenter=0):
    print 'projecting to ', whatProjection
    for feature in records:
        for part in feature['shp_data']['parts']:
            part['projectedPoints'] = []
            for point in part['points']:
                tempPoint = project_point(
                    point, whatProjection, lonCenter, latCenter)
                part['projectedPoints'].append(tempPoint)


def project_point(fromPoint, whatProjection, lonCenter, latCenter):
    latRadians = fromPoint['y'] * math.pi / 180
    if latRadians > 1.5:
        latRadians = 1.5
    if latRadians < -1.5:
        latRadians = -1.5
    lonRadians = fromPoint['x'] * math.pi / 180
    lonCenter = lonCenter * math.pi / 180
    latCenter = latCenter * math.pi / 180
    newPoint = {}
    if whatProjection == "MERCATOR":
        newPoint['x'] = (180 / math.pi) * (lonRadians - lonCenter)
        newPoint['y'] = (180 / math.pi) * math.log(
            math.tan(latRadians) + (1 / math.cos(latRadians)))
        if newPoint['y'] > 200:
            newPoint['y'] = 200
        if newPoint['y'] < -200:
            newPoint['y'] = 200
        return newPoint
    if whatProjection == "EQUALAREA":
        newPoint['x'] = 0
        newPoint['y'] = 0
        return newPoint


def overlap(feature1, feature2):
    if (feature1['shp_data']['xmax'] > feature2['shp_data']['xmin'] and
            feature1['shp_data']['ymax'] > feature2['shp_data']['ymin'] and
            feature1['shp_data']['xmin'] < feature2['shp_data']['xmax'] and
            feature1['shp_data']['ymin'] < feature2['shp_data']['ymax']):
        return True
    else:
        return False
