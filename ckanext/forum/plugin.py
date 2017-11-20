import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from flask.ext.markdown import Markdown
from flask.ext.sqlalchemy import SQLAlchemy

import models
import views


class ForumPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IMiddleware)

    # IConfigurer

    def update_config(self, config_):
        plugins.toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'forum')

        self.conn_string = config_['sqlalchemy.url']
        config_['SQLALCHEMY_DATABASE_URI'] = config_['sqlalchemy.url']

    # IBlueprint

    def get_blueprint(self):
        blueprint = views.bp
        blueprint.template_folder = 'templates'
        return blueprint

    # IMiddleware
    def make_middleware(self, app, config):
        from ckan.config.middleware.pylons_app import CKANPylonsApp
        # NOTE: during Pylons to Flask migration CKAN calls this method
        # twice. We don't need to do anything with Pylons app
        if isinstance(app, CKANPylonsApp):
            return app

        db = SQLAlchemy(app)
        # NOTE: init DB and create all tables in it.
        models.init_db(db)
        db.create_all()

        # Markdown
        Markdown(app, safe_mode='escape')

        return app

    def make_error_log_middleware(self, app, config):
        u'''Return an app configured with this error log middleware
        Note that both on the Flask and Pylons middleware stacks, this
        method will receive a wrapped WSGI app, not the actual Flask or
        Pylons app.
        '''
        # TODO: add app error handling
        return app
