import pyglet
import audiopong
import libaudioverse
libaudioverse.initialize()

window = pyglet.window.Window()
simulation = libaudioverse.Simulation()
simulation.set_output_device(-1, mixahead=2)
main_screen = audiopong.MainScreen(simulation)

pyglet.app.run()
libaudioverse.shutdown()