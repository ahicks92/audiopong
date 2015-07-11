from __future__ import division
import Box2D

def create_body(world, shape_type, position = (0, 0), angle = 0,
friction = None, restitution = None, density = None, linear_damping = None,
is_sensor = False, fixed_rotation = False,
body_type = Box2D.b2_dynamicBody, user_data = None, **kwargs):
	"""Creates a body.
	All parameters should be self-explanatory with a quick skim of the Box2D manual.
	
	**kwargs will be set on the shape type after its construction."""
	shape = shape_type()
	for i, j in kwargs.iteritems():
		setattr(shape, i, j)
	fixture_def = Box2D.b2FixtureDef()
	if friction is not None:
		fixture_def.friction = friction
	if restitution is not None:
		fixture_def.restitution = restitution
	if density is not None:
		fixture_def.density = density
	fixture_def.shape = shape
	fixture_def.isSensor = is_sensor
	body_def = Box2D.b2BodyDef()
	body_def.type = body_type
	body_def.position = position
	body_def.angle = angle
	body = world.CreateBody(body_def)
	body.CreateFixture(fixture_def)
	body.userData = user_data
	if linear_damping:
		body.linearDamping = linear_damping
	body.fixedRotation = fixed_rotation
	return body

def box_vertices(half_width, half_height):
	"""Creates a list of vertices for a box, such that the upper left corner is (-half_width, half_height) and the lower right (half_widt, -half_height)"""
	return [(-half_width, -half_height), (half_width, -half_height), (half_width, half_height), (-half_width, half_height)]
