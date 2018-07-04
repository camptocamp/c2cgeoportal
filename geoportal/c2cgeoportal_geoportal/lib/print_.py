# -*- coding: utf-8 -*-

# Copyright (c) 2011-2018, Camptocamp SA
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
    yaml_tag = "!boolean"


class PrintDatasource(yaml.YAMLObject):
    yaml_tag = "!datasource"


class PrintFeatures(yaml.YAMLObject):
    yaml_tag = "!features"


class PrintFloat(yaml.YAMLObject):
    yaml_tag = "!float"


class PrintInteger(yaml.YAMLObject):
    yaml_tag = "!integer"


class PrintLegend(yaml.YAMLObject):
    yaml_tag = "!legend"


class PrintMap(yaml.YAMLObject):
    yaml_tag = "!map"


class PrintNorthArraw(yaml.YAMLObject):
    yaml_tag = "!northArrow"


class PrintOverviewMap(yaml.YAMLObject):
    yaml_tag = "!overviewMap"


class PrintPaging(yaml.YAMLObject):
    yaml_tag = "!paging"


class PrintScalbar(yaml.YAMLObject):
    yaml_tag = "!scalebar"


class PrintStaticLayer(yaml.YAMLObject):
    yaml_tag = "!staticLayer"


class PrintString(yaml.YAMLObject):
    yaml_tag = "!string"


class PrintStringArray(yaml.YAMLObject):
    yaml_tag = "!stringArray"


class PrintStyle(yaml.YAMLObject):
    yaml_tag = "!style"


class PrintTable(yaml.YAMLObject):
    yaml_tag = "!table"


# Configuration


class PrintAcceptAll(yaml.YAMLObject):
    yaml_tag = "!acceptAll"


class PrintAlwaysAllowedAssertion(yaml.YAMLObject):
    yaml_tag = "!alwaysAllowedAssertion"


class PrintAndAssertion(yaml.YAMLObject):
    yaml_tag = "!andAssertion"


class PrintCertificateStore(yaml.YAMLObject):
    yaml_tag = "!certificateStore"


class PrintCredential(yaml.YAMLObject):
    yaml_tag = "!credential"


class PrintDnsMatch(yaml.YAMLObject):
    yaml_tag = "!dnsMatch"


class PrintHostnameMatch(yaml.YAMLObject):
    yaml_tag = "!hostnameMatch"


class PrintIpMatch(yaml.YAMLObject):
    yaml_tag = "!ipMatch"


class PrintLocalMatch(yaml.YAMLObject):
    yaml_tag = "!localMatch"


class PrintMergeSource(yaml.YAMLObject):
    yaml_tag = "!mergeSource"


class PrintOldApi(yaml.YAMLObject):
    yaml_tag = "!oldApi"


class PrintPdfConfig(yaml.YAMLObject):
    yaml_tag = "!pdfConfig"


class PrintProxy(yaml.YAMLObject):
    yaml_tag = "!proxy"


class PrintRoleAccessAssertion(yaml.YAMLObject):
    yaml_tag = "!roleAccessAssertion"


class PrintTemplate(yaml.YAMLObject):
    yaml_tag = "!template"


class PrintUpdatePdfConfigUpdate(yaml.YAMLObject):
    yaml_tag = "!updatePdfConfigUpdate"


class PrintUrlImage(yaml.YAMLObject):
    yaml_tag = "!urlImage"


class PrintZoomLevels(yaml.YAMLObject):
    yaml_tag = "!zoomLevels"


# Processor


class PrintAddBackgroundLayers(yaml.YAMLObject):
    yaml_tag = "!addBackgroundLayers"


class PrintaddHeaders(yaml.YAMLObject):
    yaml_tag = "!addHeaders"


class PrintaddOverlayLayers(yaml.YAMLObject):
    yaml_tag = "!addOverlayLayers"


class PrintconfigureHttpRequests(yaml.YAMLObject):
    yaml_tag = "!configureHttpRequests"


class PrintcreateDataSource(yaml.YAMLObject):
    yaml_tag = "!createDataSource"


class PrintcreateMap(yaml.YAMLObject):
    yaml_tag = "!createMap"


class PrintcreateMapPages(yaml.YAMLObject):
    yaml_tag = "!createMapPages"


class PrintcreateNorthArrow(yaml.YAMLObject):
    yaml_tag = "!createNorthArrow"


class PrintcreateOverviewMap(yaml.YAMLObject):
    yaml_tag = "!createOverviewMap"


class PrintcreateScalebar(yaml.YAMLObject):
    yaml_tag = "!createScalebar"


class PrintForwardHeaders(yaml.YAMLObject):
    yaml_tag = "!forwardHeaders"


class PrintMapUri(yaml.YAMLObject):
    yaml_tag = "!mapUri"


class PrintMergeDataSources(yaml.YAMLObject):
    yaml_tag = "!mergeDataSources"


class PrintPrepareLegend(yaml.YAMLObject):
    yaml_tag = "!prepareLegend"


class PrintPrepareTable(yaml.YAMLObject):
    yaml_tag = "!prepareTable"


class PrintReportBuilder(yaml.YAMLObject):
    yaml_tag = "!reportBuilder"


class PrintRestrictUris(yaml.YAMLObject):
    yaml_tag = "!restrictUris"


class PrintSetFeatures(yaml.YAMLObject):
    yaml_tag = "!setFeatures"


class PrintSetStyle(yaml.YAMLObject):
    yaml_tag = "!setStyle"


class PrintSetWmsCustomParam(yaml.YAMLObject):
    yaml_tag = "!setWmsCustomParam"


class PrintUpdatePdfConfig(yaml.YAMLObject):
    yaml_tag = "!updatePdfConfig"


class PrintUseHttpForHttps(yaml.YAMLObject):
    yaml_tag = "!useHttpForHttps"


# Other


class PrintConfigureHttpRequests(yaml.YAMLObject):
    yaml_tag = "!configureHttpRequests"


class PrintCreateNorthArrow(yaml.YAMLObject):
    yaml_tag = "!createNorthArrow"


class PrintCreateScalebar(yaml.YAMLObject):
    yaml_tag = "!createScalebar"


class PrintCreateMap(yaml.YAMLObject):
    yaml_tag = "!createMap"


class PrintCreateDataSource(yaml.YAMLObject):
    yaml_tag = "!createDataSource"
