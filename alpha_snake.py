import numpy as np
import random

import loggers as lg

from game import Game, GameState
from model import Residual_CNN

from agent import Agent, User

import config

from snake_keys import *



def xyToBoard(xy, w, h, layer):
    return xy[0] + xy[1] * h + w * h * layer



class Battlesnake():
  def __init__(self):
    self.w = 0
    self.h = 0
    self.grid_shape = None
    self.num_players = 0
    self.food_layer = 0
    self.other_layer = 0
    self.num_layers = 0


    # Set AI Constants
    self.logger = lg.logger_main
    self.turns_until_tau0 = 10
    self.goes_first = 0

    self.run_version = 1
    self.playerversion = 6
    self.player = None


  def start(self, data):

    # Generate Game from initial json
    board_json = data[BOARD_KEY]

    # Find grid shape
    self.grid_shape=(board_json[WIDTH_KEY],
                board_json[HEIGHT_KEY])

    self.w, self.h = self.grid_shape

    # Find the snake positions.
    snakes = board_json[SNAKES_KEY]

    # Find your position
    your_id = data[YOU_KEY][ID_KEY]

    starting_pos_json = []
    for snake in snakes:
      if snake[ID_KEY] == your_id:
        starting_pos_json = [snake[BODY_KEY][0]] + starting_pos_json
      else:
        starting_pos_json = starting_pos_json + [snake[BODY_KEY][0]]

    starting_pos = []
    for pos_json in starting_pos_json:
      starting_pos += [(pos_json['x'], pos_json['y'])]

    self.num_players = len(snakes) + 1

    # Food layer immediately after players
    self.food_layer = self.num_players * 2

    # Other Layer immediately after food
    self.other_layer = self.food_layer + 1

    # Total layers
    self.num_layers = self.other_layer + 1

    # Find the food positions.
    foods = board_json[FOOD_KEY]
    starting_food = []
    for pos_json in foods:
      starting_food += (pos_json['x'], pos_json['y'])

    print("Creating new Game")
    # Create Game
    env = Game(self.grid_shape, self.num_players, starting_pos, starting_food)

    print("Creating new Agent")
    # Create Agent
    player_NN = Residual_CNN(config.REG_CONST, config.LEARNING_RATE, env.input_shape, env.action_size, config.HIDDEN_CNN_LAYERS)
    player_network = player_NN.read(env.name, self.run_version, self.playerversion)
    player_NN.model.set_weights(player_network.get_weights())   
    # self.player = Agent('player', env.state_size, env.action_size, config.MCTS_SIMS, config.CPUCT, player_NN)
    self.player = Agent('player', env.state_size, env.action_size, 50, config.CPUCT, player_NN)


  def act(self, json):
    state = self.gamestate_from_json(json)
    tau = 1 if json[TURN_KEY] < self.turns_until_tau0 else 0
    return self.player.act(state, tau)


  def create_board(self, snakes, food, turns, health):
    board = np.array( [0] * self.w * self.h * self.num_layers, dtype=np.int)
    print(snakes)
    print(food)
    print(turns)
    print(health)
    # Draw snakes on board
    for i, snake in enumerate(snakes):
      for j, xy in enumerate(snake):
        if j == 0: # Draw heads in the head layer
          board[xyToBoard(xy, self.w, self.h, i * 2)] = 1
        else: # Draw body in the body layer
          board[xyToBoard(xy, self.w, self.h, i * 2 + 1)] = 1

    # Draw food on board
    for xy in food:
      board[xyToBoard(xy, self.w, self.h, self.food_layer)] = 1


    # Add them to the board
    for i, turn in enumerate(turns):
      xy = (i, 0)
      board[xyToBoard(xy, self.w, self.h, self.other_layer)] = turn

    for i, health in enumerate(health):
      xy = (i, 1)
      board[xyToBoard(xy, self.w, self.h, self.other_layer)] = health

    return board

  def gamestate_from_json(self, json):

    # Generate Game from initial json
    board_json = json[BOARD_KEY]

    # Find grid shape
    grid_shape=(board_json[WIDTH_KEY],
                board_json[HEIGHT_KEY])

    # Find your position
    your_id = json[YOU_KEY][ID_KEY]

    # Find the snake positions.
    snakes = []
    snakes_json = board_json[SNAKES_KEY]
    health = []
    for snake_json in snakes_json:
      if snake_json[ID_KEY] == your_id:
        snakes = [[(xy['x'], xy['y']) for xy in snake_json[BODY_KEY]]] + snakes
        health = [snake_json[HEALTH_KEY]] + health
      else:
        snakes += [[(xy['x'], xy['y']) for xy in snake_json[BODY_KEY]]]
        health += [snake_json[HEALTH_KEY]]

    # Find the food positions.
    foods_json = board_json[FOOD_KEY]
    foods = []
    for pos_json in foods_json:
      foods += [(pos_json['x'], pos_json['y'])]

    turn = json[TURN_KEY]
    turns = [turn] * self.num_players

    board = self.create_board(snakes, foods, turns, health)

    return GameState(board, self.grid_shape, snakes, 0, turns, health)
