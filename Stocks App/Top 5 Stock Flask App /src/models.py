from main import db
from main import login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


# creating a User ojbect as a SQLAlchemy object that will be translated into a table and columns
class User(UserMixin, db.Model):
	#__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), unique=True)
	email = db.Column(db.String(120), unique=True)
	password_hash = db.Column(db.String(128))
	
	# this function defines what will happen with we try and print the object
	def __repr__(self):
		return '<User {}>'.format(self.username)   

	# using the werkeug module to create a password hash from a password
	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	# cheking if teh hash matches a password (BOOL)
	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
	return User.query.get(int(id))