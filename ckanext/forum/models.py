from datetime import datetime

from flask.ext.security import RoleMixin
from sqlalchemy import event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.orderinglist import ordering_list


from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

Base = None
TimestampMixin = None
UserRoleAssoc = None
Role = None
Board = None
Thread = None
Post = None


def init_db(db):
    class _Base(db.Model):

        """A base class that automatically creates the table name and
        primary key.
        """

        __abstract__ = True
        id = db.Column(db.Integer, primary_key=True)

        @declared_attr
        def __tablename__(cls):
            return cls.__name__.lower()

    global Base
    Base = _Base

    # TODO: use _TimestampMixin in rest of models
    class _TimestampMixin(object):
        created = db.Column(db.DateTime, default=datetime.utcnow)
        updated = db.Column(db.DateTime, default=datetime.utcnow)

        def readable_date(self, date, format='%H:%M on %-d %B'):
            """Format the given date using the given format."""
            return date.strftime(format)

    global TimestampMixin
    TimestampMixin = _TimestampMixin

    # Authentication
    # ~~~~~~~~~~~~~~
    class _UserRoleAssoc(db.Model):

        """Associates a user with a role."""

        __tablename__ = 'user_role_assoc'
        user_id = db.Column(db.String, primary_key=True)
        role_id = db.Column(db.Integer, primary_key=True)

    global UserRoleAssoc
    UserRoleAssoc = _UserRoleAssoc

    class _Role(Base, RoleMixin):

        """
        A specific role. `RoleMixin` provides the following methods:

            `__eq__(self, other)`
                Returns ``True`` if the `name` attributes are the same. If
                `other` is a string, returns `self.name == other`.

            `__ne__(self, other)`
        """

        name = db.Column(db.String)
        description = db.Column(db.String)

        def __repr__(self):
            return '<Role(%s, %s)>' % (self.id, self.name)

    global Role
    Role = _Role

    # Forum
    # ~~~~~
    class _Board(Base):

        #: The human-readable name, e.g. "Python 3"
        name = db.Column(db.String)

        #: The URL-encoded name, e.g. "python-3"
        slug = db.Column(db.String, unique=True)

        #: A short description of what the board contains.
        description = db.Column(db.Text)

        #: The threads associated with this board.
        threads = db.relationship('_Thread', cascade='all,delete', backref='_board')

        def __unicode__(self):
            return self.name

    global Board
    Board = _Board

    class _Thread(Base, TimestampMixin):
        name = db.Column(db.String(80))

        #: The original author of the thread.
        author_id = db.Column(db.String(), index=True)

        #: The parent board.
        board_id = db.Column(db.ForeignKey('_board.id'), index=True)

        #: An ordered collection of posts
        posts = db.relationship('_Post', backref='_thread',
                                cascade='all,delete',
                                order_by='_Post.index',
                                collection_class=ordering_list('index'))

        #: Length of the threads
        length = db.Column(db.Integer, default=0)

        def __unicode__(self):
            return self.name

    global Thread
    Thread = _Thread

    class _Post(Base, TimestampMixin):
        #: Used to order the post within its :class:`Thread`
        index = db.Column(db.Integer, default=0, index=True)

        #: The post content. The site views expect Markdown by default, but
        #: you can store anything here.
        content = db.Column(db.Text)

        #: The original author of the post.
        author_id = db.Column(db.String(), index=True)

        #: The parent thread.
        thread_id = db.Column(db.Integer, index=True)

        #: The parent thread.
        thread_id = db.Column(db.ForeignKey('_thread.id'), index=True)

        def __repr__(self):
            return '<Post(%s)>' % self.id

    global Post
    Post = _Post

    def thread_posts_append(thread, post, initiator):
        """Update some thread values when `Thread.posts.append` is called."""
        thread.length += 1
        thread.updated = datetime.utcnow()

# TODO: use this trigger or .count() funciton
# event.listen(Thread.posts, 'append', thread_posts_append)
