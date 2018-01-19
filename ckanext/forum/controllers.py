import logging
import base64
from operator import itemgetter

from ckan.lib.base import BaseController, abort
from ckan.model import User
from ckan.plugins import toolkit as tk
from ckan.lib.helpers import flash_success, flash_error, get_page_number
from ckan.common import c
from jinja2.filters import do_striptags
import ckan.lib.jobs as jobs

from ckanext.forum.models import Board, Thread, Post, BannedUser, Unsubscription
from ckanext.forum.forms import CreateThreadForm, CreatePostForm, CreateBoardForm


log = logging.getLogger(__name__)


def send_notifications_on_new_post(post):
    from ckan.lib.mailer import mail_user
    from ckan.lib.base import render_jinja2
    from ckan.model import User

    post_author = User.get(post.author_id)

    thread = Thread.get_by_id(post.thread_id)
    author_ids = set([p.author_id for p in thread.forum_posts] + [thread.author_id])
    author_ids -= set([u.user_id for u in Unsubscription.filter_by_thread_id(post.thread_id)])

    for author_id in author_ids:
        user = User.get(author_id)
        unsubscribe_url = tk.url_for('forum_unsubscribe', base64_name=base64.b64encode(user.name), thread_id=thread.id)
        context = {
            'post_content': post.content,
            'title': tk._('New post'),
            'unsubscribe_url': tk.config['ckan.site_url'] + unsubscribe_url,
            'username': post_author.name
        }
        body = render_jinja2('forum_new_post_mail.html', context)

        mail_user(user, tk._('New post'), body)


class ForumController(BaseController):
    paginated_by = 3.0

    def __render(self, template_name, context):
        if c.userobj is None or not c.userobj.sysadmin:
            board_list = Board.filter_active()
        else:
            board_list = Board.all()
        context.update({
            'board_list': board_list,
        })
        log.debug('ForumController.__render context: %s', context)
        return tk.render(template_name, context)

    def index(self):
        page = get_page_number(tk.request.params) or 1
        total_pages = float(Thread.all().count() / self.paginated_by)
        if total_pages > 1:
            total_pages = int(total_pages + 1)
        if not 1 < page <= total_pages:
            page = 1
        context = {
            'thread_list': Thread.all().offset((page - 1) * self.paginated_by).limit(self.paginated_by),
            'total_pages': total_pages,
            'current_page': page,
        }
        return self.__render('forum_index.html', context)

    def thread_add(self):
        if c.userobj is None:
            tk.redirect_to(tk.url_for(controller='user', action='login'))
        if BannedUser.check_by_id(c.userobj):
            flash_error(tk._('You are banned'))
            tk.redirect_to(tk.url_for('forum_index'))
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
        return self.__render('create_board.html', context)

    def thread_show(self, slug, id):
        thread = Thread.get_by_id(id=id)
        if not thread:
            abort(404)
        form = CreatePostForm(tk.request.POST)
        if tk.request.POST:
            if c.userobj is None:
                tk.redirect_to(tk.url_for(controller='user', action='login'))
            if BannedUser.check_by_id(c.userobj):
                flash_error(tk._('You are banned'))
                tk.redirect_to(thread.get_absolute_url())
            if form.validate():
                post = Post()
                form.populate_obj(post)
                post.thread = thread
                post.author_id = c.userobj.id
                post.content = do_striptags(post.content)
                post.save()
                jobs.enqueue(send_notifications_on_new_post, [post])
                flash_success(tk._('You successfully create comment'))
                return tk.redirect_to(thread.get_absolute_url())
            else:
                flash_error(tk._('You have errors in form'))
        context = {
            'thread': thread,
            'form': form,
            'posts': Post.filter_thread(thread.id)
        }
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
        return self.__render('forum_index.html', context)

    def activity(self):
        page = get_page_number(tk.request.params) or 1
        total_pages = float(Thread.all().count() / self.paginated_by)
        if total_pages > 1:
            total_pages = int(total_pages + 1)
        if not 1 < page <= total_pages:
            page = 1
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
        activity = sorted(activity, key=itemgetter('created'), reverse=True)
        start_elem = int((page - 1) * self.paginated_by)
        end_elem = int(page * self.paginated_by)
        context = {
            'total_pages': total_pages,
            'current_page': page,
            'activity': activity[start_elem: end_elem]
        }
        return self.__render('forum_activity.html', context)

    def thread_ban(self, id):
        thread = Thread.get_by_id(id=id)
        if not thread:
            abort(404)
        if c.userobj is None or not c.userobj.sysadmin:
            tk.redirect_to(tk.url_for(controller='user', action='login'))
        thread.ban()
        if tk.request.GET.get('with_user'):
            BannedUser.ban(thread.author_id)
        tk.redirect_to(tk.url_for('forum_activity'))

    def post_ban(self, id):
        post = Post.get_by_id(id=id)
        if not post:
            abort(404)
        if c.userobj is None or not c.userobj.sysadmin:
            tk.redirect_to(tk.url_for(controller='user', action='login'))
        post.ban()
        if tk.request.GET.get('with_user'):
            BannedUser.ban(post.author_id)
        tk.redirect_to(tk.url_for('forum_activity'))

    def board_hide(self, slug):
        board = Board.get_by_slug(slug)
        if not board:
            abort(404)
        if c.userobj is None or not c.userobj.sysadmin:
            tk.redirect_to(tk.url_for(controller='user', action='login'))
        board.hide()
        flash_success(tk._('You successfully hided board'))
        tk.redirect_to(tk.url_for('forum_index'))

    def board_unhide(self, slug):
        board = Board.get_by_slug(slug)
        if not board:
            abort(404)
        if c.userobj is None or not c.userobj.sysadmin:
            tk.redirect_to(tk.url_for(controller='user', action='login'))
        board.unhide()
        flash_success(tk._('You successfully unhided board'))
        tk.redirect_to(tk.url_for('forum_index'))

    def unsubscribe(self, base64_name, thread_id):
        log.debug('Unsubscribing %s %s', base64.b64decode(base64_name), thread_id)
        thread = Thread.get_by_id(thread_id)
        user = User.get(base64.b64decode(base64_name))
        if not thread or not user:
            abort(404)

        Unsubscription.add(user.id, thread.id)
        flash_success(tk._('You successfully unsibsribed'))
        tk.redirect_to(thread.get_absolute_url())