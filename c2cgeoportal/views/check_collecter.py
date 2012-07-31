# -*- coding: utf-8 -*-

from time import time

from pyramid.view import view_config
from pyramid.response import Response

from httplib2 import Http


class CheckerCollecter(object):

    def __init__(self, request):
        self.status_int = 200
        self.request = request
        self.settings = request.registry.settings.check_collecter

    # Method called by the sysadmins to make sure that our app work well.
    # Then this name must not change.
    @view_config(route_name='check_collecter')
    def check_collecter(self):
        body = ""
        start0 = time()
        for host in self.settings['hosts']:
            params = self.request.params
            check_type = params['type'] if 'type' in params else \
                    host['type'] if 'type' in host else 'default'
            checks = self.settings['check_type'][check_type]
            body += "<h2>%s</h2>" % host['display']

            start1 = time()
            for check in checks:
                start2 = time()
                res = self._testurl("%s/%s" % (host['url'], check['name']))
                body += "<p>%s: %s (%0.4fs)</p>" % \
                        (check['display'], res, time() - start2)
            body += "<p>Elapsed: %0.4f</p>" % (time() - start1)
        body += "<p>Elapsed all: %0.4f</p>" % (time() - start0)
        return Response(body=body, status_int=self.status_int)

    def _testurl(self, url):
        h = Http()
        resp, content = h.request(url)

        if resp['status'] != '200':
            self.status_int = max(self.status_int, int(resp['status']))

        return content
