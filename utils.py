import pandas as pd
from tkinter import *
import math
from RoutePlanningSoftware import *

def compute_euclidean_distance_matrix(locations):
    """Creates callback to return distance between points."""
    distances = {}
    for from_counter, from_node in enumerate(locations):
        distances[from_counter] = {}
        for to_counter, to_node in enumerate(locations):
            if from_counter == to_counter:
                distances[from_counter][to_counter] = 0
            else:
                # Euclidean distance
                distances[from_counter][to_counter] = (int(
                    math.hypot((from_node[0] - to_node[0]),
                               (from_node[1] - to_node[1]))))
    return distances

def get_nodes(city):
    return pd.read_csv(f'./instances/{city}.nodes', sep=' ')

def get_routes(city):
    return pd.read_csv(f'./instances/{city}.routes', sep=' ')

def get_distance_matrix_from_routes(routes, num_nodes, dist_type):
    # Returns distance matrix computed from custom .routes format
    valid = ['Total', 'Inside', 'Outside']
    if dist_type not in valid:
        raise ValueError(f"{dist_type} is not a valid distance type.\nAcceptable values are: {valid}")
    km_list = routes[f'Distance{dist_type}[km]']
    m_list = [int(1000 * x) for x in km_list] 
    # km_matrix = list(zip(*([iter(routes[f'Distance{dist_type}[km]'])]*num_nodes)))
    m_matrix = list(zip(*([iter(m_list)]*num_nodes)))
    return m_matrix

def make_gui():
    window = Tk()
    window.title('Routing Software')

    window.rowconfigure(0, minsize=800, weight=1)
    window.columnconfigure(1, minsize=800, weight=1)

    text_pane = Text(window)
    frame_buttons = Frame(window, relief=RAISED, bd=2)
    radio = IntVar(window, 1)
    values = {"Paris" : 1, "New York" : 2, "Shanghai" : 3}

    # Loop is used to create multiple Radiobuttons
    # rather than creating each button separately
    for (text, value) in values.items():
        button = Radiobutton(frame_buttons, text = text, variable = radio, value = value, indicator = 0, background = "light gray")
        button.grid(row=value-1, column=0, sticky='ew', padx=5, pady=5)

    #btn_open = Button(frame_buttons, text="Open")
    #btn_save = Button(frame_buttons, text="Save As...", command=print('Hello'))

    #btn_open.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
    #btn_save.grid(row=1, column=0, sticky="ew", padx=5)

    frame_buttons.grid(row=0, column=0, sticky="ns")
    text_pane.grid(row=0, column=1, sticky="nsew")

    window.mainloop()