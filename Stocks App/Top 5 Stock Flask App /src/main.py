from flask import Flask, render_template, flash, redirect, request
import requests
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
import logging
from logging.handlers import SMTPHandler
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'
bootstrap = Bootstrap(app)

# import done after db is created becasue models imports db
from models import User
from login import LoginForm, RegistrationForm


#------------------------------------------------------------------------------------------------------------------#
#----------Start Flask App Logic-----------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------#


# allows me to create a flask shell session in the terminal without having to import each module (for testing)
@app.shell_context_processor
def make_shell_context():
	return {'db':db, 'User':User}

# Decorator used to tell Flask the URLs to create 
#render_template() creates the html template file it is passed at the specified URL
@app.route("/")
@app.route("/home")
def welcome():
	return render_template('BS_welcome.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/data')
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect('/login')
    return render_template('BS_register.html', form=form)




# Using the login.py module where a form object is created of type FlaskForm
@app.route("/login", methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect('/data')
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user is None or not user.check_password(form.password.data):
			flash('Invalid username or password')
			return redirect('/login')
		login_user(user, remember=form.remember_me.data)
		next_page = request.args.get('next')
		if not next_page or url_parse(next_page).netloc != '':
			next_page = '/data'
		return redirect(next_page)
	return render_template('BS_login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect("/home")



# Calling the API using requests module and return the data to the showdata.html template
@app.route("/data")
@login_required
def show_data():
    url = 'https://flask-api-dot-warm-airline-207713.appspot.com/list-top-5/stocks_data_NASDAQ'
    #http://127.0.0.1:8000
    response = requests.get(url)
    if response.ok:
        data = response.json()
    else:
        response.raise_for_status()

    # other column settings -> http://bootstrap-table.wenzhixin.net.cn/documentation/#column-options
    columns = [
    {
    "field": "symbol",
    "title": "Symbol",
    "sortable": True,
    },
    {
    "field": "company",
    "title": "Company",
    "sortable": True,
    },
    {
    "field": "change_percent", # which is the field's name of data key 
    "title": "Change_percent", # display as the table header's name
    "sortable": True,
    },
    {
    "field": "price",
    "title": "Price",
    "sortable": True,
    }
    ]

    return render_template('BS_showDataTable.html', data=data, columns=columns)



#------------------------------------------------------------------------------------------------------------------#
#------------------Error Handeling---------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------#

@app.errorhandler(404)
def not_found_error(error):
	return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
	db.session.rollback()
	return render_template('500.html'), 500


# add email on error functionality 
'''
if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='Microblog Failure',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

'''



if __name__ == "__main__":
    app.run(port='5000', debug=True)