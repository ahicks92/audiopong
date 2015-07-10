from __future__ import division
import Box2D
import enum

#There are a very limited number of objects in this game, so we can just use an enum.
#Other game tuypes need more stuff, so this would often be classes.
ObjectTypes = enum.Enum('ObjectTypes', 'ball lower_paddle upper_paddle border lower_dead_zone upper_dead_zone')


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
		self.paddle_width = paddle_width
		self.paddle_height = paddle_height
		self.ball_radius = ball_radius
		#Set up the physics.
		#This stuff never changes.
		self.world = Box2D.b2World()
		#Must be in counterclockwise ordering.
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
		self.border_vertices = [(-board_width/2, -board_height/2), (board_width/2, -board_height/2), (board_width/2, board_height/2), (-board_width/2, board_height/2)]
		#first, build the paddle shapes.
		self.lower_paddle_shape = Box2D.b2PolygonShape(vertices = self.lower_paddle_vertices)
		self.upper_paddle_shape = Box2D.b2PolygonShape(vertices = self.upper_paddle_vertices)
		#The dead zones are boxes.
		self.lower_dead_zone_shape = Box2D.b2PolygonShape()
		self.lower_dead_zone_shape.SetAsBox(board_width/2, dead_zone_height/2)
		self.upper_dead_zone_shape = Box2D.b2PolygonShape()
		self.upper_dead_zone_shape.SetAsBox(board_width/2, dead_zone_height/2)
		#The border:
		self.border_shape = Box2D.b2ChainShape()
		#Vertices can only be replaced, don't try to modify this list. Annoying bug in Box2D bindings.
		self.border_shape.vertices_loop = self.border_vertices
		#Box2D makes bodies from body definitions, we do these here.
		#Everything gets a fixture definition, named with _fixture.
		self.lower_paddle_fixture = Box2D.b2FixtureDef()
		self.upper_paddle_fixture = Box2D.b2FixtureDef()
		self.lower_dead_zone_fixture = Box2D.b2FixtureDef()
		self.upper_dead_zone_fixture = Box2D.b2FixtureDef()
		self.border_fixture = Box2D.b2FixtureDef()
		#Wire up the shapes:
		self.border_fixture.shape = self.border_shape
		self.lower_paddle_fixture.shape = self.lower_paddle_shape
		self.upper_paddle_fixture.shape = self.upper_paddle_shape
		self.lower_dead_zone_fixture.shape = self.lower_dead_zone_shape
		self.upper_dead_zone_fixture.shape = self.upper_dead_zone_shape
		#Clear frictions:
		self.lower_paddle_fixture.friction = 0
		self.upper_paddle_fixture.friction = 0
		self.border_fixture.friction = 0
		#The dead zones are sensors:
		self.lower_dead_zone_fixture.isSensor = True
		self.upper_dead_zone_fixture.isSensor = True
		#We can now create the bodies for everything permanent; we avoid the ball.
		#Box2D invalidates the associated shapes when a body is destroyed, and balls are destroyed when they hit the dead zone.
		#Since this is swig, best to avoid.
		self.lower_paddle_def = Box2D.b2BodyDef()
		self.upper_paddle_def = Box2D.b2BodyDef()
		self.lower_dead_zone_def = Box2D.b2BodyDef()
		self.upper_dead_zone_def = Box2D.b2BodyDef()
		self.border_def = Box2D.b2BodyDef()
		#Static bodies are bodies which do not move, ever, the end:
		self.border_def.type = Box2D.b2_staticBody
		self.lower_dead_zone_def.type = Box2D.b2_staticBody
		self.upper_dead_zone_def.type = Box2D.b2_staticBody
		#Kinematic bodies are manipulated by us. We can set the velocity, but they won't be affected by forces.
		self.lower_paddle_def.type = Box2D.b2_kinematicBody
		self.upper_paddle_def.type = Box2D.b2_kinematicBody
		#The position of the lower paddle is just above the lower dead zone; the upper paddle, just below the upper dead zone.
		#Positions are relative to the back of the paddle.
		self.lower_paddle_def.position = (0.0, -board_height/2+dead_zone_height)
		self.upper_paddle_def.position = (0.0, board_height/2-dead_zone_height)
		#The positions of the dead zones is relative to their centers.
		self.lower_dead_zone_def.position = (0.0, -board_height/2+dead_zone_height/2)
		self.upper_dead_zone_def.position = (0.0, board_height/2-dead_zone_height/2)
		#We finally make the calls to create the bodies.
		self.border = self.world.CreateBody(self.border_def)
		self.lower_paddle = self.world.CreateBody(self.lower_paddle_def)
		self.upper_paddle = self.world.CreateBody(self.upper_paddle_def)
		self.lower_dead_zone = self.world.CreateBody(self.lower_dead_zone_def)
		self.upper_dead_zone = self.world.CreateBody(self.upper_dead_zone_def)
		self.border.CreateFixture(self.border_fixture)
		self.lower_dead_zone.CreateFixture(self.lower_dead_zone_fixture)
		self.upper_dead_zone.CreateFixture(self.upper_dead_zone_fixture)
		self.lower_paddle.CreateFixture(self.lower_paddle_fixture)
		self.upper_paddle.CreateFixture(self.upper_paddle_fixture)
		#Finally, tag objects with their types, so we can tell them apart.
		self.border.userData = ObjectTypes.border
		self.upper_paddle.userData = ObjectTypes.upper_paddle
		self.lower_paddle.userData = ObjectTypes.lower_paddle
		self.lower_dead_zone.userData = ObjectTypes.lower_dead_zone
		self.upper_dead_zone.userData = ObjectTypes.upper_dead_zone
		
