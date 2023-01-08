import numpy as np
from tkinter import *
from tkinter import ttk
from route_planning import set_variables, main

""" GUI code is based on and adapted from the following online resources: """
""" https://realpython.com/python-gui-tkinter/#building-a-text-editor-example-app """
""" https://zetcode.com/tkinter/ """
""" https://www.geeksforgeeks.org/radiobutton-in-tkinter-python/ """

def make_gui():
    def int_increase():
        value = int(label_value['text'])
        label_value['text'] = f'{value+1}'
    
    def int_decrease():
        value = int(label_value['text'])
        label_value['text'] = f'{max(value-1, 0)}'

    def float_increase():
        value = min(float(label_value['text'])+0.01, 1)
        label_value['text'] = '{:.2f}'.format(value)
    
    def float_decrease():
        value = max(float(label_value['text'])-0.01, 0)
        label_value['text'] = '{:.2f}'.format(value)

    def run_routing():
        new_vehicles = np.repeat(np.arange(1, 8), 10)
        new_city = 'Paris' if radio==1 else 'NewYork' if radio==2 else 'Shanghai'
        new_tolls = float(label_value['text'])
        set_variables(new_vehicles, new_city, new_tolls)
        text_pane['text'] = main()
    
    window = Tk()
    window.title('Routing Software')

    window.rowconfigure(0, minsize=800, weight=1)
    window.columnconfigure(1, minsize=800, weight=1)

    text_pane = Label(window, text='Welcome to Efficient Transport Solution\'s new routing software!')
    button_pane = Frame(window, relief=RAISED, bd=2)
    button_subpane = Frame(button_pane)

    button_run = Button(master=button_pane, text='Run routing...', command=run_routing)
    button_run.grid(row=0, column=0, sticky='nsew')

    separator = ttk.Separator(button_pane, orient='horizontal')
    separator.grid(row=1, column=0)

    radio = IntVar(window, 1)
    values = {'Paris' : 1, 'New York' : 2, 'Shanghai' : 3}

    for (text, value) in values.items():
        button = Radiobutton(button_pane, text=text, variable=radio, value=value, indicator=0, background='light gray')
        button.grid(row=value+1, column=0, sticky='ew', padx=5, pady=5)

    label_title = Label(master=button_subpane, text='Tolls [€/km]:')
    label_title.grid(row=0, column=0)
    button_minus = Button(master=button_subpane, text='-', command=float_decrease, repeatdelay=500, repeatinterval=50)
    button_minus.grid(row=0, column=1, sticky='nsew')
    label_value = Label(master=button_subpane, text='0.00')
    label_value.grid(row=0, column=2)
    button_plus = Button(master=button_subpane, text='+', command=float_increase, repeatdelay=500, repeatinterval=50)
    button_plus.grid(row=0, column=3, sticky='nsew')

    button_pane.grid(row=0, column=0, sticky='ns')
    button_subpane.grid(row=5, column=0, sticky='ns', padx=5, pady=5)
    text_pane.grid(row=0, column=1, sticky='nsew')

    window.mainloop()


if __name__ == '__main__':
    make_gui()