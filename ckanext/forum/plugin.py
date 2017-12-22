from ckan import plugins
from ckan.plugins import toolkit as tk


class ForumPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        tk.add_template_directory(config_, 'templates')
        tk.add_public_directory(config_, 'public')
        tk.add_resource('fanstatic', 'forum')

    # IRoutes

    def after_map(self, sub_map):
        from ckan.config.routing import SubMapper
        with SubMapper(sub_map, controller='ckanext.forum.controllers:ForumController') as m:
            m.connect('forum_index', '/forum', action='index')
            m.connect('forum_thread_add', '/forum/thread_add', action='thread_add')
            m.connect('forum_board_add', '/forum/board_add', action='board_add')
            m.connect('forum_activity', '/forum/activity', action='activity')
            m.connect('forum_thread_ban', '/forum/thread_ban/:id', action='thread_ban')
            m.connect('forum_post_ban', '/forum/post_ban/:id', action='post_ban')
            m.connect('forum_board_show', '/forum/:slug', action='board_show')
            m.connect('forum_thread_show', '/forum/:slug/:id', action='thread_show')
        return sub_map
