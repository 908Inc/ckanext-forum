from wtforms import TextAreaField, StringField, validators, IntegerField
from wtforms import Form


class CreateThreadForm(Form):
    board_id = IntegerField(validators=[validators.InputRequired()])
    name = StringField(validators=[validators.InputRequired(), validators.Length(min=3)])
    content = TextAreaField(validators=[validators.InputRequired(), validators.Length(min=10)])


class CreatePostForm(Form):
    content = TextAreaField(validators=[validators.InputRequired(), validators.Length(min=10)])


class CreateBoardForm(Form):
    name = StringField(validators=[validators.InputRequired(), validators.Length(min=3)])
    slug = StringField(validators=[validators.InputRequired(),
                                   validators.Length(min=3),
                                   validators.Regexp('^[a-z0-9\-]*$')])
