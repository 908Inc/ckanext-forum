from jinja2.filters import do_striptags
from HTMLParser import HTMLParser

import ckan.logic as logic
from ckanext.forum.models import Thread, Post


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def forum_create_thread(context, data_dict):
    """
    Create new thread on board
    data_dict:
        board_id - Board id for thread
        name - Thread name
        content - Thread text
        can_post - False if thread is closed for posts
    :return Thread
    """
    thread = Thread()
    thread.board_id = logic.get_or_bust(data_dict, 'board_id')
    thread.name = logic.get_or_bust(data_dict, 'name')
    thread.content = strip_tags(logic.get_or_bust(data_dict, 'content'))
    thread.author = logic.get_or_bust(context, 'auth_user_obj')
    if 'can_post' in data_dict and not data_dict['can_post']:
        thread.can_post = False
    thread.save()
    return thread


def forum_create_post(context, data_dict):
    """
    Create post in thread
    data_dict:
        thread_id - Thread id for post
        content - Post text
    :return Post
    """
    thread = Thread.get_by_id(logic.get_or_bust(data_dict, 'thread_id'))
    if thread.can_post:
        post = Post()
        post.thread = thread
        post.content = strip_tags(logic.get_or_bust(data_dict, 'content'))
        post.author_id = logic.get_or_bust(context, 'auth_user_obj').id
        post.save()
        return post
