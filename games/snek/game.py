import numpy as np
import copy
import logging
import random

MAX_HEALTH = 10
SIZE_FOOD_LAYER = 1
games_explored = 0

def xyToBoard(xy, w, h, layer):
	return xy[0] + xy[1] * h + w * h * layer


def gen_random_unoccupied_spaces_size_n(n, x, y):
	starting_pos = []
	for i in range(n):
		while True:
			pos = (random.randint(0,x - 1), random.randint(0,y - 1))
			if pos not in starting_pos:
				starting_pos.append(pos)
				break
	return starting_pos

class Game:

	def __init__(self, grid_shape=(7,7), num_players=2):

		self.currentPlayer = 0
		
		self.grid_shape = grid_shape
		self.w = grid_shape[0]
		self.h = grid_shape[1]
		self.num_players = num_players
		self.pieces = {'1':'X', '0': '-', '-1':'O'}

		self.actionSpace = np.array([0,0,0,0], dtype=np.int)

		# TODO: Set number of food to start with
		init_num_food = self.w

		self.food_layer = self.num_players + SIZE_FOOD_LAYER - 1 # 0 indexing
		self.player_layer = 0

		self.num_layers = self.num_players + SIZE_FOOD_LAYER
		self.input_shape = (self.num_layers, self.w, self.h)

		self.name = 'snek'


		# Generate snake starting positions
		starting_pos = gen_random_unoccupied_spaces_size_n(self.num_players, self.w, self.h)

		# Assign starting positions to snakes
		self.snakes = [[p] for p in starting_pos]
		self.board = np.array( [0] * self.grid_shape[0] * self.grid_shape[1] * self.num_layers, dtype=np.int)

		# Draw snakes on board
		for i, snake in enumerate(self.snakes):
			for xy in snake:
				self.board[xy[0] + xy[1] * self.h + self.w * self.h * i] = 1


		# Generate food starting positions
		starting_food = gen_random_unoccupied_spaces_size_n(init_num_food, self.w, self.h)

		# Draw snakes on board
		for xy in starting_food:
			self.board[xy[0] + xy[1] * self.h + self.w * self.h * self.food_layer] = 1

		# Set Initial food
		self.turnNumber = [0] * self.num_players
		self.health = [MAX_HEALTH] * self.num_players


		self.gameState = GameState(self.board, self.grid_shape, self.snakes, 0, self.turnNumber, self.health)

		self.state_size = len(self.gameState.binary)
		self.action_size = len(self.actionSpace)



	def reset(self):
		self.gameState = GameState(self.board, self.grid_shape, self.snakes, 0, self.turnNumber, self.health)
		
		self.currentPlayer = 0
		return self.gameState

	def step(self, action):
		next_state, value, done = self.gameState.takeAction(action)
		self.gameState = next_state
		self.currentPlayer = -self.currentPlayer
		info = None
		return ((next_state, value, done, info))

	def identities(self, state, actionValues):
		identities = [(state,actionValues)]

		# TODO, should be 8 identities. Flip (x2), rotate (x4)
		currentBoard = state.board
		currentAV = actionValues

		return identities


class GameState(): # TODO: Condense inputs
	def __init__(self, board, grid_shape, snakes, playerTurn, turnNumber, health):
		self.board = board
		self.snakes = snakes
		self.num_players = len(snakes)
		self.num_snakes = len(snakes)
		self.grid_shape = grid_shape
		self.w = grid_shape[0]
		self.h = grid_shape[1]
		self.turnNumber = turnNumber

		global games_explored
		games_explored += 1
		if games_explored % 100 == 0:
			print("games_explored = %s" % games_explored, end="\r")

		self.health = health


		# Docs - More const section
		self.food_layer = self.num_players + SIZE_FOOD_LAYER - 1 # 0 indexing
		self.pieces = {'1':'X', '0': '-', '-1':'O'}

		self.direction_map_x = {
			'up' : 0, 'down' : 0, 'left' : -1,'right' : 1
		}

		self.direction_map_y = {
			'up' : -1, 'down' : 1, 'left' : 0, 'right' : 0
		}

		self.possibleActions = ['up','down','left','right']


		# Eval Section
		self.winners = []
		self.playerTurnInternal = playerTurn
		self.playerTurn = 1 if playerTurn == 0 else -1
		self.binary = self._binary()
		self.id = self._convertStateToId()
		self.allowedActions = self._allowedActions()
		self.isEndGame = self._checkForEndGame()
		self.value = self._getValue()
		self.score = self._getScore()

		if (self.playerTurnInternal == 0 and
			 turnNumber[self.playerTurnInternal] % 10 == 0):
				# Add food
				new_food = gen_random_unoccupied_spaces_size_n(1, self.w, self.h)[0]
				self.board[xyToBoard(new_food, self.w, self.h, self.food_layer)] = 1


	def _get_current_location(self):
		return self.snakes[self.playerTurnInternal][0]


	def _in_board(self, xy):
		
		BOARD_HEIGHT = self.h
		BOARD_WIDTH = self.w
		if xy[0] >= BOARD_WIDTH or xy[0] < 0:
				return False
		elif xy[1] >= BOARD_HEIGHT or xy[1] < 0:
				return False
			 
		return True

	def _get_action_xy(self, action):

		xy = self._get_current_location()
		next_xy = (xy[0] + self.direction_map_x[action],
							 xy[1] + self.direction_map_y[action])

		return next_xy

	def _is_valid_action(self, action):

		current_xy = self._get_current_location()
		
		# Check if the action moves you off the board
		new_xy = self._get_action_xy(action)

		if not self._in_board(new_xy):
			return False

		# Check if you will hit another snake
		snake_bodies = []

		snakes = self.snakes

		snakes_bodies = ( snake_xy for snake in snakes for snake_xy in snake )

		# TODO : Remove tails of snakes longer than 3
		# TODO : Remove heads of already moved snakes which are smaller
		# TODO : Add heads of not yet moved snakes which are equal/larger

		if new_xy in snakes_bodies:
			# print('Theres a snake in this boot')
			return False


		return True

	def _allowedActions(self):
		allowed = []

		for i, action in enumerate(self.possibleActions):
			if self._is_valid_action(action):
				allowed.append(i)
				
		return allowed

	def _binary(self):

		return (self.board)

	def _convertStateToId(self):

		id = ''.join(map(str,self.board))

		return id

	def _checkForEndGame(self):
		if not self.allowedActions:
			return 1

		if self.health[self.playerTurnInternal] <= 0:
			return 1

		return 0


	def _getValue(self):
		# This is the value of the state for the current player
		# i.e. if you have no more moves, you lose
		if self.isEndGame:
			return (-1,-1,-1)

		v = 0 # len(self.snakes[self.playerTurnInternal])

		return (v, v, v)


	def _getScore(self):
		tmp = self.value
		return (tmp[1], tmp[2])

	def _hasFood(self, xy):
		return self._xyToBoard(xy, self.food_layer) == 1


	def _xyToBoard(self, xy, layer):
		return xyToBoard(xy, self.w, self.h, layer)

	def _nextPlayer(self):
		return (self.playerTurnInternal  + 1) % self.num_players


	def takeAction(self, action):


		new_xy = self._get_action_xy(self.possibleActions[action])

		snake = copy.deepcopy(self.snakes[self.playerTurnInternal])

		newBoard = np.array(self.board)

		hasFood = self._hasFood(new_xy)
		newBoard[self._xyToBoard(new_xy, self.food_layer)] = 0

		# Remove tail if at least 3 long
		if len(snake) >= 3 and not hasFood:
			newBoard[ self._xyToBoard(snake[-1], self.playerTurnInternal) ] = 0
			snake = snake[:-1]

		# Add head
		newBoard[self._xyToBoard(new_xy, self.playerTurnInternal)] = 1
		snake = [new_xy] + snake

		snakes = copy.deepcopy(self.snakes)
		snakes[self.playerTurnInternal] = snake


		# Update Turn number
		turnNumber = copy.deepcopy(self.turnNumber)
		turnNumber[self.playerTurnInternal] += 1

		# Update Health
		health = copy.deepcopy(self.health)
		health[self.playerTurnInternal] -= 1
		if hasFood:
			health[self.playerTurnInternal] = MAX_HEALTH




		newState = GameState(newBoard, self.grid_shape, snakes, self._nextPlayer(), turnNumber, health)

		value = 0
		done = 0

		if newState.isEndGame:
			value = newState.value[0]
			done = 1

		return (newState, value, done)




	def render(self, logger):
		logger.info('--------------')