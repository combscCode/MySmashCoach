from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SelectField, IntegerField
from passlib.hash import sha256_crypt
from functools import wraps
from flask_mysqldb import MySQL
import trainingAlgorithms

CHARACTER_LIST = [(0, "Any"), (1, "Fox"), (2, "Falco"), (3, "Marth"), (4, "Sheik"), (5, "Jigglypuff"),
(6, "Peach"), (7, "Ice Climbers"), (8, "Captain Falcon"), (9, "Pikachu"), (10, "Samus"), (11, "Dr. Mario"),
(12, "Yoshi"), (13, "Luigi"), (14, "Ganondorf"), (15, "Mario"), (16, "Young Link"), (17, "Donkey Kong"),
(18, "Link"), (19, "Mr. Game & Watch"), (20, "Roy"), (21, "Mewtwo"), (22, "Zelda"), (23, "Ness"), (24, "Pichu"), 
(25, "Bowser"), (26, "Kirby")]

PRIORITY_LIST = [(0, "Fundamental"), (1, "Maintain"), (2, "Learning")]

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


#Exercise Form Class
class ExercisePForm(Form):
	title = StringField('Title', [validators.Length(min = 1, max = 200)])
	description = TextAreaField('Description', [validators.Length(min = 0)])
	exercise_type = StringField('Exercise Type', [validators.Length(min = 1, max = 50)])
	main = SelectField('Character', choices=CHARACTER_LIST, coerce=int)
	opponent = SelectField('Opponent', choices=CHARACTER_LIST, coerce=int)
	priority = SelectField('Priority', choices=PRIORITY_LIST, coerce=int)

class ExerciseForm(Form):
	title = StringField('Title', [validators.Length(min = 1, max = 200)])
	description = TextAreaField('Description', [validators.Length(min = 0)])
	exercise_type = StringField('Exercise Type', [validators.Length(min = 1, max = 50)])
	main = SelectField('Character', choices=CHARACTER_LIST, coerce=int)
	opponent = SelectField('Opponent', choices=CHARACTER_LIST, coerce=int)

@app.route('/my_exercises')
@is_logged_in
def my_exercises():
	cur = mysql.connection.cursor()
	userID = session['id']
	sort = request.args.get('sort')
	if sort is None:
		requests = cur.execute("SELECT * FROM user_exercise INNER JOIN exercises ON user_exercise.exercise_id=exercises.id WHERE user_exercise.user_id=%s ORDER BY priority", [userID])
	else:
		requests = cur.execute("SELECT * FROM user_exercise INNER JOIN exercises ON user_exercise.exercise_id=exercises.id WHERE user_exercise.user_id=%s ORDER BY " + sort, (str(userID)))
	exercises = cur.fetchall()
	cur.close()
	if requests > 0:
		return render_template('my_exercises.html', exercises=exercises, CHARACTER_LIST=CHARACTER_LIST, PRIORITY_LIST=PRIORITY_LIST)
	else:
		msg = "No exercises found, start by adding an exercise!"
		return render_template('my_exercises.html', msg=msg)

@app.route('/create_exercise', methods=['GET', 'POST'])
@is_logged_in
def create_exercise():
	cur = mysql.connection.cursor()
	form = ExercisePForm(request.form)
	if(request.method == 'POST' and form.validate()):
		title = form.title.data
		description = form.description.data
		exercise_type = form.exercise_type.data
		main = form.main.data
		opponent = form.opponent.data
		priority = form.priority.data
		cur.execute("INSERT INTO exercises(title, author, exercise_type, description, main, opponent) VALUES(%s, %s, %s, %s, %s, %s)", (title, session['username'], exercise_type, description, main, opponent))
		mysql.connection.commit()
		result = cur.execute("SELECT id FROM exercises WHERE title=%s AND main=%s AND opponent=%s", (title, main, opponent))
		exercise_id = cur.fetchone()
		cur.execute("INSERT INTO user_exercise(user_id, exercise_id, priority) VALUES(%s, %s, %s)", (session['id'], exercise_id['id'], priority))
		mysql.connection.commit()
		cur.close()
		flash("Exercise added", 'success')
		return redirect(url_for('my_exercises'))

	cur.close()

	return render_template('create_exercise.html', form=form)

@app.route('/exercise/<string:id>')
def exercise(id):
	cur = mysql.connection.cursor()
	requests = cur.execute("SELECT * FROM exercises WHERE id = %s", [id])
	exercise = cur.fetchone()

	return render_template('exercise.html', exercise=exercise)

@app.route('/edit_exercise/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_exercise(id):

	#Create cursor
	cur = mysql.connection.cursor()

	#Get exericse
	result = cur.execute("SELECT * FROM exercises WHERE id = %s", [id])
	exercise = cur.fetchone()

	if(exercise['author'] != session['username']):
		cur.close()
		flash("Cannot edit exercise that you did not create", "danger")
		return redirect(url_for('my_exercises'))

	#Get form
	form = ExerciseForm(request.form)
	#Populate exercise form fields
	form.title.data = exercise['title']
	form.description.data = exercise['description']
	form.exercise_type.data = exercise['exercise_type']
	form.main.data = exercise['main']
	form.opponent.data = exercise['opponent']

	if(request.method == 'POST' and form.validate()):
		title = request.form['title']
		description = request.form['description']
		exercise_type = request.form['exercise_type']
		main = request.form['main']
		opponent = request.form['opponent']

		cur = mysql.connection.cursor()

		cur.execute("UPDATE exercises SET title=%s, description=%s, exercise_type=%s, main=%s, opponent=%s WHERE id = %s", (title, description, exercise_type, main, opponent, exercise['id']))

		mysql.connection.commit()

		cur.close()

		flash("Exercise Edited", "success")
		
		return redirect(url_for('training'))

	return render_template('edit_exercise.html', form=form)

@app.route('/delete_exercise/<string:id>', methods=['POST'])
@is_logged_in
def delete_exercise(id):
	cur = mysql.connection.cursor()
	result = cur.execute("SELECT * FROM exercises WHERE id = %s", [id])
	result = cur.fetchone()
	if result['author'] != session['username']:
		flash("You cannot delete exercises you didn't create", "danger")
		return redirect(url_for('my_articles'))
	result = cur.execute("DELETE FROM exercises WHERE id = %s", [id])
	result = cur.execute("DELETE FROM user_exercise WHERE exercise_id = %s", [id])
	mysql.connection.commit()
	cur.close()

	flash("Exercise deleted", 'success')
	return redirect(url_for('find_exercises'))

@app.route('/remove_exercise/<string:id>', methods=['POST'])
@is_logged_in
def remove_exercise(id):
	cur = mysql.connection.cursor()
	result = cur.execute("DELETE FROM user_exercise WHERE user_id = %s AND exercise_id = %s", (session['id'], id))
	mysql.connection.commit()
	cur.close()

	flash("Exercise removed", 'success')
	return redirect(url_for('my_exercises'))

@app.route('/find_exercises')
@is_logged_in
def find_exercises():
	cur = mysql.connection.cursor()
	sort = request.args.get('sort')
	if sort is None:
		requests = cur.execute("SELECT * FROM exercises")
		exercises = list(cur.fetchall())
		requests = cur.execute("SELECT * FROM user_exercise WHERE user_id = %s", [session["id"]])
	else:
		requests = cur.execute("SELECT * FROM exercises ORDER BY " + sort)
		exercises = list(cur.fetchall())
		requests = cur.execute("SELECT * FROM user_exercise WHERE user_id = %s", [session["id"]])
	my_exercises = cur.fetchall()
	my_ids = {}
	indexes = []
	for exercise in my_exercises:
		my_ids[exercise['exercise_id']] = 1
	for index, exercise in enumerate(exercises):
		if exercise['id'] in my_ids:
			indexes.append(index)
	for index in sorted(indexes, reverse=True):
		del exercises[index]
	cur.close()
	return render_template('find_exercises.html', exercises=tuple(exercises), CHARACTER_LIST=CHARACTER_LIST)

@app.route('/add_exercise/<string:id>', methods=['POST'])
@is_logged_in
def add_exercise(id):
	cur = mysql.connection.cursor()
	userID = session['id']
	result = cur.execute("INSERT INTO user_exercise (user_id, exercise_id, priority) VALUES (%s, %s, 1)", (userID, id))
	mysql.connection.commit()
	cur.close()
	flash("Exercise added", "success")
	return redirect(url_for('find_exercises'))

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
				session['id'] = data['id']

				flash('You are now logged in', 'success')
				return redirect(url_for('my_exercises'))
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

#Training Form Class
class TrainingForm(Form):
	time = IntegerField("Time", [validators.NumberRange(min = 15, max = 90)])
	main = SelectField('Main', choices=CHARACTER_LIST, coerce=int)
	opponent = SelectField('Opponent', choices=CHARACTER_LIST, coerce=int)

@app.route('/training')
@is_logged_in
def training():
	cur = mysql.connection.cursor()
	userID = session['id']
	requests = cur.execute("SELECT * FROM user_exercise INNER JOIN exercises ON user_exercise.exercise_id=exercises.id WHERE user_exercise.user_id=%s", [userID])
	exercises = cur.fetchall()
	request = cur.execute("SELECT * FROM train_settings WHERE id=%s", [session['id']])
	settings = cur.fetchone()

	updated_exercises = trainingAlgorithms.default_training_algorithm(exercises, settings)
	totalTime = 0
	for exercise in updated_exercises:
		totalTime += exercise['time']
	
	cur.close()
	if requests > 0:
		if totalTime < settings['time']:
			warning = "You need to add more exercises to have a complete training schedule!"
			return render_template('training.html', exercises=updated_exercises, CHARACTER_LIST=CHARACTER_LIST, PRIORITY_LIST=PRIORITY_LIST, warning=warning)
		return render_template('training.html', exercises=updated_exercises, CHARACTER_LIST=CHARACTER_LIST, PRIORITY_LIST=PRIORITY_LIST)
	else:
		msg = "No exercises found, start by adding an exercise!"
		return render_template('training.html', msg=msg)


@app.route('/training_settings', methods=['GET', 'POST'])
@is_logged_in
def training_settings():
	cur = mysql.connection.cursor()
	result = cur.execute("SELECT * FROM train_settings WHERE id = %s", [session['id']])
	if result < 1:
		cur.execute("INSERT INTO train_settings(id, time, main, opponent) VALUES (%s, 25, 0, 0)", [session['id']])
		mysql.connection.commit()
		result = cur.execute("SELECT * FROM train_settings WHERE id = %s", [session['id']])
	settings = cur.fetchone()
	form = TrainingForm(request.form)
	form.time.data = settings['time']
	form.main.data = settings['main']
	form.opponent.data = settings['opponent']

	if(request.method == 'POST' and form.validate()):
		cur = mysql.connection.cursor()
		timeSpent = request.form['time']
		main = request.form['main']
		opponent = request.form['opponent']
		cur.execute("UPDATE train_settings SET time=%s, main=%s, opponent=%s WHERE id = %s", (timeSpent, main, opponent, session['id']))
		mysql.connection.commit()

		cur.close()
		flash("Settings Updated", "success")
		return redirect(url_for('training'))

	return render_template('training_settings.html', form=form, CHARACTER_LIST=CHARACTER_LIST)

@app.route('/set_priority/<string:exercise_id>/<string:priority>', methods=['GET', 'POST'])
@is_logged_in
def edit_priorities(exercise_id, priority):
	cur = mysql.connection.cursor()
	user_id = session['id']
	cur.execute("UPDATE user_exercise SET priority=%s WHERE user_id=%s AND exercise_id=%s", (priority, user_id, exercise_id))
	mysql.connection.commit()
	cur.close()
	
	flash("Priority Updated", "success")
	return redirect(url_for('my_exercises'))

if __name__ == '__main__':
	app.secret_key='secret123'
	app.run(debug=True)

