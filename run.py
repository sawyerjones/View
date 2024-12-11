from manim import *
from ManimInterpreter import ManimInterpreter
import sys

interpreter = ManimInterpreter("view.tx")

filename = sys.argv[1]
MyGeneratedScene = interpreter.interpret_file(filename)

if __name__ == '__main__':
    # force mp4 & popup window
    config.write_to_movie = True
    config.format = "mp4"
    config.output_file = "scene.mp4"
    config.preview = True
    
    scene = MyGeneratedScene()
    try:
        scene.render()
    except Exception as e:
        print(f"Error during rendering: {str(e)}")