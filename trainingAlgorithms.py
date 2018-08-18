import random
import math

def default_pick_fundamentals(exercises, minTime, maxTime, totalTime):
	if len(exercises) == 0:
		return []
	random.shuffle(exercises)

	timeLeft = math.ceil(totalTime)
	minTime = math.ceil(minTime)
	maxTime = math.ceil(maxTime)
	#avgTime should be the time each exercise would take if we did each one within the allotted timeframe
	avgTime = math.ceil(timeLeft/len(exercises))

	#If there aren't enough exercises we need to increase the min and max time allotted for each exercise.
	#If the user doesn't like this, just add more exercises homie
	if avgTime > minTime:
		minTime = avgTime
	if minTime > maxTime:
		maxTime = minTime + 2


	fundamentals = []
	index = 0
	#For this loop if every exercise got the min time we should still fill up the total time allotted to us
	while timeLeft > 0 and index < len(exercises):
		timeSpent = random.randint(min(minTime, timeLeft), min(maxTime, timeLeft))
		exercises[index]['time'] = timeSpent
		fundamentals.append(exercises[index])
		timeLeft -= timeSpent
		index += 1
	if timeLeft > 0:
		fundamentals[0]['time'] += timeLeft
	return fundamentals


def right_character(exercise, settings):
	main = settings['main'] == 0 or settings['main'] == exercise['main'] or exercise['main'] == 0
	opponent = settings['opponent'] == 0 or settings['opponent'] == exercise['opponent'] or exercise['opponent'] == 0
	return main and opponent

def default_pick_exercises(exercises, minTime, maxTime, totalTime):
	if len(exercises) == 0:
		return []
	random.shuffle(exercises)

	timeLeft = math.ceil(totalTime)
	minTime = math.ceil(minTime)
	maxTime = math.ceil(maxTime)
	avgTime = math.ceil(timeLeft/len(exercises))

	#I expect minTime to be much higher than avgTime. If not, increase it.
	if avgTime > minTime:
		minTime = avgTime + 1
	if minTime > maxTime:
		maxTime = minTime + 2

	ret = []
	index = 0
	while timeLeft > 0 and index < len(exercises):
		timeSpent = random.randint(min(minTime, timeLeft), min(maxTime, timeLeft))
		exercises[index]['time'] = timeSpent
		ret.append(exercises[index])
		timeLeft -= timeSpent
		index += 1
	if timeLeft > 0:
		ret[0]['time'] += timeLeft
	return ret

def default_pick_learning(exercises, minTime, maxTime, totalTime):
	if len(exercises) == 0:
		return []
	random.shuffle(exercises)

	timeLeft = math.ceil(totalTime)
	minTime = math.ceil(minTime)
	maxTime = math.ceil(maxTime)
	avgTime = math.ceil(timeLeft/len(exercises))

	#I expect minTime to be much higher than avgTime. If not, increase it.
	if avgTime > minTime:
		minTime = avgTime + 1
	if minTime > maxTime:
		maxTime = minTime + 2

	ret = []
	index = 0
	while timeLeft > 0 and index < len(exercises):
		if minTime > timeLeft:
			break
		timeSpent = random.randint(minTime, min(maxTime, timeLeft))
		
		exercises[index]['time'] = timeSpent
		ret.append(exercises[index])
		timeLeft -= timeSpent
		index += 1
	if timeLeft > 0:
		ret[0]['time'] += timeLeft
	return ret

def default_training_algorithm(exercises, settings):
	"""
	How the algorithm generates the training exercises for you to practice.
	fundamental takes 1/3 of the time
	maintain/learn takes 2/3 of the time

	Individual fundamental exercise should just take like 1-3 minutes
	Individual maintain exercise should just take like 1-3 minutes
	Individual learn exercise should take anywhere from 5 - 20 minutes
	"""

	if len(exercises) == 0:
		return []
	time = settings['time']
	main = settings['main']
	opponent = settings['opponent']
	fundamentals = []
	maintain = []
	learning = []
	updatedExercises = []
	for exercise in exercises:
		if exercise['priority'] == 1 and right_character(exercise, settings):
			fundamentals.append(exercise)
		if exercise['priority'] == 2 and right_character(exercise, settings):
			maintain.append(exercise)
		if exercise['priority'] == 3 and right_character(exercise, settings):
			learning.append(exercise)

	timeLearning = random.randint(int(time/3), int(time/2))
	if time > 30:
		timeLearning = random.randint(int(time/2), int(time*2/3))
	timeFundamentals = random.randint(int(time/3), int(time/2))
	if time > 30:
		timeFundamentals = random.randint(int(time/4), int(time/3))
	timeMaintain = time - timeLearning - timeFundamentals

	print(timeFundamentals)
	print(timeMaintain)
	print(timeLearning)

	fundamentals = default_pick_fundamentals(fundamentals, 1, 3, timeFundamentals)
	maintain = default_pick_exercises(maintain, 1, 2, timeMaintain)
	learning = default_pick_learning(learning, max(timeLearning//3, 5), timeLearning, timeLearning)

	for exercise in fundamentals:
		updatedExercises.append(exercise)
	for exercise in maintain:
		updatedExercises.append(exercise)
	for exercise in learning:
		updatedExercises.append(exercise)

	return updatedExercises