# Iguana game

import random, sys, time, math, pygame
from pygame.locals import*

musicOn = True

FPS = 30 # frames per second to update the screen
WINWIDTH = 640 # width of the program's window
WINHEIGHT = 480 # height in pixels
HALF_WINWIDTH = int(WINWIDTH / 2)
HALF_WINHEIGHT = int(WINHEIGHT / 2)

GRASSCOLOR = (24, 255, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

DIFFICULTYINCREASETIME = 10 # how often to increase the difficulty in seconds

SCOREINCREASETIME = 1
SCOREINCREASEAMOUNT = 10

CAMERASLACK = 90 # how far from the center the iguana moves before moving the camera

MAXMOVERATE = 30 # movement speed of the player
MAXWIGGLETIME = .3 # maximum time of a player wiggle in seconds
MINWIGGLETIME = 0.05 # minimum time of a player wiggle in seconds
PLAYERSIZE = 100 # size of the player (width and height)
INVULNTIME = 2 # how long the player is invulnerable after being hit in seconds
GAMEOVERTIME = 4 # how long the "game over" text stays on the screen in seconds
MAXHEALTH = 3 # how much health the player starts with

NUMGRASS = 30 # number of grass objects in the active area
STARTINGNUMBIRDS = 5 # number of enemy birds to start in the active area

# chickens
CHICKENSIZE = 70 # width and height
CHICKENMINSPEED = 3
CHICKENMAXSPEED = 7
CHICKENDIRCHANGEFREQ = 5 # % chance of chicken direction change
CHICKENMINMOVECOUNT = 3 # minimum number of times the chicken moves before changing directions
CHICKENMAXMOVECOUNT = 6 # maximum number of times the chicken moves before changing directions
CHICKENMAXMOVETIME = .25 # the maximum length of time the chicken moves before pausing
CHICKENMINWAITTIME = 1 # the minimum amount of time the chicken waits before changing directions in seconds
CHICKENMAXWAITTIME = 3 # the maximum amount of time the chicken waits before changing directions in seconds

"""
Data structure keys

Keys used by all three data structures:
	'x' - the left edge coordinate of the object in the game world (not a pixel coordinate on the screen)
 	'y' - the top edge coordinate of the object in the game world (not a pixel coordinate on the screen)
	'rect' - the pygame.Rect object representing where on the screen the object is located.
Player data structure keys:
	'surface' - the pygame.Surface object that stores the image of the player which will be drawn to the screen.
	'step' - one of the sequence of image steps in the walking animation. Set to '1' or '2'.
	'movex' - how many pixels per frame the player moves horizontally.  A negative integer is moving to the left, a positive to the right.
	'movey' - how many pixels per frame the player moves horizontally.  A negative integer is moving up, a positive moving down.
	'size' - the width and height of the player in pixels. (The width & height are always the same.)
	'health' - an integer showing how many more times the player can be hit by a bird
Chicken data structure keys:
	'surface' - the pygame.Surface object that stores the image of the bird which will be drawn to the screen.
	'type' - which type of bird - chicken, pelican, or hawk
	'movex' - how many pixels per frame the bird moves horizontally. A negative integer is moving to the left, a positive to the right.
	'movey' - how many pixels per frame the bird moves vertically. A negative integer is moving up, a positive moving down.
	'width' - the width of the bird's image, in pixels
	'height' - the height of the bird's image, in pixels

Grass data structure keys:
'grassImage' - an integer that refers to the index of the pygame.Surface object in GRASSIMAGES used for this grass object
"""

def main():
	global FPSCLOCK, DISPLAYSURF, BASICFONT, IGUANAIMAGE, IGUANAIMAGE_FLIP, GRASSIMAGES, CHICKENIMAGE, CHICKENIMAGE_FLIP

	pygame.init()
	FPSCLOCK = pygame.time.Clock()
	DISPLAYSURF = pygame.display.set_mode((WINWIDTH, WINHEIGHT))
	pygame.display.set_caption('Iguana Game')
	BASICFONT = pygame.font.Font('freesansbold.ttf', 32)

	# load image files
	IGUANAIMAGE = pygame.image.load('iguana.png')
	IGUANAIMAGE_FLIP = pygame.transform.flip(IGUANAIMAGE, True, False)
	CHICKENIMAGE = pygame.image.load('chicken.png')
	CHICKENIMAGE_FLIP = pygame.transform.flip(CHICKENIMAGE, True, False)

	GRASSIMAGES = []
	for i in range(1, 5):
		GRASSIMAGES.append(pygame.image.load('grass%s.png' % i))

	while True:
		runGame()	

def runGame():
	# set up variables for the start of a new game
	invulnerableMode = False # if the player is invulnerable
	invulnerableStartTime = 0 # time the player became invulnerable
	gameOverMode = False # if the player has lost
	gameOverStartTime = 0 # time the player has lost
	playerScore = 0 # player's score

	# create the surfaces to hold game text
	gameOverSurf = BASICFONT.render('Game Over', True, WHITE)
	gameOverRect = gameOverSurf.get_rect()
	gameOverRect.center = (HALF_WINWIDTH, HALF_WINHEIGHT)

	# camerax and cameray are where the middle of the camera view is
	camerax = 0
	cameray = 0

	# the number of active birds
	numBirds = STARTINGNUMBIRDS

	grassObjs = [] # stores all the grass objects in the game
	chickenObjs = [] # stores all the enemy chicken objects in the game
	
	# stores the player object:
	playerObj = {'surface': pygame.transform.scale(IGUANAIMAGE, (PLAYERSIZE, PLAYERSIZE)),
		'wigglestate': 1, # the wiggle state of the player - 1 or 2
		'wiggletimestart': time.time(), # the starting time of the current wiggle state
		'size': PLAYERSIZE,
		'x': HALF_WINWIDTH,
		'y': HALF_WINHEIGHT,
		'movex': 0,
		'movey': 0,
		'health': MAXHEALTH}

	# start off with some random grass images on the screen
	for i in range(10):
		grassObjs.append(makeNewGrass(camerax, cameray))
		grassObjs[i]['x'] = random.randint(0, WINWIDTH)
		grassObjs[i]['y'] = random.randint(0, WINHEIGHT)

	numBirds = STARTINGNUMBIRDS

	# initialize time for score and difficulty increases
	scoreTime = time.time()
	difficultyTime = time.time()

	# play music
	if musicOn:
		pygame.mixer.music.load('music.mp3')
		pygame.mixer.music.play(-1)

	while True: # main game loop

		# check if we should turn off invulnerability
		if invulnerableMode and time.time() - invulnerableStartTime > INVULNTIME:
			invulnerableMode = False
		
		# move all chickens
		moveChickens(chickenObjs)

		# delete any objects that are far away
		deleteObjs(grassObjs, camerax, cameray)
		deleteObjs(chickenObjs, camerax, cameray)
	
		# add more grass and chickens if we don't have enough
		while len(grassObjs) < NUMGRASS:
			grassObjs.append(makeNewGrass(camerax, cameray))
		while len(chickenObjs) < numBirds:
			chickenObjs.append(makeNewChicken(camerax, cameray))

		# the player is always in the center of the screen		
		camerax = playerObj['x'] + int(playerObj['size']/2) - HALF_WINWIDTH
		cameray = playerObj['y'] + int(playerObj['size']/2) - HALF_WINHEIGHT

		# draw the green background
		DISPLAYSURF.fill(GRASSCOLOR)
		
		# draw all the grass objects on the screen
		for gObj in grassObjs:
			gRect = pygame.Rect((gObj['x'] - camerax,
				gObj['y'] - cameray,
				gObj['width'],
				gObj['height']))
			DISPLAYSURF.blit(GRASSIMAGES[gObj['grassImage']], gRect)

		# draw all tbe chickens
		for cObj in chickenObjs:
			cObj['rect'] = pygame.Rect((cObj['x'] - camerax,
				cObj['y'] - cameray,
				cObj['width'],
				cObj['height']))
			DISPLAYSURF.blit(cObj['surface'], cObj['rect'])

		# draw the player
		flashIsOn = round(time.time(), 1) * 10 % 2 == 1
		if not gameOverMode and not (invulnerableMode and flashIsOn):
			playerObj['rect'] = pygame.Rect((playerObj['x'] - camerax,
				playerObj['y'] - cameray,
				playerObj['size'],
				playerObj['size']))
			
			DISPLAYSURF.blit(playerObj['surface'], playerObj['rect'])

		# draw the health meter
		# NOTE: maybe this game doesn't need health - just one hit and game over
		drawHealthMeter(playerObj['health'])

		# write the score
		drawScore(playerScore)

		# get player inputs
		for event in pygame.event.get(): # event handling loop
			if event.type == QUIT:
				terminate()

		if not gameOverMode:
			# move the player
			movePlayer(playerObj)

			# add 10 points for every second the player is alive
			if time.time() - scoreTime > SCOREINCREASETIME:
				# increase the score
				playerScore += SCOREINCREASEAMOUNT
				scoreTime = time.time()

			# increase the game difficulty
			if time.time() - difficultyTime > DIFFICULTYINCREASETIME:
				# increase the difficulty
				# increase the number of birds
				numBirds += 1
				difficultyTime = time.time()


			# check if the player has collided with any chickens
			for i in range(len(chickenObjs) - 1, -1, -1):
				cObj = chickenObjs[i]
				if 'rect' in cObj and playerObj['rect'].colliderect(cObj['rect']):
					# a player/bird collision has occurred

					if not invulnerableMode:
						# player takes damage
						invulnerableMode = True
						invulnerableStartTime = time.time()
						playerObj['health'] -= 1
						if playerObj['health'] == 0:
							gameOverMode = True # turn on "game over mode"
							gameOverStartTime = time.time()
		else:
			# game is over, show the "game over" text
			DISPLAYSURF.blit(gameOverSurf, gameOverRect)
			if time.time() - gameOverStartTime > GAMEOVERTIME:
				return # end of current game

		pygame.display.update()
		FPSCLOCK.tick(FPS)

def movePlayer(playerObj):
	# the players moves in the direction of the mouse cursor
	# if the mouse cursor is farther away from the player, the player moves more
	mousex, mousey = pygame.mouse.get_pos()		
	playerObj['movex'] = int( ((mousex - HALF_WINWIDTH) / HALF_WINWIDTH) * MAXMOVERATE )
	playerObj['movey'] = int( ((mousey - HALF_WINHEIGHT) / HALF_WINHEIGHT) * MAXMOVERATE )
	playerObj['x'] += playerObj['movex']
	playerObj['y'] += playerObj['movey']

	# update wiggle state
	playerSpeed = math.sqrt( (playerObj['movex'] * playerObj['movex']) + (playerObj['movey'] * playerObj['movey']) )
	maxSpeed = math.sqrt( (MAXMOVERATE * MAXMOVERATE) * 2)
	wiggleTime = ( ((maxSpeed - playerSpeed) / maxSpeed) * (MAXWIGGLETIME - MINWIGGLETIME) ) + MINWIGGLETIME
	if time.time() - playerObj['wiggletimestart'] > wiggleTime:
		# change the wiggle state
		playerObj['wigglestate'] = 3 - playerObj['wigglestate']
		playerObj['wiggletimestart'] = time.time() # reset the wiggle time start
	
	# put the player surface in the correct wiggle state
	if playerObj['wigglestate'] == 1:
		playerObj['surface'] = pygame.transform.scale(IGUANAIMAGE, (PLAYERSIZE, PLAYERSIZE))
	else:
		playerObj['surface'] = pygame.transform.scale(IGUANAIMAGE_FLIP, (PLAYERSIZE, PLAYERSIZE))

	# give the player the correct rotation angle (direction the player is facing)
	if playerObj['movey'] == 0:
		playerAngle = math.copysign(90, -playerObj['movex'])
	else:
		playerAngle = -math.degrees(math.atan(playerObj['movex'] / -playerObj['movey']))
		if playerObj['movey'] > 0:
			playerAngle -= 180

	playerObj['surface'] = pygame.transform.rotate(playerObj['surface'], playerAngle)

def moveChickens(chickenObjs):
	# move all the chickens
	# chikens move like this:
	# move in one direction, pausing shortly 3 - 5 times
	# then stay idle for 3 - 5 seconds
	# then repeat
	for cObj in chickenObjs:
		if cObj['ismoving']:
			# the chicken is moving
			cObj['x'] += cObj['movex']
			cObj['y'] += cObj['movey']

			if time.time() - cObj['movestarttime'] > cObj['maxmovetime']:
				# time to pause
				cObj['ismoving'] = False
				cObj['ispaused'] = True
				cObj['pausestarttime'] = time.time() # start pause timer

		elif cObj['ispaused']:
			# the chicken is paused

			if time.time() - cObj['pausestarttime'] > cObj['maxpausetime']:
				# time to move again, if there are move counts left
				if cObj['movecount'] > 0:
					cObj['movecount'] -= 1 # decrement move count
					cObj['movestarttime'] = time.time() # start move timer
					cObj['ispaused'] = False
					cObj['ismoving'] = True
				else:
					# no move moves left - start waiting
					cObj['waitstarttime'] = time.time() # start wait timer
					cObj['maxwaittime'] = random.randint(CHICKENMINWAITTIME, CHICKENMAXWAITTIME)
					cObj['ispaused'] = False
					cObj['ismoving'] = False
		else:
			# the chicken is waiting
			if time.time() - cObj['waitstarttime'] > cObj['maxwaittime']:
				# waiting time is over - change direction
				cObj['movex'] = getChickenVelocity()
				cObj['movey'] = getChickenVelocity()

				if cObj['movex'] >= 0:
					cObj['surface'] = pygame.transform.scale(CHICKENIMAGE, (cObj['width'], cObj['height']))
				else:
					cObj['surface'] = pygame.transform.scale(CHICKENIMAGE_FLIP, (cObj['width'], cObj['height']))

				# reset move count
				cObj['movecount'] = random.randint(CHICKENMINMOVECOUNT, CHICKENMAXMOVECOUNT)
				cObj['movestarttime'] = time.time() # start move timer
				cObj['ismoving'] = True			

def deleteObjs(objs, camerax, cameray):
	# delete objects that are far away
	for i in range(len(objs) - 1, -1, -1):
		if isOutsideActiveArea(camerax, cameray, objs[i]):
			del objs[i]

def drawHealthMeter(currentHealth):
	for i in range(currentHealth): # draw red health bars
		pygame.draw.rect(DISPLAYSURF, RED, (15, 5 + (10 * MAXHEALTH) - i * 10, 20, 10))
	for i in range(MAXHEALTH): # draw the white outlines
		pygame.draw.rect(DISPLAYSURF, WHITE, (15, 5 + (10 * MAXHEALTH) - i * 10, 20, 10), 1)

def drawScore(playerScore):
	scoreSurf = BASICFONT.render(str(playerScore), True, WHITE)
	scoreRect = scoreSurf.get_rect()
	scoreRect.top = 10
	scoreRect.right = WINWIDTH - 10
	DISPLAYSURF.blit(scoreSurf, scoreRect)

def terminate():
	pygame.quit()
	sys.exit()

def getChickenVelocity():
	speed = random.randint(CHICKENMINSPEED, CHICKENMAXSPEED)
	if random.randint(0,1) == 0:
		return speed
	else:
		return -speed

def getRandomOffCameraPos(camerax, cameray, objWidth, objHeight):
	# create a Rect of the camera view
	cameraRect = pygame.Rect(camerax, cameray, WINWIDTH, WINHEIGHT)
	while True:
		x = random.randint(camerax - WINWIDTH, camerax + (2 * WINWIDTH))
		y = random.randint(cameray - HALF_WINHEIGHT, cameray + (2 * WINHEIGHT))
		# create a Rect object with the random coordinates and use colliderect()
		# to make sure the right edge isn't in the camera view
		objRect = pygame.Rect(x, y, objWidth, objHeight)
		if not objRect.colliderect(cameraRect):
			return x, y

def makeNewGrass(camerax, cameray):
	gr = {}
	gr['grassImage'] = random.randint(0, len(GRASSIMAGES) - 1)
	gr['width'] = GRASSIMAGES[0].get_width()
	gr['height'] = GRASSIMAGES[0].get_height()
	gr['x'], gr['y'] = getRandomOffCameraPos(camerax, cameray, gr['width'], gr['height'])
	gr['rect'] = pygame.Rect( (gr['x'], gr['y'], gr['width'], gr['height']) )
	return gr

def makeNewChicken(camerax, cameray):
	chicken = {}
	chicken['width'] = CHICKENSIZE
	chicken['height'] = CHICKENSIZE
	chicken['x'], chicken['y'] = getRandomOffCameraPos(camerax, cameray, chicken['width'], chicken['height'])
	chicken['movex'] = getChickenVelocity()
	chicken['movey'] = getChickenVelocity()

	if chicken['movex'] >= 0:
		chicken['surface'] = pygame.transform.scale(CHICKENIMAGE, (chicken['width'], chicken['height']))
	else:
		chicken['surface'] = pygame.transform.scale(CHICKENIMAGE_FLIP, (chicken['width'], chicken['height']))
	chicken['ismoving'] = True	
	chicken['movestarttime'] = time.time() # the time the chicken started moving
	chicken['maxmovetime'] = CHICKENMAXMOVETIME # how long the chicken should move before pausing in seconds
	chicken['ispaused'] = False # is the chicken paused? 
	chicken['pausestarttime'] = 0 # the time the chicken started pausing
	chicken['maxpausetime'] = chicken['maxmovetime'] # how long the chicken should pause before moving again in seconds - it's the same as maxmovetime
	chicken['movecount'] = random.randint(CHICKENMINMOVECOUNT, CHICKENMAXMOVECOUNT) # number of times remaining the chicken moves before changing direction
	chicken['waitstarttime'] = 0
	chicken['maxwaittime'] = 0
	
	return chicken

def isOutsideActiveArea(camerax, cameray, obj):
	# return False if camerax and cameray are more than
	# a half-window length beyond th edge of the window
	boundsLeftEdge = camerax - HALF_WINWIDTH
	boundsTopEdge = cameray - HALF_WINHEIGHT
	boundsRect = pygame.Rect(boundsLeftEdge, boundsTopEdge, WINWIDTH * 3, WINHEIGHT * 3)
	objRect = pygame.Rect(obj['x'], obj['y'], obj['width'], obj['height'])
	return not boundsRect.colliderect(objRect)

if __name__ == '__main__':
	main()