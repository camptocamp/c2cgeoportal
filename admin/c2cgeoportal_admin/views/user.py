from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from c2cgeoportal_commons.models.main import User


@view_config(route_name='user', renderer='../templates/mytemplate.jinja2')
def user_view(request):
    try:
        users = request.dbsession.query(User).all();
        if len(users) > 0:
            return {'first': users[0], 'project': 'c2cgeoportal_admin'}
        else:
            return {}
                    
    except DBAPIError:
        return Response(db_err_msg, content_type='text/plain', status=500)
    


db_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to run the "initialize_c2cgeoportal_admin_db" script
    to initialize your database tables.  Check your virtual
    environment's "bin" directory for this script and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""
