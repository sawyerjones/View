from textx import metamodel_from_file
from manim import *
import numpy as np

class ManimInterpreter:
    def __init__(self, grammar_file):
        # get grammar rules
        self.meta_model = metamodel_from_file(grammar_file)
        
    def interpret_file(self, input_file):
        model = self.meta_model.model_from_file(input_file)
        return self.create_scene(model)
    
    def create_scene(self, model):
        class GeneratedScene(Scene):
            # pass config settings to Scene
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
            
            def construct(self_scene):
                # init dictionaries and maps
                objects = {}
                creation_commands = []
                animation_commands = []
                
                position_map = {
                    'topLeft': UP + LEFT,
                    'topCenter': UP,
                    'topRight': UP + RIGHT,
                    'left': LEFT,
                    'center': ORIGIN,
                    'right': RIGHT,
                    'bottomLeft': DOWN + LEFT,
                    'bottomCenter': DOWN,
                    'bottomRight': DOWN + RIGHT
                }
                
                color_map = {
                    'red': RED,
                    'blue': BLUE,
                    'green': GREEN,
                    'yellow': YELLOW,
                    'white': WHITE,
                    'black': BLACK,
                    'purple': PURPLE,
                    'orange': ORANGE
                }

                def create_star(size):
                    num_points = 5
                    # golden ratio: outer = 1, inner = 1 * .382
                    outer_radius = size
                    inner_radius = size * 0.382  
                    # creates 10 angles from 0 rads to 2pi rads --> 0, pi/5, 2pi/5 ...
                    angles = np.linspace(0, 2*np.pi, num_points*2, endpoint=False)
                    points = []
                    
                    for i, angle in enumerate(angles):
                        # alternate drawing outer and inner radius
                        radius = outer_radius if i % 2 == 0 else inner_radius
                        x = radius * np.cos(angle - np.pi/2)
                        y = radius * np.sin(angle - np.pi/2)
                        points.append([x, y, 0])

                    star = Polygon(*points)
                    # default orientation looks weird    
                    star.rotate(PI/5)
                    return star

                # separate creation and animation commands
                for cmd in model.commands:
                    if hasattr(cmd, 'target') and hasattr(cmd, 'speed'):
                        animation_commands.append(cmd)
                    else:
                        creation_commands.append(cmd)
                        
                # create all objects first so animations don't stall out
                for cmd in creation_commands:
                    if isinstance(cmd, self.meta_model['CreateTextCommand']):
                        # Remove the quotes from the content string
                        text_content = cmd.content.strip('"')
                        text = Text(text_content)
                        text.scale(0.75)
                        if hasattr(cmd, 'position') and cmd.position in position_map:
                            text.move_to(position_map[cmd.position])
                        # Use the text content as the key for text objects
                        objects[text_content] = text
                    # generate specific shape w/ color, size, & position
                    elif isinstance(cmd, self.meta_model['CreateShapeCommand']):
                        shape_color = color_map.get(cmd.color, WHITE) if hasattr(cmd, 'color') else WHITE
                        shape_size = cmd.size if hasattr(cmd, 'size') else 1.0
            
                        if cmd.shape == 'circle':
                            shape = Circle(radius=shape_size).set_color(shape_color)
                        elif cmd.shape == 'square':
                            shape = Square(side_length=shape_size).set_color(shape_color)
                        elif cmd.shape == 'rectangle':
                            shape = Rectangle(width=shape_size*2, height=shape_size).set_color(shape_color)
                        elif cmd.shape == 'triangle':
                            shape = Triangle().scale(shape_size).set_color(shape_color)
                        elif cmd.shape == 'star':
                            shape = create_star(shape_size).set_color(shape_color)
                            
                        if hasattr(cmd, 'position') and cmd.position in position_map:
                            shape.move_to(position_map[cmd.position])
                            
                        objects[cmd.name] = shape

                self_scene.add(*objects.values())
                
                self_scene.wait(0.5)
                
                for cmd in animation_commands:
                    if not hasattr(cmd, 'target') or cmd.target not in objects:
                        continue
                        
                    target_obj = objects[cmd.target]
                    # spins
                    if isinstance(cmd, self.meta_model['SpinCommand']):
                        rotation_time = 2.0 / cmd.speed
                        self_scene.play(
                            Rotate(
                                target_obj,
                                angle=TAU,
                                about_point=target_obj.get_center(),
                                rate_func=linear,
                                run_time=rotation_time
                            )
                        )
                    elif isinstance(cmd, self.meta_model['GlideCommand']):
                        if hasattr(cmd, 'destination') and cmd.destination in position_map:
                            destination = position_map[cmd.destination]
                            movement_time = 2.0 / cmd.speed
                            self_scene.play(
                                target_obj.animate.move_to(destination),
                                run_time=movement_time,
                                rate_func=smooth
                            )
                    else:  # rotates
                        # current_pos = (x,y,z), radius^2 = x^2 + y^2, since origin is always (0,0,0)
                        current_pos = target_obj.get_center()
                        radius = np.sqrt(current_pos[0]**2 + current_pos[1]**2)
                        
                        # calculate initial angle, radians from positive X-axis
                        initial_angle = np.arctan2(current_pos[1], current_pos[0])
                        
                        # input val from 0 --> 1, every val between represents position along circle's path
                        def rotate_around_center(t):
                            angle = initial_angle + t * TAU
                            # generates coordinates for each position around the circle
                            return np.array([
                                radius * np.cos(angle), # x
                                radius * np.sin(angle), # y
                                0 # z
                            ])
                        
                        rotation_time = 4.0 / cmd.speed
                        # UpdateFromAlphaFunc runs each frame, alpha increments from 0 --> 1 
                        self_scene.play(
                            UpdateFromAlphaFunc(
                                target_obj,
                                lambda m, alpha: m.move_to(rotate_around_center(alpha)),
                                run_time=rotation_time,
                                rate_func=linear
                            )
                        )
                
                self_scene.wait(1)
        
        return GeneratedScene