from wtforms import SubmitField, TextAreaField, StringField, validators, IntegerField
from wtforms.validators import Required
from wtforms import Form


class CreateThreadForm(Form):
    board_id = IntegerField(validators=[validators.input_required()])
    name = StringField(validators=[validators.input_required()])
    content = TextAreaField(validators=[validators.input_required()])


class CreatePostForm(Form):
    content = TextAreaField(validators=[Required()])
    submit = SubmitField()


class EditPostForm(CreatePostForm):
    pass
