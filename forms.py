from flask_wtf import FlaskForm
from wtforms import StringField, DateField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange

class CompanyForm(FlaskForm):
    name = StringField('Nimi', validators=[DataRequired(), Length(min=3, max=100)])
    reg_code = StringField('Registrikood', validators=[DataRequired(), Length(min=7, max=7)])
    founding_date = DateField('Asutamiskuupäev', validators=[DataRequired()], format='%Y-%m-%d')
    capital = IntegerField('Kogukapital', validators=[DataRequired(), NumberRange(min=2500)])
    shareholder_name = StringField('Osaniku nimi', validators=[DataRequired(), Length(min=3, max=100)])
    shareholder_personalcode = IntegerField('Osaniku isikukood/registrikood', validators=[DataRequired(), NumberRange(min=1000000, max=99999999999)])
    shareholder_share = IntegerField('Osaniku osa', validators=[DataRequired(), NumberRange(min=1)])


class IncreaseCapitalForm(FlaskForm):
    shareholder_name = StringField('Osaniku nimi', validators=[DataRequired(), Length(min=3, max=100)])
    shareholder_personalcode = IntegerField('Osaniku isikukood/registrikood', validators=[DataRequired(), NumberRange(min=1000000, max=99999999999)])
    shareholder_share = IntegerField('Osaniku osa', validators=[DataRequired(), NumberRange(min=1)])