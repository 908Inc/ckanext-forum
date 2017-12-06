from wtforms import SubmitField, TextAreaField, StringField, validators
from wtforms.validators import Required
from wtforms import Form


class CreateThreadForm(Form):
    name = StringField(validators=[validators.input_required()])
    content = TextAreaField(validators=[validators.input_required()])
    submit = SubmitField()


class CreatePostForm(Form):
    content = TextAreaField(validators=[Required()])
    submit = SubmitField()


class EditPostForm(CreatePostForm):
    pass
