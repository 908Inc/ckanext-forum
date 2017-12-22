import logging
from operator import itemgetter

from ckan.lib.base import BaseController, abort
from ckan.plugins import toolkit as tk
from ckan.lib.helpers import flash_success, flash_error
from ckan.common import c
from jinja2.filters import do_striptags


from ckanext.forum.models import Board, Thread, Post
from ckanext.forum.forms import CreateThreadForm, CreatePostForm, CreateBoardForm


log = logging.getLogger(__name__)


class ForumController(BaseController):
    paginated_by = 3

    def __render(self, template_name, context):
        context.update({
            'board_list': Board.all(),
        })
        return tk.render(template_name, context)

    def index(self):
        page = int(tk.request.GET.get('page', 1))
        total_pages = int(Thread.all().count() / self.paginated_by) + 1
        if not 1 < page <= total_pages:
            page = 1
        context = {
            'thread_list': Thread.all().offset((page - 1) * self.paginated_by).limit(self.paginated_by),
            'total_pages': total_pages,
            'current_page': page,
        }
        log.debug('ForumController.index context: %s', context)
        return self.__render('forum_index.html', context)

    def thread_add(self):
        if c.userobj is None:
            tk.redirect_to(tk.url_for(controller='user', action='login'))
        form = CreateThreadForm(tk.request.POST)
        if tk.request.POST:
            if form.validate():
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
        }
        log.debug('ForumController.thread_add context: %s', context)
        return self.__render('create_thread.html', context)

    def board_add(self):
        if c.userobj is None:
            tk.redirect_to(tk.url_for(controller='user', action='login'))
        form = CreateBoardForm(tk.request.POST)
        if tk.request.POST:
            if form.validate():
                board = Board()
                form.populate_obj(board)
                board.save()
                flash_success(tk._('You successfully create thread'))
                tk.redirect_to(board.get_absolute_url())
            else:
                flash_error(tk._('You have errors in form'))
                log.error("Validate errors: %s", form.errors)
        context = {
            'form': form,
        }
        log.debug('ForumController.thread_add context: %s', context)
        return self.__render('create_board.html', context)

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
            'thread': thread,
            'form': form
        }
        log.debug('ForumController.thread_show context: %s', context)
        return self.__render('thread.html', context)

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
            'thread_list': Thread.filter_board(board_slug=board.slug).offset((page - 1) * self.paginated_by).limit(self.paginated_by),
            'total_pages': total_pages,
            'current_page': page,
        }
        log.debug('ForumController.board_show context: %s', context)
        return self.__render('forum_index.html', context)

    def activity(self):
        thread_activity = Thread.all().order_by(Thread.created.desc())
        post_activity = Post.all().order_by(Post.created.desc())
        activity = [dict(id=i.id,
                         url=i.get_absolute_url(),
                         ban_url=tk.url_for('forum_thread_ban', id=i.id),
                         type=tk._('Thread'),
                         content=i.content,
                         author_name=i.author.name,
                         created=i.created) for i in thread_activity]
        activity += [dict(id=i.id,
                          url=i.get_absolute_url(),
                          ban_url=tk.url_for('forum_post_ban', id=i.id),
                          type=tk._('Post'),
                          content=i.content,
                          author_name=i.author.name,
                          created=i.created) for i in post_activity]
        context = {
            'activity': sorted(activity, key=itemgetter('created'), reverse=True)
        }
        return self.__render('forum_activity.html', context)

    def thread_ban(self, id):
        thread = Thread.get_by_id(id=id)
        if not thread:
            abort(404)
        if c.userobj is None or not c.userobj.sysadmin:
            tk.redirect_to(tk.url_for(controller='user', action='login'))
        thread.ban()
        tk.redirect_to(tk.url_for('forum_activity'))

    def post_ban(self, id):
        post = Post.get_by_id(id=id)
        if not post:
            abort(404)
        if c.userobj is None or not c.userobj.sysadmin:
            tk.redirect_to(tk.url_for(controller='user', action='login'))
        post.ban()
        tk.redirect_to(tk.url_for('forum_activity'))