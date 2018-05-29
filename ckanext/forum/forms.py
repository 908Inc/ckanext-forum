import re
from wtforms import TextAreaField, StringField, validators, IntegerField
from wtforms import Form

from ckanext.forum.models import Board
from ckan.plugins import toolkit as tk


class CreateThreadForm(Form):
    min_length = 10
    board_id = IntegerField(validators=[validators.InputRequired()])
    name = StringField(validators=[validators.InputRequired()])
    content = TextAreaField(validators=[validators.InputRequired()])

    def validate_name(self, field):
        if len(field.data) < self.min_length:
            msg = tk._('Field must be at least %d characters long')
            raise validators.ValidationError(msg % self.min_length)


    def validate_content(self, field):
        if len(field.data) < self.min_length:
            msg = tk._('Field must be at least %d characters long')
            raise validators.ValidationError(msg % self.min_length)


class CreatePostForm(Form):
    content = TextAreaField(validators=[validators.InputRequired()])


class CreateBoardForm(Form):
    min_length = 5
    name = StringField(validators=[validators.InputRequired()])
    slug = StringField(validators=[validators.InputRequired(),
                                   validators.Length(min=1)])
    def validate_name(self, field):
        if len(field.data) < self.min_length:
            msg = tk._('Field must be at least %d characters long')
            raise validators.ValidationError(msg % self.min_length)
        if Board.get_by_name(field.data):
            raise validators.ValidationError(tk._('Bord with this name already exists'))


    def validate_slug(self, field):
        if len(field.data) < self.min_length:
            msg = tk._('Field must be at least %d characters long')
            raise validators.ValidationError(msg % self.min_length)
        if not re.match('^[a-z0-9\-]*$', field.data):
            raise validators.ValidationError(tk._('Invalid input'))
        if Board.get_by_slug(field.data):
            raise validators.ValidationError(tk._('Bord with this slug already exists'))

