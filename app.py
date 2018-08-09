from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SelectField
from passlib.hash import sha256_crypt
from functools import wraps

CHARACTER_LIST = [(0, "Any"), (1, "Fox"), (2, "Falco"), (3, "Marth"), (4, "Sheik"), (5, "Jigglypuff"),
(6, "Peach"), (7, "Ice Climbers"), (8, "Captain Falcon"), (9, "Pikachu"), (10, "Samus"), (11, "Dr. Mario"),
(12, "Yoshi"), (13, "Luigi"), (14, "Ganondorf"), (15, "Mario"), (16, "Young Link"), (17, "Donkey Kong"),
(18, "Link"), (19, "Mr. Game & Watch"), (20, "Roy"), (21, "Mewtwo"), (22, "Zelda"), (23, "Ness"), (24, "Pichu"), 
(25, "Bowser"), (26, "Kirby")]

app = Flask(__name__)

#Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Meowmix1'
app.config['MYSQL_DB'] = 'myflaskapp'
#Acts like a dictionary! Gives things like tuple values
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
#init MySQL
mysql = MySQL(app)

#Check if user is logged in
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash("Unauthorized, please log in", 'danger')
			return redirect(url_for('login'))
	return wrap

@app.route('/')
def index():
	return redirect(url_for('home'))

@app.route('/home')
def home():
	return render_template('home.html')

@app.route('/about')
def about():
	return render_template('about.html')

#Skill Form Class
class SkillForm(Form):
	title = StringField('Title', [validators.Length(min = 1, max = 200)])
	description = TextAreaField('Description', [validators.Length(min = 0)])
	main = SelectField('Character', choices=CHARACTER_LIST, coerce=int)
	opponent = SelectField('Opponent', choices=CHARACTER_LIST, coerce=int)

@app.route('/skills')
@is_logged_in
def skills():
	cur = mysql.connection.cursor()
	requests = cur.execute("SELECT * FROM skills")
	skills = cur.fetchall()
	cur.close()
	if requests > 0:
		return render_template('skills.html', skills=skills, CHARACTER_LIST=CHARACTER_LIST)
	else:
		msg = "No skills found, start by adding a skill!"
		return render_template('skills.html', msg=msg)

@app.route('/add_skill', methods=['GET', 'POST'])
@is_logged_in
def add_skill():
	form = SkillForm(request.form)
	if(request.method == 'POST' and form.validate()):
		title = form.title.data
		body = form.description.data
		main = form.main.data
		opponent = form.opponent.data

		cur = mysql.connection.cursor()

		requests = cur.execute("SELECT * FROM skills WHERE title = %s AND main = %s", (title, main))
		if requests > 0:
			cur.close()
			flash("The skill '" + title + "'' is already in the database", 'danger')
			return redirect(url_for('skills'))

		cur.execute("INSERT INTO skills(title, description, main, opponent) VALUES(%s, %s, %s, %s)", (title, body, main, opponent))

		mysql.connection.commit()

		cur.close()

		flash("Skill added", "success")
		
		return redirect(url_for('dashboard'))

	return render_template('add_skill.html', form=form)

#Article Form Class
class ExerciseForm(Form):
	title = StringField('Title', [validators.Length(min = 1, max = 200)])
	description = TextAreaField('Description', [validators.Length(min = 0)])
	skillid = SelectField('Skill Practiced', choices=[], coerce=int)
	main = SelectField('Character', choices=CHARACTER_LIST, coerce=int)
	opponent = SelectField('Opponent', choices=CHARACTER_LIST, coerce=int)

@app.route('/exercises')
@is_logged_in
def exercises():
	cur = mysql.connection.cursor()
	requests = cur.execute("SELECT * FROM exercises")
	exercises = cur.fetchall()
	cur.close()
	if requests > 0:
		return render_template('exercises.html', exercises=exercises, CHARACTER_LIST=CHARACTER_LIST)
	else:
		msg = "No exercises found, start by adding an exercise!"
		return render_template('exercises.html', msg=msg)

@app.route('/add_exercise', methods=['GET', 'POST'])
@is_logged_in
def add_exercise():
	cur = mysql.connection.cursor()
	requests = cur.execute("SELECT id, title FROM skills")
	skills = cur.fetchall()
	choices = []
	for skill in skills:
		choices.append((skill['id'], skill['title']))
	form = ExerciseForm(request.form)
	form.skillid.choices = choices

	if(request.method == 'POST' and form.validate()):
		title = form.title.data
		description = form.description.data
		skillid = form.skillid.data
		main = form.main.data
		opponent = form.opponent.data
		cur.execute("INSERT INTO exercises(title, skillid, description, main, opponent) VALUES(%s, %s, %s, %s, %s)", (title, skillid, description, main, opponent))
		mysql.connection.commit()
		cur.close()
		flash("Exercise added", 'success')
		return redirect(url_for('exercises'))

	cur.close()

	return render_template('add_exercise.html', form=form)

	

@app.route('/article/<string:id>')
def article(id):
	cur = mysql.connection.cursor()
	requests = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
	article = cur.fetchone()


	return render_template('article.html', article=article)

#RegisterForm, wtform
class RegisterForm(Form):
	username = StringField('Username', [validators.Length(min = 3, max = 30)])
	password = PasswordField('Password', [
		validators.DataRequired(),
		validators.EqualTo('confirm', message = "Passwords do not match")
	])
	confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))

		#Create Cursor
		cur = mysql.connection.cursor()

		requests = cur.execute("SELECT * FROM users WHERE username = %s", [username])
		if requests > 0:
			cur.close()
			flash('Username already taken, please select another', 'danger')
			return redirect(url_for('register'))

		#Execute Query
		cur.execute("INSERT INTO users(username, password) VALUES(%s, %s)", (username, password))
		#commit to db
		mysql.connection.commit()

		#close connection
		cur.close()

		flash('You are now registered and can log in', 'success')
		return redirect(url_for('login'))
	return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password_candidate = request.form['password']

		cur = mysql.connection.cursor()
		result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

		if result > 0:
			data = cur.fetchone()
			password = data['password']
			cur.close()
			if sha256_crypt.verify(password_candidate, password):
				app.logger.info('PASSWORD MATCHED')
				session['logged_in'] = True
				session['username'] = username

				flash('You are now logged in', 'success')
				return redirect(url_for('dashboard'))
			else:
				error = 'Invalid login'
				app.logger.info('PASSWORD NOT MATCHED')
				return render_template('login.html', error=error)
			
		else:
			cur.close()
			error = 'Username not found'
			app.logger.info('NO USER')
			return render_template('login.html', error=error)
			

	return render_template('login.html')



@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('Successfully logged out', 'success')
	return redirect(url_for('index'))

@app.route('/dashboard')
@is_logged_in
def dashboard():

	cur = mysql.connection.cursor()

	result = cur.execute("SELECT * FROM skills")

	skills = cur.fetchall()

	cur.close()
	if result > 0:
		return render_template('dashboard.html', skills=skills, CHARACTER_LIST=CHARACTER_LIST)
	else:
		msg = 'No articles found'
		return render_template('dashboard.html', msg=msg)
	

#Article Form Class
class ArticleForm(Form):
	title = StringField('Title', [validators.Length(min = 1, max = 200)])
	body = TextAreaField('Body', [validators.Length(min = 30)])


@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
	form = ArticleForm(request.form)
	if(request.method == 'POST' and form.validate()):
		title = form.title.data
		body = form.body.data

		cur = mysql.connection.cursor()

		cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))

		mysql.connection.commit()

		cur.close()

		flash("Article added", "success")
		
		return redirect(url_for('dashboard'))

	return render_template('add_article.html', form=form)

@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):

	#Create cursor
	cur = mysql.connection.cursor()

	#Get article
	result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
	article = cur.fetchone()

	#Get form
	form = ArticleForm(request.form)
	#Populate article form fields
	form.title.data = article['title']
	form.body.data = article['body']

	if(request.method == 'POST' and form.validate()):
		title = request.form['title']
		body = request.form['body']

		cur = mysql.connection.cursor()

		cur.execute("UPDATE articles SET title=%s, body=%s WHERE id = %s", (title, body, article['id']))

		mysql.connection.commit()

		cur.close()

		flash("Article Updated", "success")
		
		return redirect(url_for('dashboard'))

	return render_template('edit_article.html', form=form)

@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
	cur = mysql.connection.cursor()
	cur.execute("SELECT * FROM articles WHERE id = %s", [id])
	article = cur.fetchone()

	if session['username'] != article['author']:
		flash("You do not have permission over that article", 'danger')
		cur.close()
		return redirect(url_for('dashboard'))

	result = cur.execute("DELETE FROM articles WHERE id = %s AND author = %s", (id, session['username']))
	mysql.connection.commit()
	cur.close()

	flash("Article deleted", 'success')
	return redirect(url_for('dashboard'))

if __name__ == '__main__':
	app.secret_key='secret123'
	app.run(debug=True)

