""" GUI code is based on and adapted from the following online resources: """
""" https://realpython.com/python-gui-tkinter/#building-a-text-editor-example-app """
""" https://zetcode.com/tkinter/ """
""" https://www.geeksforgeeks.org/radiobutton-in-tkinter-python/ """
import time as ti
import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from functools import partial
from utils import count_occurrences, generate_vehicles, write_to_csv
from route_planning import set_variables, main

# Global variables
display = 'Welcome to ETS\'s new routing software!\n\nSelect the relevant city, toll, and fleet in the left sidebar.\nChoose your preferred first solution strategy (FSS), local search strategy (LSS), and time limit [sec] via the blue option menus.\nGenerate routes with the green button in the top left!\n\nAll vehicles are assumed to be available for routes twice per day, which is why the solution may use up to double the vehicles chosen.'
texts = ['', '', '']
new_vehicles = []
new_city = 'Paris'
new_toll = 0.00
existing_fleets = [[19, 0, 0, 0, 0, 0, 0], [8, 12, 0, 0, 0, 0, 0], [0, 17, 0, 0, 0, 0, 0]]
busy = False
busy_end = 0


# Main function to create/run GUI
def gui():
    # Function to increase discrete values for fleet selection
    def int_increase(id):
        value = fleet_nums[id]+1
        fleet_labels[id]['text'] = f' {value} of each ' if id==0 else f'Type {id}: {value}'
        fleet_nums[id] = value
    
    # Function to decrease discrete values for fleet selection
    def int_decrease(id):
        value = max(fleet_nums[id]-1, 0)
        fleet_labels[id]['text'] = f' {value} of each ' if id==0 else f'Type {id}: {value}'
        fleet_nums[id] = value

    # Function to increase float values for toll
    def float_increase():
        global new_toll
        new_toll = min(new_toll+0.01, 1)
        label_value['text'] = ' {:.2f}€/km '.format(new_toll)
    
    # Function to decrease float values for toll
    def float_decrease():
        global new_toll
        new_toll = max(new_toll-0.01, 0)
        label_value['text'] = ' {:.2f}€/km '.format(new_toll)

    # Function to update displayed text based on tab selection
    def update_display():
        global texts
        global busy
        global busy_end
        display = texts[radio_top.get()]
        if busy:
            label_busy.config(text=f'busy until ≤ {busy_end}')
            label_busy.grid(row=0, column=3, sticky='nsew', padx=5)
        else:
            label_busy.grid_forget()
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

    # Function to hide all buttons and labels relating to fleet selection
    def hide_all_fleet():
        for id, num in enumerate(fleet_nums):
            fleet_mins[id].grid_forget()
            fleet_labels[id].grid_forget()
            fleet_plus[id].grid_forget()

    # Function to show/hide the correct buttons and labels relating to fleet selection
    def show_fleet_buttons():
        if radio2.get() == 1:
            hide_all_fleet()
        elif radio2.get() == 2:
            hide_all_fleet()
            fleet_mins[0].grid(row=0, column=0, sticky='ns')
            fleet_labels[0].grid(row=0, column=1, sticky='ns')
            fleet_plus[0].grid(row=0, column=2, sticky='ns')
        else:
            for id, num in enumerate(fleet_nums):
                if id>0:
                    fleet_mins[id].grid(row=id-1, column=0, sticky='ns')
                    fleet_labels[id].grid(row=id-1, column=1, sticky='ns')
                    fleet_plus[id].grid(row=id-1, column=2, sticky='ns')

    # Function to call routing script with selected parameters
    def run_routing():
        global texts
        global busy
        global busy_end
        new_city = 'Paris' if radio.get() == 1 else 'NewYork' if radio.get() == 2 else 'Shanghai'
        new_vehicles = generate_vehicles(existing_fleets[radio.get()-1]) if radio2.get() == 1 else np.repeat(np.arange(1, 8), fleet_nums[0]*2) if radio2.get() == 2 else generate_vehicles(fleet_nums[1:])
        new_toll_str = label_value['text']
        new_fss = fss_var.get()
        new_lss = lss_var.get()
        new_time = time_var.get()
        for id, _ in enumerate(texts):
            texts[id] += f'### Solving {new_city} with{new_toll_str}tolls and fleet {count_occurrences(new_vehicles)}\n'
        busy = True
        busy_end = ti.strftime('%X', ti.localtime(ti.time()+new_time))
        update_display()

        if len(new_vehicles)>0:
            set_variables(new_vehicles, new_city, new_toll*1000, new_fss, new_lss, new_time) # Convert toll to 0.1ct value used in router
            start_time = ti.time()
            routes, load, dist, time, cost, fleet, params, csv_list = main()
            end_time = ti.time()
            texts[0] += f'{cost}\n{dist}\n{load}\n{time}\n{fleet}\n\n' if load else f'{cost}\n{dist}\n\n'
            texts[1] += routes+'\n\n____________________________________________________________\n\n\n\n\n' if load else 'No solution could be found\n____________________________________________________________\n\n'
            texts[2] += f'{params}\nSearch completed in {round(end_time-start_time, 3)}s\n'
        else:
            texts[0] += 'Infeasible parameter set detected!\nPlease check your chosen parameters\n\n'
            texts[1] += 'No solution possible\n____________________________________________________________\n\n'
            texts[2] += f'Search parameters: FSS={new_fss}, LSS={new_lss}, t={new_time}s\nNo solution possible\n'
        update_display()
        if csv_list:
            texts[2] += write_to_csv(csv_list, new_city, int(new_toll*100), new_time, round(end_time-start_time, 3), routes)
        texts[2] += '\n'
        busy = False
        update_display()
    

    # Tkinter window set-up
    window = tk.Tk()
    window.title('ETS Routing Software')
    window.rowconfigure(0, minsize=25, weight=0)
    window.rowconfigure(1, minsize=25, weight=0)
    window.rowconfigure(2, minsize=25, weight=0)
    window.rowconfigure(3, minsize=25, weight=0)
    window.rowconfigure(4, minsize=300, weight=1)
    window.rowconfigure(5, minsize=25, weight=0)
    window.columnconfigure(0, minsize=120, weight=0)
    window.columnconfigure(1, minsize=600, weight=1)


    # Content panes set-up
    button_run = tk.Button(window, text='Run routing', background='lime green', activebackground='green')
    top_pane = tk.Frame(window, relief=tk.RAISED, bd=2)
    fss_options = ['Automatic FSS', 'Path Cheapest Arc', 'Path Most Constrained Arc', 'Evaluator Strategy', 'Savings', 'Sweep', 'Christofides', 'All Unperformed', 'Best Insertion', 'Parallel Cheapest Insertion', 'Local Cheapest Insertion', 'Global Cheapest Arc', 'Local Cheapest Arc', 'First Unbound Min Value']
    fss_var = tk.StringVar()
    fss_var.set('Automatic FSS')
    fss_menu = tk.OptionMenu(window, fss_var, *fss_options)
    fss_menu.config(bg='light sea green', activebackground='medium turquoise')
    lss_options = ['Automatic LSS', 'Greedy Descent', 'Guided Local Search', 'Simulated Annealing', 'Tabu Search', 'Generic Tabu Search']
    lss_var = tk.StringVar()
    lss_var.set('Automatic LSS')
    lss_menu = tk.OptionMenu(window, lss_var, *lss_options)
    lss_menu.config(bg='light sea green', activebackground='medium turquoise')
    time_options = [1, 2, 5, 10, 30, 60, 120, 300, 600]
    time_var = tk.IntVar()
    time_var.set(30)
    time_menu = tk.OptionMenu(window, time_var, *time_options)
    time_menu.config(bg='light sea green', activebackground='medium turquoise')
    left_pane = tk.Frame(window, width=120, relief=tk.RAISED, bd=2)
    main_pane = scrolledtext.ScrolledText(window, wrap=tk.WORD)
    main_pane.insert(tk.INSERT, display)
    main_pane.configure(state='disabled')
    button_clear = tk.Button(master=window, text='Clear text', command=clear, bg='dark gray')


    # Content on left sidebar
    #   City selection
    label_city = tk.Label(master=left_pane, text='Select city:')
    label_city.grid(row=0, column=0, sticky='w', pady=3)

    radio = tk.IntVar(window, 1)
    values = {'Paris' : 1, 'New York' : 2, 'Shanghai' : 3}
    for (text, value) in values.items():
        button = tk.Radiobutton(left_pane, text=text, variable=radio, value=value)
        button.grid(row=value, column=0, sticky='w')

    separator = tk.ttk.Separator(left_pane, orient='horizontal')
    separator.grid(row=4, columnspan=2, sticky='nsew', pady=3)

    #   Toll selection
    label_title = tk.Label(master=left_pane, text='Set city tolls:')
    label_title.grid(row=5, column=0, sticky='w', pady=3)

    button_subpane = tk.Frame(left_pane)
    button_minus = tk.Button(master=button_subpane, text=' - ', command=float_decrease, repeatdelay=250, repeatinterval=50)
    button_minus.grid(row=0, column=0, sticky='w')
    label_value = tk.Label(master=button_subpane, text=f' 0.00€/km ')
    label_value.grid(row=0, column=1)
    button_plus = tk.Button(master=button_subpane, text=' + ', command=float_increase, repeatdelay=250, repeatinterval=50)
    button_plus.grid(row=0, column=2, sticky='e')
    button_subpane.grid(row=6, column=0, sticky='ns', padx=2, pady=5)

    separator2 = tk.ttk.Separator(left_pane, orient='horizontal')
    separator2.grid(row=7, columnspan=1, sticky='ew', pady=3)

    #   Fleet selection
    label_fleet = tk.Label(master=left_pane, text='Choose fleet:')
    label_fleet.grid(row=8, column=0, sticky='w', pady=3)

    radio2 = tk.IntVar(window, 1)
    values2 = {'Existing' : 1, 'New (equal)' : 2, 'New (custom)' : 3}
    for (text, value) in values2.items():
        button = tk.Radiobutton(left_pane, text=text, variable=radio2, value=value, command=show_fleet_buttons)
        button.grid(row=value+8, column=0, sticky='w')

    button_subpane2 = tk.Frame(left_pane)
    fleet_nums = [0, 0, 0, 0, 0, 0, 0, 0]
    fleet_mins = []
    fleet_labels = []
    fleet_plus = []
    for id, num in enumerate(fleet_nums):
        fleet_mins.append(tk.Button(master=button_subpane2, text=' - ', command=partial(int_decrease, id), repeatdelay=250, repeatinterval=50))
        fleet_labels.append(tk.Label(master=button_subpane2, text=f' {num} of each ' if id==0 else f'Type {id}: {num}'))
        fleet_plus.append(tk.Button(master=button_subpane2, text=' + ', command=partial(int_increase, id), repeatdelay=250, repeatinterval=50))
    button_subpane2.grid(row=12, column=0, sticky='ns', padx=2, pady=5)


    # Content on top menubar
    radio_top = tk.IntVar(top_pane, 0)
    values_top = {'Summary' : 0, 'Routes' : 1, 'Console' : 2}
    for (text, value) in values_top.items():
        button = tk.Radiobutton(top_pane, text=text, variable=radio_top, value=value, indicator=0, background='light gray', command=update_display)
        button.grid(row=0, column=value, sticky='nsew')
        
    label_busy = tk.Label(master=top_pane, text=f'Busy (done by <={busy_end}', fg='red')


    # Content pane grid managers
    button_run.configure(command=run_routing)
    button_run.grid(row=0, column=0, sticky='nsew')
    top_pane.grid(row=0, column=1, sticky='nsew')
    fss_menu.grid(row=1, column=0, sticky='nsew')
    lss_menu.grid(row=2, column=0, sticky='nsew')
    time_menu.grid(row=3, column=0, sticky='nsew')
    main_pane.grid(row=1, rowspan=5, column=1, sticky='nsew')
    left_pane.grid(row=4, column=0, sticky='nsew')
    button_clear.grid(row=5, column=0, sticky='nsew')

    
    # GUI mainloop
    window.mainloop()


if __name__ == '__main__':
    gui()