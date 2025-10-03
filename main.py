from tkinter import *
from tkinter import ttk

LINECOUNT = 0
table = []

def add_line(n):
    table.append({'airportID'+str(LINECOUNT):StringVar(), 'fuelPrice'+str(LINECOUNT):StringVar(), 'fee'+str(LINECOUNT):StringVar(), 'amountWaiveGal'+str(LINECOUNT):StringVar(),
                  'amountWaiveLb'+str(LINECOUNT):StringVar(), 'costToWaive'+str(LINECOUNT):StringVar(), 'maxBeforeWaive'+str(LINECOUNT):StringVar(),'fuelTakingGal'+str(LINECOUNT):StringVar(),
                  'fuelTakingLB'+str(LINECOUNT):StringVar(), 'legCost'+str(LINECOUNT):StringVar(), 'fuelStart'+str(LINECOUNT):StringVar(), 'fuelEnd'+str(LINECOUNT):StringVar(), 'legBurn'+str(LINECOUNT):StringVar()})
    line = []
    for k in table[LINECOUNT].keys():
        line.append(k + 'Entry')
        line[-1] = ttk.Entry(mainframe, textvariable=table[LINECOUNT][k], width=10)
        line[-1].grid(row=LINECOUNT + 3, column=len(line)-1)
        LINECOUNT += 1
    return



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

add_line()

'''
airport1 = StringVar()
airportEntry1 = ttk.Entry(mainframe, textvariable=airport1, width=10)
airportEntry1.grid(column=0, row=2)

fuelPrice1 = StringVar()
fuelPriceEntry1 = ttk.Entry(mainframe, textvariable=fuelPrice1, width=10)
fuelPriceEntry1.grid(column=1, row=2)

fee1 = StringVar()
feeEntry1 = ttk.Entry(mainframe, textvariable=fee1, width=10)
feeEntry1.grid(column=2, row=2)

amountWaive1 = StringVar()
amountWaiveEntry1 = ttk.Entry(mainframe, textvariable=amountWaive1, width=10)
amountWaiveEntry1.grid(column=3, row=2)
'''




ttk.Button(mainframe, text="Save").grid(column=0, row=LINECOUNT + 4, sticky=W)

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
mainframe.columnconfigure(2, weight=1)
for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=5)


root.bind("<Return>")

root.mainloop()