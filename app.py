from flask import Flask, render_template, redirect, request, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange
import sqlite3
from flask import g


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'

DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def close_db(exception=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.before_request
def before_request():
    g.db = get_db()

@app.teardown_request
def teardown_request(exception=None):
    close_db(exception)

def create_tables():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            reg_code TEXT NOT NULL,
            founding_date DATE NOT NULL,
            capital INTEGER NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shareholders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            personalcode INTEGER NOT NULL,
            share INTEGER NOT NULL,
            founder INTEGER NOT NULL,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        )
    ''')
    db.commit()


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


# Andmebaasina kasutame siin lihtsat sõnastikku
companies = []

def search_companies(query):
    db = get_db()
    cursor = db.cursor()
    search_query = f"%{query}%"
    cursor.execute('''
        SELECT DISTINCT companies.id, companies.name, companies.reg_code 
        FROM companies 
        JOIN shareholders ON companies.id = shareholders.company_id 
        WHERE companies.name LIKE ? 
            OR companies.reg_code LIKE ? 
            OR shareholders.name LIKE ?
            OR shareholders.personalcode LIKE ?
    ''', (search_query, search_query, search_query, search_query))
    companies = cursor.fetchall()
    return companies

@app.route('/search')
def search():
    query = request.args.get('query', '')
    companies = search_companies(query)
    return render_template('search.html', companies=companies, query=query)



@app.route('/')
def home():
    return render_template('home.html', companies=companies)


@app.route('/company/<int:index>')
def view_company(index):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, name, reg_code, founding_date, capital FROM companies WHERE id = ?', (index,))
    company_data = cursor.fetchone()
    cursor.execute('SELECT name, personalcode, share, founder FROM shareholders WHERE company_id = ?', (index,))
    shareholders = cursor.fetchall()
    return render_template('company.html', company=company_data, shareholders=shareholders)



@app.route('/create_company', methods=['GET', 'POST'])
def create_company():
    form = CompanyForm()
    if form.validate_on_submit():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO companies (name, reg_code, founding_date, capital) VALUES (?, ?, ?, ?)', (
            form.name.data, form.reg_code.data, form.founding_date.data, form.capital.data
        ))
        company_id = cursor.lastrowid
        cursor.execute('INSERT INTO shareholders (company_id, name, personalcode, share, founder) VALUES (?, ?, ?, ?, ?)', (
            company_id, form.shareholder_name.data, form.shareholder_personalcode.data, form.shareholder_share.data, 1
        ))
        db.commit()
        return redirect(url_for('view_company', index=company_id))
    return render_template('create_company.html', form=form)



@app.route('/increase_capital/<int:company_id>', methods=['GET', 'POST'])
def increase_capital(company_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, name, reg_code, founding_date, capital FROM companies WHERE id = ?', (company_id,))
    company = cursor.fetchone()
    form = IncreaseCapitalForm()

    if form.validate_on_submit():
        # Värskenda olemasolevate osanike osakapitali
        existing_shareholder_shares = request.form.getlist('existing_shareholder_shares[]')
        existing_shareholder_ids = request.form.getlist('existing_shareholder_ids[]')

        for i in range(len(existing_shareholder_shares)):
            shareholder_id = existing_shareholder_ids[i]
            shareholder_share = existing_shareholder_shares[i]

            cursor.execute('UPDATE shareholders SET share = ? WHERE id = ?', (shareholder_share, shareholder_id))
            db.commit()

        # Lisa uus osanik andmebaasi, kui väljad on täidetud
        if form.shareholder_name.data and form.shareholder_share.data and form.shareholder_personalcode.data:
            cursor.execute('INSERT INTO shareholders (company_id, name, personalcode, share, founder) VALUES (?, ?, ?, ?, ?)', (
                company_id, form.shareholder_name.data, form.shareholder_personalcode.data, form.shareholder_share.data, 0
            ))
            db.commit()

        # Värskenda ettevõtte osakapitali
        cursor.execute('SELECT SUM(share) FROM shareholders WHERE company_id = ?', (company_id,))
        total_shares = cursor.fetchone()[0]
        cursor.execute('UPDATE companies SET capital = ? WHERE id = ?', (total_shares, company_id))
        db.commit()

        return redirect(url_for('view_company', index=company_id))

    # Hangi olemasolevate osanike andmed
    cursor.execute('SELECT id, name, personalcode, share FROM shareholders WHERE company_id = ?', (company_id,))
    shareholders = cursor.fetchall()

    return render_template('increase_capital.html', form=form, company=company, shareholders=shareholders)

if __name__ == '__main__':
    with app.app_context():
        create_tables()

    @app.teardown_appcontext
    def teardown_appcontext(exception=None):
        close_db(exception)

    app.run()
    
