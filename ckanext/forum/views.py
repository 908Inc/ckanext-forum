from sqlalchemy.exc import SQLAlchemyError as sql_exc
import flask
from flask import Flask
from flask import Blueprint, redirect, render_template, url_for
from flask.ext.sqlalchemy import SQLAlchemy

import forms
import models

GET_POST = ['GET', 'POST']

bp = Blueprint('forum', __name__)
app = Flask(__name__)
db = SQLAlchemy(app)
models.init_db(db)


@bp.route('/forum')
def index():
    boards = models.Board.query.all()
    # TODO: remove this 'if' once admin page will be implemented
    # NOTE: create test board if DB is empty
    if not len(boards):
        board = models.Board()
        board.name = 'Test'
        board.slug = 'test'
        db.session.add(board)
        db.session.commit()
    return render_template('forum_index.html', boards=boards)


@bp.route('/<slug>/')
def board(slug):
    try:
        board = models.Board.query.filter(models.Board.slug == slug).one()
        threads = models.Thread.query.filter(models.Thread.board_id == board.id) \
                        .order_by(models.Thread.updated.desc()).all()
    except sql_exc:
        return redirect(url_for('.index'))

    return render_template('board.html', board=board,
                           threads=threads)


@bp.route('/<slug>/<int:id>')
@bp.route('/<slug>/<int:id>-<title>')
def thread(slug, id, title=None):
    try:
        board = models.Board.query.filter(models.Board.slug == slug).one()
    except sql_exc:
        return redirect(url_for('.index'))

    try:
        thread = models.Thread.query.filter(models.Thread.id == id).one()
    except sql_exc:
        return redirect(url_for('.board', slug=slug))

    return render_template('thread.html', board=board, thread=thread,
                           posts=thread.posts)


@bp.route('/<slug>/create/', methods=GET_POST)
def create_thread(slug):
    try:
        board = models.Board.query.filter(models.Board.slug == slug).one()
    except sql_exc:
        return redirect(url_for('.index'))

    form = forms.CreateThreadForm()
    if form.validate_on_submit():
        t = models.Thread(name=form.name.data,
                          board_id=board.id,
                          author_id=flask.g.userobj.id)
        db.session.add(t)
        db.session.flush()

        p = models.Post(content=form.content.data,
                        author_id=flask.g.userobj.id)
        t.posts.append(p)
        db.session.commit()

        return redirect(url_for('.board', slug=slug))

    return render_template('create_thread.html', board=board,
                           form=form)


@bp.route('/<slug>/<int:id>/create', methods=GET_POST)
def create_post(slug, id):
    try:
        board = models.Board.query.filter(models.Board.slug == slug).one()
    except sql_exc:
        return redirect(url_for('.index'))
    try:
        thread = models.Thread.query.filter(models.Thread.id == id).one()
    except sql_exc:
        return redirect(url_for('.board', slug=slug))

    form = forms.CreatePostForm()
    if form.validate_on_submit():
        p = models.Post(content=form.content.data,
                        author=flask.g.userobj.id)
        thread.posts.append(p)
        db.session.flush()
        thread.updated = p.created
        db.session.commit()

        return redirect(url_for('.thread', slug=slug, id=id))

    return render_template('create_post.html', board=board,
                           thread=thread, form=form)


@bp.route('/<slug>/<int:thread_id>/<int:post_id>/edit', methods=GET_POST)
def edit_post(slug, thread_id, post_id):
    try:
        board = models.Board.query.filter(models.Board.slug == slug).one()
    except sql_exc:
        return redirect(url_for('.index'))
    try:
        thread = models.Thread.query.filter(
            models.Thread.id == thread_id).one()
    except sql_exc:
        return redirect(url_for('.board', slug=slug))

    thread_redirect = redirect(url_for('.thread', slug=slug, id=thread_id))
    try:
        post = models.Post.query.filter(models.Post.id == post_id).one()
    except sql_exc:
        return thread_redirect
    if post.author_id != flask.g.userobj.id:
        return thread_redirect

    form = forms.EditPostForm()
    if form.validate_on_submit():
        post.content = form.content.data
        db.session.commit()
        return thread_redirect
    else:
        form.content.data = post.content

    return render_template('create_post.html', board=board,
                           thread=thread, form=form)
