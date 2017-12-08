# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from ckan import model
from ckan.model import meta, User, Package, Session, Resource

from sqlalchemy import func, types, Table, ForeignKey, Column, Index
from sqlalchemy.orm import relation, backref, subqueryload, foreign, remote

from slugify import slugify_url

log = logging.getLogger(__name__)

DEFAULT_BOARDS = {
    'Робота порталу': '',
    'Відкриті дані Україна': '',
    'Відкриті дані Світ': ''
}


def init_db():
    """
    Create boards, threads and posts tables in the database.
    Prepopulate board table with default data.
    """
    if not model.package_table.exists():
        # during tests?
        return

    if not board_table.exists():
        board_table.create(checkfirst=True)
        thread_table.create(checkfirst=True)
        post_table.create(checkfirst=True)
        log.debug("Forum tables have been created")

        session = Session()
        for board_name, board_desc in DEFAULT_BOARDS.iteritems():
            board = Board()
            board.name = board_name
            board.slug = slugify_url(board_name)
            board.description = board_desc
            session.add(board)

        if session.new:
            log.debug('Default boards created')
            session.commit()

    else:
        log.debug('Forum tables already exist')


board_table = Table('forum_board', meta.metadata,
                    Column('id', types.Integer, primary_key=True, autoincrement=True),
                    Column('name', types.Unicode(128)),
                    Column('slug', types.String(128), unique=True),
                    Column('description', types.UnicodeText)
                    )

thread_table = Table('forum_thread', meta.metadata,
                     Column('id', types.Integer, primary_key=True, autoincrement=True),
                     Column('author_id', types.Unicode, nullable=False, index=True),
                     Column('board_id', types.Integer,
                            ForeignKey('forum_board.id', onupdate='CASCADE', ondelete='CASCADE'),
                            nullable=False, index=True),
                     Column('name', types.Unicode(128)),
                     Column('content', types.UnicodeText),
                     Column('slug', types.String(128), unique=True),
                     Column('created', types.DateTime, default=datetime.utcnow, nullable=False),
                     Column('updated', types.DateTime, default=datetime.utcnow, nullable=False)
                     )

post_table = Table('forum_post', meta.metadata,
                   Column('id', types.Integer, primary_key=True, autoincrement=True),
                   Column('content', types.UnicodeText),
                   Column('author_id', types.Unicode, nullable=False, index=True),
                   Column('thread_id', types.Integer,
                          ForeignKey('forum_thread.id', onupdate='CASCADE', ondelete='CASCADE'),
                          nullable=False, index=True),
                   Column('created', types.DateTime, default=datetime.utcnow),
                   Column('updated', types.DateTime, default=datetime.utcnow)
                   )


class Board(object):
    """
    Forum board mapping class
    """

    @classmethod
    def all(cls):
        return Session.query(cls).all()


class Thread(object):
    """
    Forum thread mapping class
    """
    def save(self):
        if not hasattr(self, 'slug') or not self.slug:
            self.slug = slugify_url(self.name)
        session = Session()
        log.debug(self)
        session.add(self)

    @classmethod
    def all(cls):
        return Session.query(cls).all()


class Post(object):
    """
    Forum thread mapping class
    """

    @classmethod
    def all(cls):
        return Session.query(cls).all()


meta.mapper(Board, board_table)

meta.mapper(Thread,
            thread_table,
            properties={
                'author': relation(User,
                                   backref=backref('forum_threads', cascade='all, delete-orphan', single_parent=True),
                                   primaryjoin=foreign(thread_table.c.author_id) == remote(User.id)
                                   )
            }
            )

meta.mapper(Post,
            post_table,
            properties={
                'author': relation(User,
                                   backref=backref('forum_posts', cascade='all, delete-orphan', single_parent=True),
                                   primaryjoin=foreign(post_table.c.author_id) == remote(User.id)
                                   )
            }
            )

if __name__ == "__main__":
    init_db()
