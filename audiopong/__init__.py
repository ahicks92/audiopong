from __future__ import division
import pyglet
import libaudioverse
from . import game_board

class MainScreen(object):

	def __init__(self, simulation):
		self.board=game_board.GameBoard()
		pyglet.clock.schedule_interval(self.tick, 1/60.0)
		#Todo: this should really, really, really use files.
		self.simulation = simulation
		self.noise = libaudioverse.NoiseNode(self.simulation)
		self.filtered_noise = libaudioverse.BiquadNode(simulation, channels = 1)
		self.noise.connect(0, self.filtered_noise, 0)
		self.filtered_noise.frequency = 500
		self.filtered_noise.q = 1
		self.environment = libaudioverse.SimpleEnvironmentNode(simulation, "default")
		self.environment.output_channels = 2
		self.environment.default_panning_strategy = libaudioverse.PanningStrategies.hrtf
		self.environment.default_max_distance = self.board.board_height
		self.environment.default_distance_model = libaudioverse.DistanceModels.exponential
		self.ball_source = libaudioverse.SourceNode(self.simulation, self.environment)
		self.filtered_noise.connect(0, self.ball_source, 0)
		self.environment.orientation = (0, 1, 0, 0, 0, 1)
		self.environment.position = (0, -self.board.board_width/2, 0)
		self.environment.connect_simulation(0)
		self.board.spawn_ball(position = (-0.3, 0))

	def tick(self, dt):
		self.board.tick()
		#Grab the ball's position as the new position of the source.
		ball_pos= self.board.ball.position
		self.ball_source.position = ball_pos[0], ball_pos[1], 0