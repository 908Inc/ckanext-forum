import logging
from ckan.lib.base import BaseController
from ckan.plugins import toolkit as tk
from ckan.common import c
from ckan.controllers import user


from ckanext.forum.models import Board, Thread, Post
from ckanext.forum.forms import CreateThreadForm, CreatePostForm


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
        if c.user is None:
            tk.redirect_to(tk.url_for(controller='user', action='login'))
        log.debug(c.userobj.as_dict())
        form = CreateThreadForm(tk.request.POST)
        if tk.request.POST and form.validate() and c.user:
            thread = Thread()
            form.populate_obj(thread)
            thread.author_id = c.userobj.id
            thread.save()
            log.debug("Form data is valid")
            tk.redirect_to(tk.url_for('forum_board_show', slug=thread.board.slug))
        else:
            log.error("Validate errors: %s", form.errors)
        context = {
            'form': form,
            'board_list': Board.all(),
        }
        log.debug('ForumController.thread_add context: %s', context)
        return tk.render('create_thread.html', context)

    def thread_show(self, slug):
        thread = Thread.get_by_slug(slug=slug)
        form = CreatePostForm(tk.request.POST)
        if tk.request.POST and form.validate():
            if c.user is None:
                tk.redirect_to(tk.url_for(controller='user', action='login'))
            post = Post()
            form.populate_obj(post)
            post.thread = thread
            post.author_id = c.userobj.id
            post.save()
            tk.redirect_to(tk.url_for('forum_thread_show', slug=thread.slug))
        context = {
            'board_list': Board.all(),
            'thread': thread,
            'form': form
        }
        log.debug('ForumController.thread_show context: %s', context)
        return tk.render('thread.html', context)

    def board_show(self, slug):
        context = {
            'board_list': Board.all(),
            'thread_list': Thread.filter_board(board_slug=slug)
        }
        log.debug('ForumController.board_show context: %s', context)
        return tk.render('forum_index.html', context)