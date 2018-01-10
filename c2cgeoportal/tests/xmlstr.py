# -*- coding: utf-8 -*-

# Copyright (c) 2013-2018, Camptocamp SA
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


getfeature = """
<wfs:GetFeature xmlns:wfs="http://www.opengis.net/wfs" service="WFS" version="1.1.0" xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.1.0/wfs.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<wfs:Query typeName="feature:grundstueck" srsName="EPSG:2056" xmlns:feature="http://mapserver.gis.umn.edu/mapserver">
<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
<ogc:PropertyIsLike matchCase="false" wildCard="*" singleChar="." escapeChar="!">
<ogc:PropertyName>nummer</ogc:PropertyName>
<ogc:Literal>10*</ogc:Literal>
</ogc:PropertyIsLike>
</ogc:Filter>
</wfs:Query>
</wfs:GetFeature>

"""
feature = """
    <gml:featureMember>
      <ms:grundstueck>
        <gml:boundedBy>
            <gml:Envelope srsName="EPSG:2056">
                <gml:lowerCorner>2626901.051818 1258035.790009</gml:lowerCorner>
                <gml:upperCorner>2627050.862856 1258132.841364</gml:upperCorner>
            </gml:Envelope>
        </gml:boundedBy>
        <ms:msGeometry>
          <gml:LineString srsName="EPSG:2056">
            <gml:posList srsDimension="2">2627033.201116 1258103.390372 2627034.048142 1258105.737388 2627010.821109 1258118.506850 2626985.111074 1258132.841364 2626980.135958 1258123.622322 2626978.010913 1258120.089309 2626966.170890 1258126.005538 2626949.985629 1258108.760552 2626924.919220 1258081.422566 2626910.187979 1258065.386575 2626901.051818 1258054.063564 2626935.224905 1258039.509934 2626956.098017 1258037.068626 2626971.167108 1258036.400415 2627000.949294 1258035.790009 2627018.708458 1258041.255835 2627029.967583 1258047.114753 2627048.056822 1258060.580669 2627050.862856 1258062.337652 2627048.942861 1258064.236700 2627036.107888 1258076.303014 2627023.360917 1258088.497329 2627028.596025 1258096.640354 2627033.201116 1258103.390372 </gml:posList>
          </gml:LineString>
        </ms:msGeometry>
        <ms:gs_id>1676545</ms:gs_id>
        <ms:lsn_oid>1510175178</ms:lsn_oid>
        <ms:nummer>1071</ms:nummer>
        <ms:gueltigkeit>rechtskräftig</ms:gueltigkeit>
        <ms:art>Liegenschaft</ms:art>
        <ms:gemeinde_id_bfs>2861</ms:gemeinde_id_bfs>
        <ms:meta_id>1510</ms:meta_id>
        <ms:flaechenmass>8774</ms:flaechenmass>
        <ms:nummer_m_deko>1071</ms:nummer_m_deko>
        <ms:nbident>BL0200002861</ms:nbident>
        <ms:vollstaendigkeit>vollständig</ms:vollstaendigkeit>
        <ms:datenherr>Jermann</ms:datenherr>
        <ms:mut_nummer>pn18</ms:mut_nummer>
      </ms:grundstueck>
    </gml:featureMember>
    """

featurecollection_outlimit = """
<wfs:FeatureCollection xmlns:ms="http://mapserver.gis.umn.edu/mapserver" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:wfs="http://www.opengis.net/wfs" xsi:schemaLocation="http://mapserver.gis.umn.edu/mapserver http://c2cpc29.camptocamp.com/sbrunner/mapserv?SERVICE=WFS&amp;VERSION=1.1.0&amp;REQUEST=DescribeFeatureType&amp;TYPENAME=feature:grundstueck&amp;OUTPUTFORMAT=text/xml;%20subtype=gml/3.1.1  http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.1.0/wfs.xsd">
    <gml:boundedBy>
      <gml:Envelope srsName="EPSG:2056">
          <gml:lowerCorner>2595270.118588 1244096.257242</gml:lowerCorner>
          <gml:upperCorner>2638409.063753 1267658.751429</gml:upperCorner>
      </gml:Envelope>
    </gml:boundedBy>
    """ + feature * 205 + """
</wfs:FeatureCollection>
    """

featurecollection_inlimit = """
<wfs:FeatureCollection xmlns:ms="http://mapserver.gis.umn.edu/mapserver" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:wfs="http://www.opengis.net/wfs" xsi:schemaLocation="http://mapserver.gis.umn.edu/mapserver http://c2cpc29.camptocamp.com/sbrunner/mapserv?SERVICE=WFS&amp;VERSION=1.1.0&amp;REQUEST=DescribeFeatureType&amp;TYPENAME=feature:grundstueck&amp;OUTPUTFORMAT=text/xml;%20subtype=gml/3.1.1  http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.1.0/wfs.xsd">
    <gml:boundedBy>
      <gml:Envelope srsName="EPSG:2056">
          <gml:lowerCorner>2595270.118588 1244096.257242</gml:lowerCorner>
          <gml:upperCorner>2638409.063753 1267658.751429</gml:upperCorner>
      </gml:Envelope>
    </gml:boundedBy>
    """ + feature * 199 + """
</wfs:FeatureCollection>
    """
