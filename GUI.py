from tkinter import Label, Tk, Frame, Button, Entry, StringVar, Text, messagebox, END
from tkinter.ttk import Combobox
from tkinter.scrolledtext import ScrolledText
from pandastable import Table
from pandas import Timestamp, DataFrame
from pandas._libs.tslibs.nattype import NaTType
from database import stockDB, config

class Mode:
    @classmethod
    def set_read_method(cls, func):
        cls.read = func

class ButtonMode(Frame, Mode):
    def __init__(self, parent):
        Frame.__init__(self, parent, bg=LINECOLOR)
        self.q = [ StringVar(), StringVar(), StringVar(), StringVar() ]
        for i, t in enumerate(['商品', '開始日期', '結束日期', '頻率']):
            Label(self, text=t).grid(row=0, column=i, **PAD)
        Combobox(self, values=['FITX'],
                    textvariable = self.q[0], width=10 ).grid(row=1, column=0)
        Entry(self, textvariable = self.q[1], width=10 ).grid(row=1, column=1)
        Entry(self, textvariable = self.q[2], width=10 ).grid(row=1, column=2)
        Combobox(self, values = ['minute', 'day'], 
                    textvariable = self.q[3], width=10 ).grid(row=1, column=3)

    @property
    def query(self):
        try:
            start = Timestamp(self.q[1].get())
            end = Timestamp(self.q[2].get())
            assert not isinstance(start, NaTType) and not isinstance(end, NaTType)
        except Exception as e:
            messagebox.showinfo('Wrong Format', 'Fail to convert into Timestamp')
        else:
            sDate = start.strftime('%Y-%m-%d')
            eDate = end.strftime('%Y-%m-%d')
            sTime = start.strftime('%H:%M:%S')
            eTime = end.strftime('%H:%M:%S')
            if self.q[3].get() == 'day':
                return self.read(sDate, eDate)
            else:
                return self.read(sDate, eDate, sTime, eTime)


class SQLMode(ScrolledText, Mode):
    def __init__(self, parent):
        ScrolledText.__init__(self, parent, height=8, width=44)

    @property
    def query(self):
        return self.read( self.get(0.0, END) )

class ModeSelect(Combobox):
    def __init__(self, parent, option, **kargs):
        values = [ m.__name__.replace('Mode', '') for m in option ]
        self.state  = StringVar()
        self.option = dict( zip(values, option) )
        Combobox.__init__(self, parent, values=values, textvariable = self.state, **kargs)
        self.mode = self.option[values[0]]( keyword_frame )
        self.mode.pack()
        self.current(0)
        self.bind("<<ComboboxSelected>>", self.select)

    def select(self, event):
        # clear old widgets
        for widget in keyword_frame.winfo_children():
            widget.destroy()
        # create new one
        self.mode = self.option[self.state.get()](keyword_frame)
        self.mode.pack()

    def link(self, table):
        def update():
            table.model.df = self.mode.query.head(300)
            table.redraw()
        return update

LINECOLOR = 'lightgray'
BOXCOLOR = 'palegreen'
PAD = {'padx': 1, 'pady': 1, 'sticky': 'nsew' }

if __name__ == "__main__":
    mydb = stockDB(**config)

    ButtonMode.set_read_method(mydb.read_data)
    SQLMode.set_read_method(mydb.exe_query)

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
    mode_select = ModeSelect(manipulate_frame, option = [ButtonMode, SQLMode])
    mode_select.grid(row=0, column=1, **PAD)
    datatable =Table(data_frame, showtoolbar=True, showstatusbar=True, width=300)
    datatable.model.df = DataFrame(data={'location':['高雄'], 'politics':['發大財']})
    datatable.show()
    Button(manipulate_frame, text='查詢',
            command = mode_select.link(datatable), bg='limegreen').grid(row=2, column=0, columnspan=2, **PAD)

    window.mainloop()

    mydb.db.close()