""" GUI code is based on and adapted from the following online resources: """
""" https://realpython.com/python-gui-tkinter/#building-a-text-editor-example-app """
""" https://zetcode.com/tkinter/ """
""" https://www.geeksforgeeks.org/radiobutton-in-tkinter-python/ """

import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from utils import count_occurrences
from route_planning import set_variables, main

display = 'Welcome to ETS\'s new routing software!'
texts = ['', '', '']
new_vehicles = []
new_city = 'Paris'
new_toll = 0.00


def gui():
    global display
    global texts
    global new_vehicles
    global new_city
    global new_toll

    # Function to increase discrete values for fleet selection
    def int_increase():
        value = int(label_value['text'])
        label_value['text'] = f'{value+1}'
    
    # Function to decrease discrete values for fleet selection
    def int_decrease():
        value = int(label_value['text'])
        label_value['text'] = f'{max(value-1, 0)}'

    # Function to increase float values for toll
    def float_increase():
        value = min(float(label_value['text'])+0.01, 1)
        label_value['text'] = ' {:.2f} '.format(value)
    
    # Function to decrease float values for toll
    def float_decrease():
        value = max(float(label_value['text'])-0.01, 0)
        label_value['text'] = ' {:.2f} '.format(value)

    # Function to update displayed text based on tab selection
    def update_display():
        global texts
        display = texts[radio_top.get()]
        main_pane.configure(state='normal')
        main_pane.delete('1.0', tk.END)
        main_pane.insert(tk.INSERT, display)
        main_pane.configure(state='disabled')
        window.update()

    # Function to clear all text
    def clear():
        global texts
        texts = ['', '', '']
        update_display()

    # Function to call routing script with selected parameters
    def run_routing():
        global texts
        new_vehicles = np.repeat(np.arange(1, 8), 10)
        new_city = 'Paris' if radio.get()==1 else 'NewYork' if radio.get()==2 else 'Shanghai'
        new_toll_str = label_value['text']
        new_toll = float(new_toll_str)
        for id, _ in enumerate(texts):
            texts[id] += f'### Computing routes for {new_city} with {new_toll_str}€/km tolls and fleet {count_occurrences(new_vehicles)} ###\n\n'
        update_display()

        set_variables(new_vehicles, new_city, new_toll*1000) # Convert toll to 0.1ct value used in router
        routes, load, dist, cost, fleet = main()
        texts[0] += f'{cost}\n{dist}\n{load}\n{fleet}\n\n\n'
        texts[1] += routes+'\n\n\n'
        update_display()
    

    # Tkinter window set-up
    window = tk.Tk()
    window.title('ETS Routing Software')
    window.rowconfigure(1, minsize=800, weight=1)
    window.columnconfigure(1, minsize=800, weight=1)


    # Content panes set-up
    button_run = tk.Button(window, text='Run routing', background='green')
    top_pane = tk.Frame(window, relief=tk.RAISED, bd=2)
    left_pane = tk.Frame(window, relief=tk.RAISED, bd=2)
    main_pane = scrolledtext.ScrolledText(window, wrap=tk.WORD)
    main_pane.insert(tk.INSERT, display)
    main_pane.configure(state='disabled')


    # Content on left sidebar
    label_city = tk.Label(master=left_pane, text='Select city:')
    label_city.grid(row=0, column=0, sticky='w', pady=3)

    radio = tk.IntVar(window, 1)
    values = {'Paris' : 1, 'New York' : 2, 'Shanghai' : 3}

    for (text, value) in values.items():
        button = tk.Radiobutton(left_pane, text=text, variable=radio, value=value)
        button.grid(row=value, column=0, sticky='w')

    separator = tk.ttk.Separator(left_pane, orient='horizontal')
    separator.grid(row=4, columnspan=1, sticky='ew', pady=3)

    label_title = tk.Label(master=left_pane, text='Set tolls [€/km]:')
    label_title.grid(row=5, column=0, pady=3)

    button_subpane = tk.Frame(left_pane)
    button_minus = tk.Button(master=button_subpane, text=' - ', command=float_decrease, repeatdelay=250, repeatinterval=50)
    button_minus.grid(row=0, column=0, sticky='w')
    label_value = tk.Label(master=button_subpane, text=' 0.00 ')
    label_value.grid(row=0, column=1)
    button_plus = tk.Button(master=button_subpane, text=' + ', command=float_increase, repeatdelay=250, repeatinterval=50)
    button_plus.grid(row=0, column=2, sticky='e')
    button_subpane.grid(row=6, column=0, sticky='ns', padx=2, pady=5)

    separator2 = tk.ttk.Separator(left_pane, orient='horizontal')
    separator2.grid(row=7, columnspan=1, sticky='ew', pady=3)


    # Content on top menubar
    radio_top = tk.IntVar(top_pane, 0)
    values_top = {'Summary' : 0, 'Routes' : 1, 'Console' : 2}

    for (text, value) in values_top.items():
        button = tk.Radiobutton(top_pane, text=text, variable=radio_top, value=value, indicator=0, background='light gray', command=update_display)
        button.grid(row=0, column=value, sticky='ns')

    button_clear = tk.Button(master=top_pane, text='Clear text', command=clear)
    button_clear.grid(row=0, column=3, sticky='ne')

    # Content pane grid managers
    button_run.configure(command=run_routing)
    button_run.grid(row=0, column=0, sticky='nsew')
    top_pane.grid(row=0, column=1, sticky='nw')
    left_pane.grid(row=1, column=0, sticky='ns')
    main_pane.grid(row=1, column=1, sticky='nsew')

    
    # GUI mainloop
    window.mainloop()


if __name__ == '__main__':
    gui()