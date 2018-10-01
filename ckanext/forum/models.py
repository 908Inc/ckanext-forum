# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from operator import isCallable

from slugify import slugify
from sqlalchemy import types, Table, ForeignKey, Column
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import relation, backref, foreign, remote

from ckan import model
from ckan.model import meta, User, Session
from ckan.plugins import toolkit as tk

log = logging.getLogger(__name__)

DEFAULT_BOARDS = {
    u'Робота порталу': '',
    u'Відкриті дані Україна': '',
    u'Відкриті дані Світ': ''
}


def init_db():
    """
    Create boards, threads and posts tables in the database.
    Prepopulate board table with default data.
    """
    if not model.package_table.exists():
        # during tests?
        return

    session = Session()
    if not board_table.exists():
        board_table.create(checkfirst=True)
        thread_table.create(checkfirst=True)
        post_table.create(checkfirst=True)
        log.debug("Forum tables have been created")

        for board_name, board_desc in DEFAULT_BOARDS.iteritems():
            board = Board()
            board.name = board_name
            board.slug = slugify(board_name)
            board.description = board_desc
            session.add(board)

        if session.new:
            log.debug('Default boards created')
            session.commit()

    if not migration_table.exists():
        migration_table.create(checkfirst=True)
        session.commit()
    if not banned_table.exists():
        banned_table.create(checkfirst=True)
        session.commit()
    if not unsubscription_table.exists():
        unsubscription_table.create(checkfirst=True)
        session.commit()
    migration_number = session.query(migration_table).count()
    log.debug('Migration number: %s', migration_number)
    migration_sql_list = [
        "ALTER TABLE forum_post ADD COLUMN active boolean DEFAULT TRUE",
        "ALTER TABLE forum_thread ADD COLUMN active boolean DEFAULT TRUE",
        "ALTER TABLE forum_board ADD COLUMN active boolean DEFAULT TRUE",
        "ALTER TABLE forum_thread DROP COLUMN slug",
        "ALTER TABLE forum_thread ADD COLUMN can_post boolean DEFAULT TRUE",
        "ALTER TABLE forum_board ADD COLUMN can_post boolean DEFAULT TRUE",
        u"INSERT INTO forum_board(\"id\", \"name\", \"slug\", \"description\", \"active\", \"can_post\") " +
        u"VALUES(DEFAULT, 'Запропонувати набір', 'zaproponuvati-nabir', '', true, false)"
    ]
    for counter, sql in enumerate(migration_sql_list, start=1):
        if migration_number < counter:
            try:
                log.debug(sql)
                session.execute(sql)
            except ProgrammingError as e:
                print(e)
                log.debug('Migration have been rolled back.')
                session.rollback()
            finally:
                session.execute(migration_table.insert())
                session.commit()

    session.close()


board_table = Table('forum_board', meta.metadata,
                    Column('id', types.Integer, primary_key=True, autoincrement=True),
                    Column('name', types.Unicode(128)),
                    Column('slug', types.String(128), unique=True),
                    Column('description', types.UnicodeText),
                    Column('active', types.Boolean, default=True),
                    Column('can_post', types.Boolean, default=True)
                    )

thread_table = Table('forum_thread', meta.metadata,
                     Column('id', types.Integer, primary_key=True, autoincrement=True),
                     Column('author_id', types.Unicode, nullable=False, index=True),
                     Column('board_id', types.Integer,
                            ForeignKey('forum_board.id', onupdate='CASCADE', ondelete='CASCADE'),
                            nullable=False, index=True),
                     Column('name', types.Unicode(128)),
                     Column('content', types.UnicodeText),
                     Column('created', types.DateTime, default=datetime.utcnow, nullable=False),
                     Column('updated', types.DateTime, default=datetime.utcnow, nullable=False),
                     Column('active', types.Boolean, default=True),
                     Column('can_post', types.Boolean, default=True)
                     )

post_table = Table('forum_post', meta.metadata,
                   Column('id', types.Integer, primary_key=True, autoincrement=True),
                   Column('content', types.UnicodeText),
                   Column('author_id', types.Unicode, nullable=False, index=True),
                   Column('thread_id', types.Integer,
                          ForeignKey('forum_thread.id', onupdate='CASCADE', ondelete='CASCADE'),
                          nullable=False, index=True),
                   Column('created', types.DateTime, default=datetime.utcnow),
                   Column('updated', types.DateTime, default=datetime.utcnow),
                   Column('active', types.Boolean, default=True),
                   )

banned_table = Table('forum_ban', meta.metadata,
                     Column('id', types.Integer, primary_key=True, autoincrement=True),
                     Column('author_id', types.Unicode, nullable=False, index=True),
                     )

unsubscription_table = Table('forum_unsubscribe_user', meta.metadata,
                             Column('id', types.Integer, primary_key=True, autoincrement=True),
                             Column('user_id', types.Unicode, nullable=False, index=True),
                             Column('thread_id', types.Integer,
                                    ForeignKey('forum_thread.id', onupdate='CASCADE', ondelete='CASCADE'),
                                    nullable=False, index=True),
                             )

migration_table = Table('forum_migrations', meta.metadata,
                        Column('id', types.Integer, primary_key=True, autoincrement=True),
                        Column('created', types.DateTime, default=datetime.utcnow),
                        )


class Board(object):
    """
    Forum board mapping class
    """

    def get_absolute_url(self):
        return tk.url_for('forum_board_show', slug=self.slug)

    @classmethod
    def get_by_name(cls, name):
        return Session.query(cls).filter(cls.name == name).first()

    @classmethod
    def get_by_slug(cls, slug):
        return Session.query(cls).filter(cls.slug == slug).first()

    def save(self, commit=True):
        if not hasattr(self, 'slug') or not self.slug:
            self.slug = slugify(self.name)
        session = Session()
        log.debug(self)
        session.add(self)
        if commit:
            session.commit()

    @classmethod
    def all(cls):
        query = Session.query(cls)
        if hasattr(cls, 'order_by') and isCallable(cls.order_by):
            query = cls.order_by(query)
        return query.all()

    @classmethod
    def filter_active(cls):
        return Session.query(cls).filter(cls.active == True)

    @classmethod
    def filter_can_post(cls):
        return Session.query(cls).filter(cls.active == True, cls.can_post == True)

    def hide(self):
        self.active = False
        session = Session()
        session.add(self)
        session.commit()

    def unhide(self):
        self.active = True
        session = Session()
        session.add(self)
        session.commit()


class Thread(object):
    """
    Forum thread mapping class
    """

    def get_absolute_url(self):
        return tk.url_for('forum_thread_show', slug=self.board.slug, id=self.id)

    @classmethod
    def get_by_id(cls, id):
        try:
            return Session.query(cls).filter(cls.id == int(id)).first()
        except ValueError:
            return None

    @classmethod
    def get_by_slug(cls, slug):
        return Session.query(cls).filter(cls.slug == slug).first()

    @classmethod
    def order_by(cls, query):
        return query.order_by(cls.created.desc())

    @classmethod
    def filter_board(cls, board_slug):
        return Session.query(cls).filter(cls.board.has(slug=board_slug), cls.active == True)

    def save(self, commit=True):
        session = Session()
        log.debug(self)
        session.add(self)
        if commit:
            session.commit()

    @classmethod
    def all(cls):
        query = Session.query(cls).filter(cls.active == True)
        if hasattr(cls, 'order_by') and isCallable(cls.order_by):
            query = cls.order_by(query)
        return query

    def ban(self):
        session = Session()
        session.query(self.__class__).filter(self.__class__.id == self.id).update({self.__class__.active: False})
        session.commit()


class Post(object):
    """
    Forum post mapping class
    """

    @classmethod
    def filter_thread(cls, thread_id):
        return Session.query(cls).filter(cls.thread_id == thread_id, cls.active == True)

    def get_absolute_url(self):
        return tk.url_for('forum_thread_show', slug=self.thread.board.slug, id=self.thread.id)

    def save(self, commit=True):
        session = Session()
        log.debug(self)
        session.add(self)
        if commit:
            session.commit()

    @classmethod
    def get_by_id(cls, id):
        return Session.query(cls).filter(cls.id == id).first()

    @classmethod
    def all(cls):
        query = Session.query(cls).filter(cls.active == True)
        if hasattr(cls, 'order_by') and isCallable(cls.order_by):
            query = cls.order_by(query)
        return query

    @classmethod
    def order_by(cls, session):
        return session.order_by(cls.created.desc())

    def ban(self):
        session = Session()
        session.query(self.__class__).filter(self.__class__.id == self.id).update({self.__class__.active: False})
        session.commit()


class BannedUser(object):

    def __init__(self, user_id):
        self.author_id = user_id

    @classmethod
    def get_banned_users(cls):
        session = Session()
        query = session.query(cls, model.User).join(User, cls.author_id == User.id).order_by(cls.id.desc())
        return query

    @classmethod
    def check_by_id(cls, user):
        session = Session()
        return session.query(session.query(cls).filter(cls.author_id == user.id).exists()).scalar()

    @classmethod
    def ban(cls, user_id):
        session = Session()
        banned_user = cls(user_id)
        if not session.query(cls).filter(cls.author_id == user_id).first():
            session.add(banned_user)
            session.commit()

    @classmethod
    def unban(cls, user_id):
        session = Session()
        session.query(cls).filter(cls.author_id == user_id).delete()
        session.commit()



class Unsubscription(object):

    def __init__(self, user_id, thread_id):
        self.user_id = user_id
        self.thread_id = thread_id

    @classmethod
    def filter_by_thread_id(cls, thread_id):
        session = Session()
        return session.query(cls).filter(cls.thread_id == thread_id)

    @classmethod
    def add(cls, user_id, thread_id):
        session = Session()
        unsubscr = cls(user_id, thread_id)
        session.add(unsubscr)
        session.commit()


meta.mapper(Board, board_table)

meta.mapper(Thread,
            thread_table,
            properties={
                'author': relation(User,
                                   backref=backref('forum_threads', cascade='all, delete-orphan', single_parent=True),
                                   primaryjoin=foreign(thread_table.c.author_id) == remote(User.id)
                                   ),
                'board': relation(Board,
                                  backref=backref('forum_threads', cascade='all, delete-orphan', single_parent=True),
                                  primaryjoin=foreign(thread_table.c.board_id) == remote(Board.id)
                                  )
            }
            )

meta.mapper(Post,
            post_table,
            properties={
                'author': relation(User,
                                   backref=backref('forum_posts', cascade='all, delete-orphan', single_parent=True),
                                   primaryjoin=foreign(post_table.c.author_id) == remote(User.id)
                                   ),
                'thread': relation(Thread,
                                   backref=backref('forum_posts', cascade='all, delete-orphan', single_parent=True),
                                   primaryjoin=foreign(post_table.c.thread_id) == remote(Thread.id))
            }
            )

meta.mapper(BannedUser,
            banned_table,
            properties={
                'author': relation(User,
                                   backref=backref('banned', cascade='all, delete-orphan', single_parent=True),
                                   primaryjoin=foreign(banned_table.c.author_id) == remote(User.id)
                                   )
            }
            )

meta.mapper(Unsubscription, unsubscription_table)

if __name__ == "__main__":
    init_db()
