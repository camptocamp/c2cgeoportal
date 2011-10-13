Integration
===========

Fanstatic can be integrated with a number of web frameworks:

* zope/grok through :pypi:`zope.fanstatic`   

* django through django_fanstatic_.

.. _django_fanstatic: http://bitbucket.org/fanstatic/django-fanstatic

In order to integrate fanstatic with your web framework, make sure the 
following conditions are met:

* **base_url**: if your web framework supports virtual hosting, make sure
  to set the ``base_url`` attribute on the NeededResources object. 

* **error pages**: if your web framework renders error pages, make sure to
  clear the NeededResources before rendering the error page, in order to
  prevent resources from the original page to 'leak' onto the error page.

* **url calculation**: fanstatic can also serve non-javascript and non-CSS
  resources such as images that you link to from the views in your application.
  In order to do so, we advise to support rendering URLs to resources
  from the view/page templates in your web framework.

