import base64
import logging
import os
from operator import itemgetter
from urlparse import urljoin

import jinja2
from babel.support import Translations

import ckan.lib.jobs as jobs
from ckan.common import c
from ckan.lib.base import BaseController, abort
from ckan.lib.helpers import flash_success, flash_error, get_page_number, full_current_url, Page, redirect_to
from ckan.model import User
from ckan.plugins import toolkit as tk

from ckanext.forum.forms import CreateThreadForm, CreatePostForm, CreateBoardForm
from ckanext.forum.models import Board, Thread, Post, BannedUser, Unsubscription

log = logging.getLogger(__name__)


def do_if_user_not_sysadmin():
    if not c.userobj:
        tk.redirect_to(tk.url_for(controller='user', action='login'))
    if not c.userobj.sysadmin:
        abort(404)  # not 403 for security reasons


def send_notifications_on_new_post(post, lang):
    from ckan.model import User
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    locale_dir = os.path.join(os.path.dirname(__file__), 'i18n')
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), extensions=['jinja2.ext.i18n'])
    translations = Translations.load(locale_dir, [lang], domain='ckanext-forum')
    env.install_gettext_translations(translations)
    env.globals['get_locale'] = lambda: lang
    post_author = User.get(post.author_id)

    thread = Thread.get_by_id(post.thread_id)
    author_ids = set([p.author_id for p in thread.forum_posts] + [thread.author_id])
    author_ids -= set([u.user_id for u in Unsubscription.filter_by_thread_id(post.thread_id)])

    for author_id in author_ids:
        if author_id == post_author.id:
            continue
        user = User.get(author_id)
        unsubscribe_url = tk.url_for('forum_unsubscribe', base64_name=base64.b64encode(user.name), thread_id=thread.id)
        context = {
            'user_name': user.name,
            'site_title': tk.config.get('ckan.site_title'),
            'site_url': tk.config.get('ckan.site_url'),
            'post_content': post.content,
            'title': env.globals['gettext']('New post'),
            'unsubscribe_url': urljoin(tk.config['ckan.site_url'], unsubscribe_url),
            'username': post_author.name,
            'thread_url': urljoin(tk.config['ckan.site_url'], thread.get_absolute_url()),
        }
        template = env.get_template('forum_new_post_mail.html')
        body = template.render(context)
        log.debug('Email body %s', body)
        tk.get_action('send_mail')({}, {
            'to': user.email,
            'subject': env.globals['gettext']('New post'),
            'message_html': body
        })


class ForumController(BaseController):
    paginated_by = 10

    def __render(self, template_name, context):
        if not c.userobj or not c.userobj.sysadmin:
            board_list = Board.filter_active()
        else:
            board_list = Board.all()
        context.update({
            'board_list': list(board_list),
        })
        log.debug('ForumController.__render context: %s', context)
        return tk.render(template_name, context)

    def index(self):
        page = get_page_number(tk.request.params)
        total_rows = Thread.all().count()
        total_pages = (Thread.all().count() - 1) / self.paginated_by + 1
        if not 0 < page <= total_pages:
            redirect_to('forum_index')
        thread_list = Thread.all().offset((page - 1) * self.paginated_by).limit(self.paginated_by)

        c.page = Page(
            collection=thread_list,
            page=page,
            item_count=total_rows,
            items_per_page=self.paginated_by
        )
        return self.__render('forum_index.html', {'thread_list': thread_list})


    def thread_add(self):
        if not c.userobj:
            tk.redirect_to(tk.url_for(controller='user', action='login', came_from=full_current_url()))
        if BannedUser.check_by_id(c.userobj):
            flash_error(tk._('You are banned'))
            tk.redirect_to(tk.url_for('forum_index'))
        form = CreateThreadForm(tk.request.POST)
        if tk.request.POST:
            if form.validate():
                thread = tk.get_action('forum_create_thread')({'auth_user_obj': c.userobj}, form.data)
                log.debug("Form data is valid. Content: %s", thread.content)
                flash_success(tk._('You successfully create thread'))
                tk.redirect_to(thread.get_absolute_url())
            else:
                flash_error(tk._('You have errors in form'))
                log.error("Validate errors: %s", form.errors)
        context = {
            'form': form,
            'board_can_post': Board.filter_can_post()
        }
        return self.__render('create_thread.html', context)

    def board_add(self):
        do_if_user_not_sysadmin()
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
                post = tk.get_action('forum_create_post')(
                    {'auth_user_obj': c.userobj},
                    {'thread_id': id, 'content': form.data['content']})
                if post:
                    jobs.enqueue(send_notifications_on_new_post, [post, tk.request.environ.get('CKAN_LANG')])
                    flash_success(tk._('You successfully create comment'))
                else:
                    flash_error(tk._('Thread is closed for comments'))
                return tk.redirect_to(thread.get_absolute_url())
            else:
                flash_error(tk._('You have errors in form'))
        page = get_page_number(tk.request.params)
        total_rows = Post.filter_thread(thread.id).count()
        total_pages = int(total_rows / self.paginated_by) + 1
        if not 0 < page <= total_pages:
            redirect_to('forum_index')
        posts_list = Post.filter_thread(thread.id).offset((page - 1) * self.paginated_by).limit(self.paginated_by)
        c.page = Page(
            collection=posts_list,
            page=page,
            item_count=total_rows,
            items_per_page=self.paginated_by
        )
        context = {
            'thread': thread,
            'form': form,
            'posts': posts_list
        }
        return self.__render('thread.html', context)

    def board_show(self, slug):
        board = Board.get_by_slug(slug)
        if not board:
            abort(404)
        page = get_page_number(tk.request.params)
        total_rows = Thread.filter_board(board_slug=board.slug).count()
        total_pages = int(total_rows / self.paginated_by) + 1
        if not 0 < page <= total_pages:
            redirect_to('forum_index')
        thread_list = Thread.filter_board(board_slug=board.slug).offset((page - 1) * self.paginated_by).limit(
            self.paginated_by)
        c.page = Page(
            collection=thread_list,
            page=page,
            item_count=total_rows,
            items_per_page=self.paginated_by
        )
        return self.__render('forum_index.html', {'board': board, 'thread_list': thread_list})

    def activity(self):
        do_if_user_not_sysadmin()
        page = get_page_number(tk.request.params)
        total_rows = Thread.all().count()
        total_pages = (total_rows - 1) / self.paginated_by + 1
        if not 0 < page <= total_pages:
            redirect_to('forum_activity')
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
        c.page = Page(
            collection=thread_activity,
            page=page,
            item_count=total_rows,
            items_per_page=self.paginated_by
        )
        return self.__render('forum_activity.html', {'activity': activity[start_elem : end_elem]})

    def thread_ban(self, id):
        do_if_user_not_sysadmin()
        thread = Thread.get_by_id(id=id)
        if not thread:
            abort(404)
        thread.ban()
        if tk.request.GET.get('with_user'):
            BannedUser.ban(thread.author_id)
        tk.redirect_to(tk.url_for('forum_activity'))

    def post_ban(self, id):
        do_if_user_not_sysadmin()
        post = Post.get_by_id(id=id)
        if not post:
            abort(404)
        post.ban()
        if tk.request.GET.get('with_user'):
            BannedUser.ban(post.author_id)
        tk.redirect_to(tk.url_for('forum_activity'))

    def board_hide(self, slug):
        do_if_user_not_sysadmin()
        board = Board.get_by_slug(slug)
        if not board:
            abort(404)
        board.hide()
        flash_success(tk._('You successfully hided board'))
        tk.redirect_to(tk.url_for('forum_index'))

    def board_unhide(self, slug):
        do_if_user_not_sysadmin()
        board = Board.get_by_slug(slug)
        if not board:
            abort(404)
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
