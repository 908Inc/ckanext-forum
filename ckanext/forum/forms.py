from wtforms import TextAreaField, StringField, validators, IntegerField
from wtforms import Form


class CreateThreadForm(Form):
    board_id = IntegerField(validators=[validators.input_required()])
    name = StringField(validators=[validators.input_required()])
    content = TextAreaField(validators=[validators.input_required()])


class CreatePostForm(Form):
    content = TextAreaField(validators=[validators.input_required()])
