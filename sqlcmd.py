


def get_users_exercises(mysql, user_id):
	cur = mysql.connection.cursor()
	requests = cur.execute("SELECT * FROM user_exercise INNER JOIN exercises ON user_exercise.exercise_id=exercises.id WHERE user_exercise.user_id=%s ORDER BY priority", [user_id])
	exercises = cur.fetchall()
	cur.close()
	return exercises

	

