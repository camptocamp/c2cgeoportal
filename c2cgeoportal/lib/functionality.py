# -*- coding: utf-8 -*-

# Copyright (c) 2013, Camptocamp SA
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


from c2cgeoportal.lib import get_setting


def _get_config_functionality(name, registered, config):
    result = None

    if registered:
        result = get_setting(
            config, ('functionalities', 'registered', name))
    if result is None:
        result = get_setting(
            config, ('functionalities', 'anonymous', name))

    if result is None:
        result = []
    elif not isinstance(result, list):
        result = [result]

    return result


def _get_db_functionality(name, user):
    result = [
        functionality.value for
        functionality in user.functionalities
        if functionality.name == name]
    if len(result) == 0:
        result = [
            functionality.value for
            functionality in user.role.functionalities
            if functionality.name == name]
    return result


def get_functionality(name, config, request):
    result = []
    if request.user:
        result = _get_db_functionality(name, request.user)
    if len(result) == 0:
        result = _get_config_functionality(name, request.user is not None, config)
    return result
