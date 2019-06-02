from tkinter import Label, Tk, Frame, Button, Entry, StringVar, Text, END
from tkinter.ttk import Combobox
from tkinter.scrolledtext import ScrolledText
from pandastable import Table, TableModel

class ButtonMode(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent, bg=LINECOLOR)
        for i, t in enumerate(['商品', '開始日期', '結束日期', '頻率']):
            Label(self, text=t).grid(row=0, column=i, **PAD)
        self.q = [ StringVar(), StringVar(), StringVar(), StringVar() ]
        Combobox(self, values=['A', 'B', 'C', 'D'],
                    textvariable = self.q[0], width=10 ).grid(row=1, column=0)
        Entry(self, textvariable = self.q[1], width=10 ).grid(row=1, column=1)
        Entry(self, textvariable = self.q[2], width=10 ).grid(row=1, column=2)
        Combobox(self, values = ['minute', 'day', 'week', 'month', 'year'], 
                    textvariable = self.q[3], width=10 ).grid(row=1, column=3)

    @property
    def query(self):
        """translate this into MySQL"""
        return ( *map(lambda x: x.get(), self.q), )


class MySQLMode(ScrolledText):
    def __init__(self, parent):
        ScrolledText.__init__(self, parent, height=8, width=44)

    @property
    def query(self):
        return self.get(0.0, END)


class ModeSelect(Combobox):
    def __init__(self, parent, values, **kargs):
        self.state  = StringVar()
        Combobox.__init__(self, parent, values=values, textvariable = self.state, **kargs)
        self.mode = ButtonMode( keyword_frame )
        self.mode.pack()
        self.current(0)
        self.bind("<<ComboboxSelected>>", self.select)

    def select(self, event):
        # clear old widgets
        for widget in keyword_frame.winfo_children():
            widget.destroy()
        # create new one
        if self.state.get() == 'Button':
            self.mode = ButtonMode( keyword_frame )
        elif self.state.get() == 'MySQL':
            self.mode = MySQLMode( keyword_frame )
        self.mode.pack()

def update():
    data.model.df = database_query( mode_select.mode.query )
    data.redraw()

def database_query(query_string):
    """
    Write your code here,
    Input
    -----
    query_string, str/tuple, depends on select mode

    Return
    ------
    pandas.DataFrame
    """
    global i 
    i += 1
    print(query_string)
    return df.head(i)

LINECOLOR = 'lightgray'
BOXCOLOR = 'palegreen'
PAD = {'padx': 1, 'pady': 1, 'sticky': 'nsew' }
df = TableModel.getSampleData()

window = Tk()
window.title("Arlen's money tree")

manipulate_frame = Frame(window, bg=LINECOLOR) 
data_frame = Frame(window, bg= LINECOLOR)
manipulate_frame.pack(padx=1, pady=1)
data_frame.pack(padx=1, pady=1)
#                                     manipulate frame
# window                              +-----------------------------------+
# +----------------------------+      |  查詢工具  |   　  mode select     |
# |      manipulate frame      |      +-----------------------------------+
# +----------------------------+      | 查詢關鍵字 |     keyword frame     |
# |         data frame         |      +-----------------------------------+
# +----------------------------+      |　　　         查詢                 |
#                                     +-----------------------------------+

Label(manipulate_frame, text='查詢工具'  , bg=BOXCOLOR).grid(row=0, column=0, **PAD)
Label(manipulate_frame, text='查詢關鍵字', bg=BOXCOLOR).grid(row=1, column=0, **PAD)
keyword_frame = Frame(manipulate_frame, bg=LINECOLOR)
keyword_frame.grid(row=1, column=1, **PAD)
mode_select = ModeSelect(manipulate_frame, values = ['Button', 'MySQL'])
mode_select.grid(row=0, column=1, **PAD)
Button(manipulate_frame, text='查詢', command=update, bg='limegreen').grid(row=2, column=0, columnspan=2, **PAD)

data =Table(data_frame, showtoolbar=True, showstatusbar=True, width=300)

i = 5
data.model.df = dataframe=df.head(i)
data.show()

window.mainloop()