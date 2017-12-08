import logging
from ckan.lib.base import BaseController
from ckan.plugins import toolkit as tk
from ckan.common import c


from ckanext.forum.models import Board, Thread
from ckanext.forum.forms import CreateThreadForm


log = logging.getLogger(__name__)


class ForumController(BaseController):

    def index(self):
        context = {
            'board_list': Board.all(),
            'thread_list': Thread.all()
        }
        log.debug('ForumController.index context: %s', context)
        return tk.render('forum_index.html', context)

    def thread_add(self):
        log.debug(c.userobj.as_dict())
        form = CreateThreadForm(tk.request.POST)
        if tk.request.POST and form.validate():
            thread = Thread()
            form.populate_obj(thread)
            thread.author_id = c.userobj.id
            thread.save()
            log.debug("Form data is valid")
            tk.redirect_to('/forum')
        else:
            log.error("Validate errors: %s", form.errors)
        context = {
            'form': form,
            'board_list': Board.all(),
        }
        return tk.render('create_thread.html', context)
