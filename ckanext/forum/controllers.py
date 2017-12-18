import logging
from ckan.lib.base import BaseController, abort
from ckan.plugins import toolkit as tk
from ckan.lib.helpers import flash_success, flash_error
from ckan.common import c
from jinja2.filters import do_striptags


from ckanext.forum.models import Board, Thread, Post
from ckanext.forum.forms import CreateThreadForm, CreatePostForm


log = logging.getLogger(__name__)


class ForumController(BaseController):
    paginated_by = 3

    def index(self):
        page = int(tk.request.GET.get('page', 1))
        total_pages = int(Thread.all().count() / self.paginated_by) + 1
        if not 1 < page <= total_pages:
            page = 1
        context = {
            'board_list': Board.all(),
            'thread_list': Thread.all().offset((page - 1) * self.paginated_by).limit(self.paginated_by),
            'total_pages': total_pages,
            'current_page': page,
        }
        log.debug('ForumController.index context: %s', context)
        return tk.render('forum_index.html', context)

    def thread_add(self):
        if c.userobj is None:
            tk.redirect_to(tk.url_for(controller='user', action='login'))
        form = CreateThreadForm(tk.request.POST)
        if tk.request.POST and form.validate() and c.user:
            thread = Thread()
            form.populate_obj(thread)
            thread.author_id = c.userobj.id
            thread.content = do_striptags(thread.content)
            thread.save()
            log.debug("Form data is valid. Content: %s", do_striptags(thread.content))
            flash_success(tk._('You successfully create thread'))
            tk.redirect_to(thread.get_absolute_url())
        else:
            flash_error(tk._('You have errors in form'))
            log.error("Validate errors: %s", form.errors)
        context = {
            'form': form,
            'board_list': Board.all(),
        }
        log.debug('ForumController.thread_add context: %s', context)
        return tk.render('create_thread.html', context)

    def thread_show(self, slug, id):
        thread = Thread.get_by_id(id=id)
        if not thread:
            abort(404)
        form = CreatePostForm(tk.request.POST)
        if tk.request.POST:
            if c.userobj is None:
                tk.redirect_to(tk.url_for(controller='user', action='login'))
            if form.validate():
                post = Post()
                form.populate_obj(post)
                post.thread = thread
                post.author_id = c.userobj.id
                post.content = do_striptags(post.content)
                post.save()
                flash_success(tk._('You successfully create comment'))
                return tk.redirect_to(thread.get_absolute_url())
            else:
                flash_error(tk._('You have errors in form'))
        context = {
            'board_list': Board.all(),
            'thread': thread,
            'form': form
        }
        log.debug('ForumController.thread_show context: %s', context)
        return tk.render('thread.html', context)

    def board_show(self, slug):
        board = Board.get_by_slug(slug)
        if not board:
            abort(404)
        page = int(tk.request.GET.get('page', 1))
        total_pages = int(Thread.filter_board(board_slug=board.slug).count() / self.paginated_by) + 1
        if not 1 < page <= total_pages:
            page = 1
        context = {
            'board': board,
            'board_list': Board.all(),
            'thread_list': Thread.filter_board(board_slug=board.slug).offset((page - 1) * self.paginated_by).limit(self.paginated_by),
            'total_pages': total_pages,
            'current_page': page,
        }
        log.debug('ForumController.board_show context: %s', context)
        return tk.render('forum_index.html', context)