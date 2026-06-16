from manim import *

class Myscene(Scene):
    CONFIG = {
        "x_min": -4,
        "x_max": 4,
        "y_min": -2,
        "y_max": 2,
        "graph_origin": ORIGIN,
        "function_color": WHITE,
        "axes_color": BLUE
    }

    def construct(self):
        #Make  graph
        axes = Axes(axis_config={'tip_shape': StealthTip})
        func_graph =  axes.plot(lambda x: 1 / (1 + np.exp(-x)), color=WHITE)
        graph_title = Tex("sigmoid function")
        graph_title.scale(1.5)
        graph_title.to_corner(UP + LEFT)

        func_graph_2 =  axes.plot(lambda x: np.tanh(x), color=PURE_GREEN)
        graph_title_2 = Tex("tanh function")
        graph_title_2.scale(1.5)
        graph_title_2.to_corner(UP + LEFT)

        func_graph_3 =  axes.plot(lambda x: np.maximum(0, x), color=YELLOW_C)
        graph_title_3 = Tex("ReLU function")
        graph_title_3.scale(1.5)
        graph_title_3.to_corner(UP + LEFT)


        #Display  graph
        self.add(axes)
        self.play(Create(func_graph))
        self.add(graph_title)
        self.wait(1)
        self.play(FadeOut(graph_title))
        self.play(Create(func_graph_2))
        self.add(graph_title_2)
        self.wait(1)
        self.play(FadeOut(graph_title_2))
        self.play(Create(func_graph_3))
        self.add(graph_title_3)
        self.wait(2)