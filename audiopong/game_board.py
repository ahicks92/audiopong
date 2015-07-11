from __future__ import division
import Box2D
import enum
from . import physics_helper

#There are a very limited number of objects in this game, so we can just use an enum.
#Other game tuypes need more stuff, so this would often be classes.
ObjectTypes = enum.IntEnum('ObjectTypes', 'ball lower_paddle upper_paddle border lower_dead_zone upper_dead_zone')

#This class allows us to detect collisions. With it, we can build a list.
class CollisionCallback(Box2D.b2ContactListener):
	"""Used to listen for collisions.
	
	Appends the userdata off both bodies to for_objects.collisions, or removes them when they no longer touch.
	it is assumed that for_object.collisions is a dict.  The keys are tuples of touching items and the values the approximate position of the collision.
	
	for_object.per_tick_collisions is the same, but is not automatically cleared; use it to detect that something happened, rather than that something is happening."""
	
	def __init__(self, for_object):
		super(CollisionCallback, self).__init__()
		self.for_object=for_object

	def BeginContact(self, contact):
		a, b=contact.fixtureA.body.userData, contact.fixtureB.body.userData
		if a > b:
			a, b = b, a
		print a, b, contact.worldManifold.points[0]
		self.for_object.collisions[(a, b)] = contact.worldManifold.points[0]
		self.for_object.per_tick_collisions[(a, b)] = contact.worldManifold.points[0]

	def EndContact(self, contact):
		a, b = contact.fixtureA.body.userData, contact.fixtureB.body.userData
		if a > b:
			a, b = b, a
		if (a, b) in self.for_object.collisions:
			del self.for_object.collisions[(a, b)]

class GameBoard(object):
	"""The game board: manages physics and simulation.
	Audio is handled elsewhere.
	
	A pong board consists of a rectangular "table", two paddles fixed in grooves at either end, and a dead zone.
	The paddles created by this class are triangular, such that the ball will not always reflect the same; with practice, a player can learn to manipulate the ball strategically."""
	
	
	def __init__(self, board_width = 10, board_height = 30, dead_zone_height = 0.2, paddle_width = 1, paddle_height = 0.2, ball_radius = 0.05):
		#This function keeps a lot of extra stuff around for debugging.
		self.board_width = board_width
		self.board_height = board_height
		self.paddle_width = paddle_width
		self.paddle_height = paddle_height
		self.dead_zone_height = dead_zone_height
		self.ball_radius = ball_radius
		#Set up the physics.
		#This stuff never changes.
		self.world = Box2D.b2World()
		#No gravity.
		self.world.gravity = (0, 0)
		self.world.SetAllowSleeping(False)
		#Must be in counterclockwise ordering.
		#these are set up so that the position of the paddle is relative to its back.
		self.lower_paddle_vertices = [(-paddle_width/2, 0), (paddle_width/2, 0), (0, paddle_height)]
		#The other paddle is made by flipping the lower one.
		self.upper_paddle_vertices = [(i[0], -i[1]) for i in self.lower_paddle_vertices]
		#But flipping a shape changes the winding of the vertices to be clockwise, so reverse:
		self.upper_paddle_vertices.reverse()
		#This is the outer line of the board.
		#The center of the board is at the origin.
		#This constant is here for convenience.
		#Balls are handled in spawn_ball, which should be called by user code; you can safely have more than one, but usually won't.
		self.center = (0, 0)
		self.border = physics_helper.create_body(self.world, shape_type = Box2D.b2ChainShape, body_type = Box2D.b2_staticBody, user_data = ObjectTypes.border,
		vertices = physics_helper.box_vertices(board_width/2, board_height/2),
		restitution = 1)
		self.upper_paddle = physics_helper.create_body(self.world, shape_type = Box2D.b2PolygonShape, friction = 0, body_type = Box2D.b2_kinematicBody,
		user_data = ObjectTypes.upper_paddle, vertices = self.upper_paddle_vertices,
		position = (0, board_height/2-dead_zone_height),
		restitution = 1)
		self.lower_paddle = physics_helper.create_body(self.world, shape_type = Box2D.b2PolygonShape, body_type = Box2D.b2_kinematicBody, user_data = ObjectTypes.lower_paddle,
		vertices = self.lower_paddle_vertices, friction = 0, position = (0, -board_height/2+dead_zone_height),
		restitution = 1)
		self.lower_dead_zone = physics_helper.create_body(self.world, shape_type = Box2D.b2PolygonShape, is_sensor = True, friction = 0, body_type = Box2D.b2_staticBody, user_data = ObjectTypes.lower_dead_zone,
		position = (0.0, -board_height/2+dead_zone_height/2), vertices = physics_helper.box_vertices(board_width/2, dead_zone_height/2))
		self.upper_dead_zone = physics_helper.create_body(self.world, shape_type = Box2D.b2PolygonShape, user_data = ObjectTypes.upper_dead_zone, is_sensor = True, body_type = Box2D.b2_staticBody,
		position = (0, board_height/2-dead_zone_height/2), vertices = physics_helper.box_vertices(board_width/2, dead_zone_height/2))
		self.ball = None
		#See the CollisionCallback class docstring for these two.
		self.collisions =dict()
		self.per_tick_collisions = dict()
		self.collision_callback = CollisionCallback(self)
		self.world.contactListener = self.collision_callback

	def spawn_ball(self, position = (0, 0), velocity = (0, -5)):
		if self.ball is not None:
			raise valueError("Attempt to spawn two balls.")
		self.ball = physics_helper.create_body(self.world, shape_type = Box2D.b2CircleShape, position = position,
		user_data = ObjectTypes.ball, body_type = Box2D.b2_dynamicBody, radius = self.ball_radius,
		restitution = 1, friction = 0, density = 1000, linear_damping = 0,
		fixed_rotation = True)
		self.ball.linearVelocity = velocity

	def tick(self):
		"""Advances time by 1/60.0.
		
		This is not configurable; box2d steps have to be small."""
		#collisions is used to record ongoing; per_tick_collisions records all touches in one tick.
		self.per_tick_collisions.clear()
		#Parameters:time, iterations for velocity, iterations for position.
		self.world.Step(1/60.0, 100, 100)