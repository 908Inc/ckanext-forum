from wtforms import TextAreaField, StringField, validators, IntegerField
from wtforms import Form


class CreateThreadForm(Form):
    board_id = IntegerField(validators=[validators.input_required()])
    name = StringField(validators=[validators.input_required(), validators.length(min=3)])
    content = TextAreaField(validators=[validators.input_required(), validators.length(min=10)])


class CreatePostForm(Form):
    content = TextAreaField(validators=[validators.input_required(), validators.length(min=10)])
