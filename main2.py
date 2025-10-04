from tkinter import *
from tkinter import ttk

HEADERSIZE = 3

class FuelGuy(object):
    def __init__(self):
        self.table= []
        self.columnHeaders = ['Airport', 'Fuel price', 'Fee', 'Amount\nto waive', 'Cost of fuel\nto waive',
                         'Max fuel before\nmin-to-waive', 'Fuel taking', 'Leg cost', 'Fuel\nstart / end',
                         'Leg burn']
        self.root = Tk()
        self.root.title("Fuel Calculator")
        self.root.resizable(width=False, height=False)

        self.mainframe = ttk.Frame(self.root, padding=(3, 3, 12, 12))
        self.mainframe.grid(column=0, row=0, sticky=(N, W, E, S))

        for i in range(len(self.columnHeaders)):
            ttk.Label(self.mainframe, text=self.columnHeaders[i]).grid(column=i + 1, row=0)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.mainframe.columnconfigure(2, weight=1)
        for child in self.mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

        bottomLine = len(self.table) + HEADERSIZE
        ttk.Button(self.mainframe, text="Add Line", command=self.add_line).grid(column=0, row=0, sticky=W)

        self.root.bind("<Return>", lambda e: self.add_line.invoke())
        self.add_line(2)
        self.root.mainloop()

    def add_line(self, add=1):
        print('adding...')
        for ct in range(len(self.table), len(self.table) + add):
            self.table.append(
                {'airportID' + str(ct): StringVar(), 'fuelPrice' + str(ct): StringVar(), 'fee' + str(ct): StringVar(),
                 'amountWaiveGal' + str(ct): StringVar(),
                 'amountWaiveLb' + str(ct): StringVar(), 'costToWaive' + str(ct): StringVar(),
                 'maxBeforeWaive' + str(ct): StringVar(), 'fuelTakingGal' + str(ct): StringVar(),
                 'fuelTakingLB' + str(ct): StringVar(), 'legCost' + str(ct): StringVar(),
                 'fuelStart' + str(ct): StringVar(), 'fuelEnd' + str(ct): StringVar(),
                 'legBurn' + str(ct): StringVar()})
            line = []
            for k in self.table[ct].keys():
                line.append(k + 'Entry')
                line[-1] = ttk.Entry(self.mainframe, textvariable=self.table[ct][k], width=5)
                line[-1].grid(row=ct + HEADERSIZE, column=len(line))

if __name__ == '__main__':
    fg = FuelGuy()

'''
def add_line(add, ct):
    print('adding...')
    table.append({'airportID'+str(ct):StringVar(), 'fuelPrice' + str(ct):StringVar(), 'fee' + str(ct):StringVar(), 'amountWaiveGal' + str(ct):StringVar(),
                  'amountWaiveLb'+str(ct):StringVar(), 'costToWaive' + str(ct):StringVar(), 'maxBeforeWaive' + str(ct):StringVar(), 'fuelTakingGal' + str(ct):StringVar(),
                  'fuelTakingLB'+str(ct):StringVar(), 'legCost' + str(ct):StringVar(), 'fuelStart' + str(ct):StringVar(), 'fuelEnd' + str(ct):StringVar(), 'legBurn' + str(ct):StringVar()})
    line = []
    for k in table[ct].keys():
        line.append(k + 'Entry')
        line[-1] = ttk.Entry(mainframe, textvariable=table[ct][k], width=10)
        line[-1].grid(row=ct + HEADERSIZE, column=len(line) - 1)

    if ct < add - 1:
        return add_line(add, ct + 1) + 1
    else:
        return 1

def nice_add_line(n=1):
    return add_line(lines + n, lines)

#INIT setup
root = Tk()
root.title("Fuel Calculator")
root.resizable(width=False, height=False)

mainframe = ttk.Frame(root, padding=(3, 3, 12, 12))
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))

columnHeaders=['Airport', 'Fuel price', 'Fee', 'Amount\nto waive', 'Cost of fuel\nto waive',
               'Max fuel before\nmin-to-waive', 'Fuel taking', 'Leg cost', 'Fuel\nstart / end',
               'Leg burn']

for i in range(len(columnHeaders)):
    ttk.Label(mainframe, text=columnHeaders[i]).grid(column=i, row=0)

table = []
lines = 0
lines += nice_add_line(2)


#bottom line stuff
bottomLine = lines + HEADERSIZE
ttk.Button(mainframe, text="Add Line", command=nice_add_line).grid(column=0, row=bottomLine, sticky=W)

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
mainframe.columnconfigure(2, weight=1)
for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=5)

root.bind("<Return>", lambda e: nice_add_line.invoke())

root.mainloop()
'''
