from manim import *

class MyAnimation(Scene):
    def construct(self):
        circle = Circle(radius=1.0)

        self.add(circle)
        self.play(circle.animate.shift(RIGHT))
        self.wait(2)
        self.play(circle.animate.shift(LEFT))
        self.wait(2)