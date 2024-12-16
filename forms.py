from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL


class CreateForm(FlaskForm):
    name = StringField("Product Name", validators=[DataRequired()])
    img_url = StringField("Image URL", validators=[DataRequired(), URL()])
    price = StringField("Price in USD", validators=[DataRequired(), ])
    submit = SubmitField("Submit Product")
