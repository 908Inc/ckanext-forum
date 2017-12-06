import logging
from ckan.lib.base import BaseController
from ckan.plugins import toolkit as tk

from ckanext.forum.models import Board, Thread


log = logging.getLogger(__name__)


class ForumController(BaseController):

    def index(self):
        context = {
            'board_list': Board.all(),
            'thread_list': Thread.all()
        }
        log.debug('ForumController.index context: %s', context)
        return tk.render('forum_index.html', context)
