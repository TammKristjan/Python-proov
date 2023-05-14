from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, BooleanField, FieldList, FormField
from wtforms.validators import DataRequired, Length, NumberRange


class SearchForm(FlaskForm):
    search_term = StringField('Search Term')


class ShareholderForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=3, max=100)])
    id = StringField('ID', validators=[DataRequired()])
    share_size = IntegerField('Share Size (in EUR)', validators=[DataRequired(), NumberRange(min=1)])


class CreateCompanyForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired(), Length(min=3, max=100)])
    registration_code = StringField('Registration Code', validators=[DataRequired()])
    founding_date = DateField('Founding Date', validators=[DataRequired()])
    total_capital = IntegerField('Total Capital (in EUR)', validators=[DataRequired(), NumberRange(min=2500)])
    shareholders = FieldList(FormField(ShareholderForm))
