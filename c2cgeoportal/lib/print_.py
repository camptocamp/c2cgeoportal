# -*- coding: utf-8 -*-

# Copyright (c) 2011-2017, Camptocamp SA
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


import yaml


# Attributes

class PrintBoolean(yaml.YAMLObject):
    yaml_tag = u"!boolean"


class PrintDatasource(yaml.YAMLObject):
    yaml_tag = u"!datasource"


class PrintFeatures(yaml.YAMLObject):
    yaml_tag = u"!features"


class PrintFloat(yaml.YAMLObject):
    yaml_tag = u"!float"


class PrintInteger(yaml.YAMLObject):
    yaml_tag = u"!integer"


class PrintLegend(yaml.YAMLObject):
    yaml_tag = u"!legend"


class PrintMap(yaml.YAMLObject):
    yaml_tag = u"!map"


class PrintNorthArraw(yaml.YAMLObject):
    yaml_tag = u"!northArrow"


class PrintOverviewMap(yaml.YAMLObject):
    yaml_tag = u"!overviewMap"


class PrintPaging(yaml.YAMLObject):
    yaml_tag = u"!paging"


class PrintScalbar(yaml.YAMLObject):
    yaml_tag = u"!scalebar"


class PrintStaticLayer(yaml.YAMLObject):
    yaml_tag = u"!staticLayer"


class PrintString(yaml.YAMLObject):
    yaml_tag = u"!string"


class PrintStringArray(yaml.YAMLObject):
    yaml_tag = u"!stringArray"


class PrintStyle(yaml.YAMLObject):
    yaml_tag = u"!style"


class PrintTable(yaml.YAMLObject):
    yaml_tag = u"!table"


# Configuration


class PrintAcceptAll(yaml.YAMLObject):
    yaml_tag = u"!acceptAll"


class PrintAlwaysAllowedAssertion(yaml.YAMLObject):
    yaml_tag = u"!alwaysAllowedAssertion"


class PrintAndAssertion(yaml.YAMLObject):
    yaml_tag = u"!andAssertion"


class PrintCertificateStore(yaml.YAMLObject):
    yaml_tag = u"!certificateStore"


class PrintCredential(yaml.YAMLObject):
    yaml_tag = u"!credential"


class PrintDmsMatch(yaml.YAMLObject):
    yaml_tag = u"!dnsMatch"


class PrintIpMatch(yaml.YAMLObject):
    yaml_tag = u"!ipMatch"


class PrintLocalMatch(yaml.YAMLObject):
    yaml_tag = u"!localMatch"


class PrintMergeSource(yaml.YAMLObject):
    yaml_tag = u"!mergeSource"


class PrintOldApi(yaml.YAMLObject):
    yaml_tag = u"!oldApi"


class PrintPdfConfig(yaml.YAMLObject):
    yaml_tag = u"!pdfConfig"


class PrintProxy(yaml.YAMLObject):
    yaml_tag = u"!proxy"


class PrintRoleAccessAssertion(yaml.YAMLObject):
    yaml_tag = u"!roleAccessAssertion"


class PrintTemplate(yaml.YAMLObject):
    yaml_tag = u"!template"


class PrintUpdatePdfConfigUpdate(yaml.YAMLObject):
    yaml_tag = u"!updatePdfConfigUpdate"


class PrintUrlImage(yaml.YAMLObject):
    yaml_tag = u"!urlImage"


class PrintZoomLevels(yaml.YAMLObject):
    yaml_tag = u"!zoomLevels"


# Processor


class PrintAddBackgroundLayers(yaml.YAMLObject):
    yaml_tag = u"!addBackgroundLayers"


class PrintaddHeaders(yaml.YAMLObject):
    yaml_tag = u"!addHeaders"


class PrintaddOverlayLayers(yaml.YAMLObject):
    yaml_tag = u"!addOverlayLayers"


class PrintconfigureHttpRequests(yaml.YAMLObject):
    yaml_tag = u"!configureHttpRequests"


class PrintcreateDataSource(yaml.YAMLObject):
    yaml_tag = u"!createDataSource"


class PrintcreateMap(yaml.YAMLObject):
    yaml_tag = u"!createMap"


class PrintcreateMapPages(yaml.YAMLObject):
    yaml_tag = u"!createMapPages"


class PrintcreateNorthArrow(yaml.YAMLObject):
    yaml_tag = u"!createNorthArrow"


class PrintcreateOverviewMap(yaml.YAMLObject):
    yaml_tag = u"!createOverviewMap"


class PrintcreateScalebar(yaml.YAMLObject):
    yaml_tag = u"!createScalebar"


class PrintForwardHeaders(yaml.YAMLObject):
    yaml_tag = u"!forwardHeaders"


class PrintMapUri(yaml.YAMLObject):
    yaml_tag = u"!mapUri"


class PrintMergeDataSources(yaml.YAMLObject):
    yaml_tag = u"!mergeDataSources"


class PrintPrepareLegend(yaml.YAMLObject):
    yaml_tag = u"!prepareLegend"


class PrintPrepareTable(yaml.YAMLObject):
    yaml_tag = u"!prepareTable"


class PrintReportBuilder(yaml.YAMLObject):
    yaml_tag = u"!reportBuilder"


class PrintRestrictUris(yaml.YAMLObject):
    yaml_tag = u"!restrictUris"


class PrintSetFeatures(yaml.YAMLObject):
    yaml_tag = u"!setFeatures"


class PrintSetStyle(yaml.YAMLObject):
    yaml_tag = u"!setStyle"


class PrintSetWmsCustomParam(yaml.YAMLObject):
    yaml_tag = u"!setWmsCustomParam"


class PrintUpdatePdfConfig(yaml.YAMLObject):
    yaml_tag = u"!updatePdfConfig"


class PrintUseHttpForHttps(yaml.YAMLObject):
    yaml_tag = u"!useHttpForHttps"


# Other


class PrintConfigureHttpRequests(yaml.YAMLObject):
    yaml_tag = u"!configureHttpRequests"


class PrintCreateNorthArrow(yaml.YAMLObject):
    yaml_tag = u"!createNorthArrow"


class PrintCreateScalebar(yaml.YAMLObject):
    yaml_tag = u"!createScalebar"


class PrintCreateMap(yaml.YAMLObject):
    yaml_tag = u"!createMap"


class PrintCreateDataSource(yaml.YAMLObject):
    yaml_tag = u"!createDataSource"
