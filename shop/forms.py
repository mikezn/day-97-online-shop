from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, DecimalField, TextAreaField, SelectField, BooleanField, IntegerField
from wtforms.validators import DataRequired, URL, Email, NumberRange, Length


# WTForms
class CreateProductForm(FlaskForm):
    name = StringField("Product Name", validators=[DataRequired(), Length(max=100)])
    description = TextAreaField("Description", validators=[DataRequired()])
    price = DecimalField("Price", places=2, rounding=None, validators=[
        DataRequired(),
        NumberRange(min=0, message="Price must be non-negative")
    ])
    img_url = StringField("Product Image URL", validators=[DataRequired(), URL()])
    submit = SubmitField("Save Product")


class CreateUserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=100)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    role_id = SelectField("Role", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Save User")


class CreateRoleForm(FlaskForm):
    is_admin = BooleanField("Admin", validators=[DataRequired()])
    role = StringField("Role", validators=[DataRequired(), Length(max=100)])
    submit = SubmitField("Save Role")


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


class CartForm(FlaskForm):
    product_name = name = StringField("Product Name", validators=[DataRequired(), Length(max=100)])
    quantity = IntegerField("Quantity", validators=[DataRequired()])
    total = DecimalField("Total", places=2, rounding=None, validators=[
        DataRequired(),
        NumberRange(min=0, message="Price must be non-negative")
    ])
    submit = SubmitField("Checkout")