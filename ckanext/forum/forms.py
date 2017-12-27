from wtforms import TextAreaField, StringField, validators, IntegerField
from wtforms import Form


class CreateThreadForm(Form):
    board_id = IntegerField(validators=[validators.InputRequired()])
    name = StringField(validators=[validators.InputRequired(), validators.Length(min=1)])
    content = TextAreaField(validators=[validators.InputRequired(), validators.Length(min=1)])


class CreatePostForm(Form):
    content = TextAreaField(validators=[validators.InputRequired(), validators.Length(min=1)])


class CreateBoardForm(Form):
    name = StringField(validators=[validators.InputRequired(), validators.Length(min=1)])
    slug = StringField(validators=[validators.InputRequired(),
                                   validators.Length(min=1),
                                   validators.Regexp('^[a-z0-9\-]*$')])
