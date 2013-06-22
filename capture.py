"""

Data analysis Gui for csv data
Author: Lovisa Irpa Helgadottir
License: this code is in the public domain

Last modified: 20.06.2013
"""
import os
import pprint
import random
import sys
import wx

import csv
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
import numpy as np
import pylab


class PopUpBox(wx.Frame):
    def __init__(self,parent,label):
        wx.Frame.__init__(self, parent, -1, label)
        self.panel = wx.Panel(self, -1, style=wx.SIMPLE_BORDER)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        
    def create_panel(self):    
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
    
    def on_exit(self, event):
        self.Destroy()
        
        
    

class BoundControlBox(wx.Panel):
    """ A static box with a couple of radio buttons and a text
        box. Allows to switch between an automatic mode and a 
        manual mode with an associated value.
    """
    def __init__(self, parent, ID, label, initval):
        wx.Panel.__init__(self, parent, ID)
        
        self.value = initval
        
        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        
        self.radio_auto = wx.RadioButton(self, -1, label="Auto", style=wx.RB_GROUP)
        self.radio_manual = wx.RadioButton(self, -1,label="Manual")
        self.manual_text = wx.TextCtrl(self, -1, size=(35,-1),value=str(initval),style=wx.TE_PROCESS_ENTER)
        
        self.Bind(wx.EVT_UPDATE_UI, self.on_update_manual_text, self.manual_text)
        
        manual_box = wx.BoxSizer(wx.HORIZONTAL)
        manual_box.Add(self.radio_manual, flag=wx.ALIGN_CENTER_VERTICAL)
        manual_box.Add(self.manual_text, flag=wx.ALIGN_CENTER_VERTICAL)
        
        sizer.Add(self.radio_auto, 0, wx.ALL, 10)
        sizer.Add(manual_box, 0, wx.ALL, 10)
        
        self.SetSizer(sizer)
        sizer.Fit(self)
    
    def on_update_manual_text(self, event):
        self.manual_text.Enable(self.radio_manual.GetValue())
        self.value = self.manual_text.GetValue()
    
    def is_auto(self):
        return self.radio_auto.GetValue()
        
    def manual_value(self):
        return self.value


class GraphFrame(wx.Frame):
    """ The main frame of the application
    """
    
    def __init__(self):
        wx.Frame.__init__(self, None, -1, 'Data Analysis')
        
        self.filename =None
        self.data = []

        self.format="String"
        self.formats_list={'String':'S100','Int': np.int,'Float' : np.float}
        
        self.xaxis=None
        self.yaxis = []
        self.id = None
        self.selcted_ids = []
        
        self.xlabel=""
        self.ylabel=""

              
        self.create_menu()
        self.create_status_bar()
        self.create_main_panel()


    def create_menu(self):
        self.menubar = wx.MenuBar()       
        menu_file = wx.Menu()
        m_open = menu_file.Append(-1,"&Open data\tCtrl-O","Open data")
        self.Bind(wx.EVT_MENU, self.on_open_data,m_open)
        m_expt = menu_file.Append(-1, "&Save plot\tCtrl-S", "Save plot to file")
        self.Bind(wx.EVT_MENU, self.on_save_plot, m_expt)
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-X", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)
        
        menu_edit = wx.Menu()
        m_label = menu_edit.Append(-1, "Edit Labels","Edit Labels")
        self.Bind(wx.EVT_MENU, self.on_edit_label, m_label)

                
        self.menubar.Append(menu_file, "&File")
        self.menubar.Append(menu_edit,"&Edit")
        self.SetMenuBar(self.menubar)


    def create_main_panel(self):
        self.panel = wx.Panel(self, -1, style=wx.SIMPLE_BORDER)

        self.init_plot()
        
        self.canvas = FigCanvas(self.panel, -1, self.fig)

        self.xmin_control = BoundControlBox(self.panel, -1, "X min", 0)
        self.xmax_control = BoundControlBox(self.panel, -1, "X max", 1000)
        self.ymin_control = BoundControlBox(self.panel, -1, "Y min", 0)
        self.ymax_control = BoundControlBox(self.panel, -1, "Y max", 1000)
              
        self.plot_button = wx.Button(self.panel, -1, "Plot")
        self.Bind(wx.EVT_BUTTON, self.OnPlot, self.plot_button)
           
        self.cb_grid = wx.CheckBox(self.panel, -1, "Show Grid",style=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_grid, self.cb_grid)
        self.cb_grid.SetValue(True)
        
        self.cb_xlab = wx.CheckBox(self.panel, -1, "Show X labels",style=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_xlab, self.cb_xlab)        
        self.cb_xlab.SetValue(True)
        
        self.cb_title = wx.CheckBox(self.panel, -1, "Show Title",style=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_title, self.cb_title)        
        self.cb_title.SetValue(False)
        
        self.cb_bg= wx.CheckBox(self.panel, -1, "Toggle Background", style=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_bg, self.cb_bg)        
        self.cb_bg.SetValue(True) 
       

        self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox1.Add(self.cb_grid, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.AddSpacer(10)
        self.hbox1.Add(self.cb_xlab, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.AddSpacer(10)
        self.hbox1.Add(self.cb_title, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.AddSpacer(10)
        self.hbox1.Add(self.cb_bg, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        
        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2.Add(self.xmin_control, border=5, flag=wx.ALL)
        self.hbox2.Add(self.xmax_control, border=5, flag=wx.ALL)
        self.hbox2.AddSpacer(10)
        self.hbox2.Add(self.ymin_control, border=5, flag=wx.ALL)
        self.hbox2.Add(self.ymax_control, border=5, flag=wx.ALL)
        
        self.lc = wx.ListCtrl(self.panel, -1, style=wx.LC_REPORT)
        self.lc.InsertColumn(0, 'Parameter')
        self.lc.InsertColumn(1, 'Format')
        self.lc.InsertColumn(2, 'Plot')
        
        self.lc1 = wx.ListCtrl(self.panel, -1, style=wx.LC_REPORT)
        self.lc1.InsertColumn(0, 'IDs')
        
        self.hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox3.Add(self.lc,1, wx.ALIGN_LEFT |wx.ALIGN_CENTER_VERTICAL,2)
        self.hbox3.Add(self.lc1,1, wx.ALIGN_LEFT |wx.ALIGN_CENTER_VERTICAL,2)
        
        self.hbox4 = wx.BoxSizer(wx.HORIZONTAL)      
        self.hbox4.AddSpacer(20)
        self.hbox4.Add(wx.StaticText(self.panel, -1, 'Data To Plot: '),border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox4.Add(wx.Button(self.panel, 14, 'X axis'), border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox4.Add(wx.Button(self.panel, 15, 'Y axis'), border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox4.Add(wx.Button(self.panel, 16, 'Find ID'), border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox4.Add(self.plot_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)       


        self.Bind (wx.EVT_BUTTON, self.OnXSelect, id=14)
        self.Bind (wx.EVT_BUTTON, self.OnYSelect, id=15)
        self.Bind (wx.EVT_BUTTON, self.OnFindID, id=16)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectID, self.lc1)
        
        
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)        
        self.vbox.Add(self.hbox3, 0, flag=wx.EXPAND | wx.TOP)
        self.vbox.Add(self.hbox4, 0, flag=wx.ALIGN_LEFT | wx.TOP)
        self.vbox.Add(self.hbox2, 0, flag=wx.ALIGN_LEFT | wx.TOP)
        self.vbox.Add(self.hbox1, 0, flag=wx.ALIGN_LEFT | wx.TOP)

      
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
        
               
    def create_status_bar(self):
        self.statusbar = self.CreateStatusBar()
        

    def init_plot(self):
        self.dpi = 100
        self.fig = Figure((3.0, 3.0), dpi=self.dpi)

        self.axes = self.fig.add_subplot(111)

        self.axes.set_axis_bgcolor('black')

        
        pylab.setp(self.axes.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes.get_yticklabels(), fontsize=8)

        self.plot_data = self.axes.plot(
            self.data, 
            linewidth=1,
            color=(1, 1, 0),
            )[0]


    def draw_plot(self):
        """ 
        Draws the plot
        """
        if self.filename == None:
            self.flash_status_message("No file loaded in workspace")
            return

        self.axes.clear()
        
        if(self.xaxis):
            xdata = self.data[self.lc.GetItem(self.xaxis-1,0).GetText()]
        else:
            xdata= np.arange(len(self.data))


        if self.xmax_control.is_auto():
            xmax = np.max(xdata) 
        else:
            xmax = int(self.xmax_control.manual_value())
            
        if self.xmin_control.is_auto():            
            xmin =  0;
        else:
            xmin = int(self.xmin_control.manual_value())


        if self.ymin_control.is_auto():
            ymin = 0
        else:
            ymin = int(self.ymin_control.manual_value())
        
        if self.ymax_control.is_auto():
            ymax = 1000
        else:
            ymax = int(self.ymax_control.manual_value())

        self.axes.set_xlim(xmin, xmax)
        self.axes.set_ylim(ymin, ymax)

        
        if self.cb_grid.IsChecked():
            self.axes.grid(True, color='gray')
        else:
            self.axes.grid(False)

        if self.cb_title.IsChecked():
            self.axes.set_title(self.filename, size=12)
        else :  
            self.axes.set_title("")
            
        if self.cb_bg.IsChecked():
            self.axes.set_axis_bgcolor('black')
        else:
            self.axes.set_axis_bgcolor('white')

        pylab.setp(self.axes.get_xticklabels(), visible=self.cb_xlab.IsChecked())
        

        for i in xrange(len(self.yaxis)):
            self.axes.plot(xdata, self.data[self.lc.GetItem(self.yaxis[i],0).GetText()],label=self.lc.GetItem(self.yaxis[i],0).GetText())
        

        if(self.id!=None):
            for i in self.selcted_ids:
                index = self.lc.GetItem(self.id,0).GetText()
                self.axes.plot([xdata[j] for j in xrange(np.size(self.data[index])) if self.data[index][j] == self.lc1.GetItem(i,0).GetText()],
                               [ymax/2 for j in self.data[index] if j == self.lc1.GetItem(i,0).GetText()],'+',
                               label = self.lc1.GetItem(i,0).GetText())
        
        self.axes.legend(bbox_to_anchor=(1., 1), loc=2, borderaxespad=0.,prop={'size':8})
        self.axes.set_xlabel(self.xlabel)
        self.axes.set_ylabel(self.ylabel)

        self.canvas.draw()
 
    """
    Menu functions
    """               
    def on_open_data(self,event):
        self.dirname=os.getcwd()
        file_choices = "Text (*.txt)|*.txt"
        dlg = wx.FileDialog(self, 'Choose a file', self.dirname, '',
                            'TXT files (*.txt)|*.txt|CSV files (*.csv)|*.csv|All files(*.*)|*.*'
                            ,wx.OPEN) 
        if dlg.ShowModal() == wx.ID_OK:
            self.dirname=dlg.GetDirectory() 
            self.filename=os.path.join(self.dirname,dlg.GetFilename()) 
            


            self.file=open(self.filename, 'r') 
            self.datalength = len(next(csv.reader(self.file, delimiter=',')))
            self.flash_status_message("Opened  %s" % self.filename)
            self.open_popupbox_panel()

            
    
    def open_popupbox_panel(self):
        self.parm_popup = PopUpBox(self,"Set Parameters")
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.cb_param=wx.CheckBox(self.parm_popup.panel, -1, "Use First Line", style=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_param, self.cb_param)        
        self.cb_param.SetValue(False) 
        
        self.tc1 = wx.TextCtrl(self.parm_popup.panel, -1)
        self.lb1 = wx.ListBox(self.parm_popup.panel, -1, wx.DefaultPosition, (170, 20), ['String','Int','Float'], wx.LB_SINGLE)
        hbox.AddMany([(self.cb_param, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL),
                            (wx.StaticText(self.parm_popup.panel, -1, 'Parameter'),0, wx.ALIGN_CENTER_VERTICAL),
                            (self.tc1, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
                            (self.lb1,0, wx.ALIGN_CENTER_VERTICAL)])
        
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)      
        hbox1.Add(wx.Button(self.parm_popup.panel, 10, 'Add'), border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        hbox1.Add(wx.Button(self.parm_popup.panel, 11, 'Remove'), border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        hbox1.Add(wx.Button(self.parm_popup.panel, 12, 'Clear'), border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        hbox1.Add(wx.Button(self.parm_popup.panel, 13, 'Load Data'), border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.Bind (wx.EVT_BUTTON, self.OnAdd, id=10)
        self.Bind (wx.EVT_BUTTON, self.OnRemove, id=11)
        self.Bind (wx.EVT_BUTTON, self.OnClear, id=12)
        self.Bind(wx.EVT_LISTBOX, self.OnSelect, self.lb1)
        self.Bind (wx.EVT_BUTTON, self.OnLoadData, id=13)
        self.parm_popup.vbox.Add(hbox, 0, flag=wx.EXPAND | wx.TOP)
        self.parm_popup.vbox.Add(hbox1, 0, flag=wx.EXPAND | wx.TOP)
        self.parm_popup.create_panel()
        self.parm_popup.Show()
    
    
    def auto_set_param(self):
        file = open(self.filename)
        header = file.readline().split(',')
        format=np.genfromtxt(file, delimiter=",")
    
        for h in xrange(len(header)): 
             num_items = self.lc.GetItemCount()
             self.lc.InsertStringItem(num_items, header[h])
             if np.isnan(format[0,h]):
                 self.lc.SetStringItem(num_items, 1, "String")
             else:
                 self.lc.SetStringItem(num_items, 1, "Float")                       
        file.close()
            
           
    def on_save_plot(self, event):
        file_choices = "PNG (*.png)|*.png"
        
        dlg = wx.FileDialog( self, message="Save plot as...", defaultDir=os.getcwd(),
                             defaultFile="plot.png",wildcard=file_choices,style=wx.SAVE)
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.canvas.print_figure(path, dpi=self.dpi)
            self.flash_status_message("Saved to %s" % path)
    
    
    def on_exit(self, event):
        self.Destroy()
        
    def on_edit_label(self,event):
        self.edit_popup_panel()

        
    def edit_popup_panel(self):
        
        def OK(event):
            self.xlabel=x.GetValue()
            self.ylabel=y.GetValue()
            self.draw_plot()         
            label_popup.on_exit(event)
            
        label_popup=PopUpBox(self,"Edit Labels")
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        
        
        x = wx.TextCtrl(label_popup.panel, -1)
        y =wx.TextCtrl(label_popup.panel, -1)
        hbox.AddMany([(wx.StaticText(label_popup.panel, -1, 'X label'),0, wx.ALIGN_CENTER_VERTICAL),
                      (x, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
                      (wx.StaticText(label_popup.panel, -1, 'Y label'),0, wx.ALIGN_CENTER_VERTICAL),
                      (y,0, wx.ALIGN_CENTER_VERTICAL)])
        
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)      
        hbox1.Add(wx.Button(label_popup.panel, 20, 'OK'), border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.Bind(wx.EVT_BUTTON, OK, id=20)

        label_popup.vbox.Add(hbox, 0, flag=wx.EXPAND | wx.TOP)
        label_popup.vbox.Add(hbox1, 0, flag=wx.EXPAND | wx.TOP)
        label_popup.create_panel()
        label_popup.Show()
    
    def flash_status_message(self, msg, flash_len_ms=1500):
        self.statusbar.SetStatusText(msg)
        self.timeroff = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_flash_status_off, self.timeroff)
        self.timeroff.Start(flash_len_ms, oneShot=True)
    
    def on_flash_status_off(self, event):
        self.statusbar.SetStatusText('') 
  
    """
    Button functions
    """

    def OnAdd(self, event):
        if not self.tc1.GetValue():
            return
        num_items = self.lc.GetItemCount()
        self.lc.InsertStringItem(num_items, self.tc1.GetValue())
        self.lc.SetStringItem(num_items, 1, self.format)
        self.tc1.Clear()
        
    def OnRemove(self, event):
        index = self.lc.GetFocusedItem()
        self.lc.DeleteItem(index)

    def OnClear(self, event):
        self.lc.DeleteAllItems()
        self.file.close()
        self.__init__
    
    def OnSelect(self, event):
        index = event.GetSelection()
        self.format = self.lb1.GetString(index)

    def OnLoadData(self,event):
        if self.filename == None:
            self.flash_status_message("No Data File open")
            return
              
        if self.datalength != self.lc.GetItemCount():
            self.flash_status_message("Data has %d columns. Please define all parameters " % self.datalength)
            return
               
        names  =[]
        formats =[]
        for i in xrange(self.datalength):
            names.append(self.lc.GetItem(i,0).GetText())
            formats.append(self.formats_list[self.lc.GetItem(i,1).GetText()])

        dt = np.dtype({'names':names,'formats':formats})
        
        try:
             self.data=np.loadtxt(self.file,dt,delimiter=',')
             self.parm_popup.on_exit(event)
        except:
            self.flash_status_message("Error Loading Data" )
              
    
    def OnXSelect(self,event):
        index = self.lc.GetFocusedItem()
         
        if(self.lc.GetItem(index,2).GetText()!="X axis"):
            self.lc.SetStringItem(index,2,"X axis")
        else:
            self.lc.SetStringItem(index,2,"")
            self.xaxis=None
            return
             
        if(self.xaxis):
            self.lc.SetStringItem(self.xaxis-1,2,"")
         
        self.xaxis=index+1
            
    
    def OnYSelect(self,event):
        index = self.lc.GetFocusedItem()
        if(self.lc.GetItem(index,2).GetText() =="Y axis"):
            self.lc.SetStringItem(index,2,"")
            self.yaxis.remove(index)        
        else:
            self.lc.SetStringItem(index,2,"Y axis")
            self.yaxis.append(index)
            
    
    def OnFindID(self,event):
        self.lc1.DeleteAllItems()
        index = self.lc.GetFocusedItem()
        self.id=index
        unique_id= set(self.data[self.lc.GetItem(index,0).GetText()])
        for i in xrange(len(unique_id)):
            num_items = self.lc1.GetItemCount()
            self.lc1.InsertStringItem(num_items, unique_id.pop())
            
    def OnSelectID(self,event):
        index=self.lc1.GetFocusedItem()
        if (self.selcted_ids.count(index)==0):
            self.selcted_ids.append(index)
        else:
            self.selcted_ids.remove(index) 
    
    def OnPlot(self, event):
         self.draw_plot()
       
    def on_cb_grid(self, event):
        self.draw_plot()
    
    def on_cb_xlab(self, event):
        self.draw_plot()

    def on_cb_title(self, event):
        self.draw_plot()
    
    def on_cb_bg(self,event):
        self.draw_plot()
        
    def on_cb_param(self,event):
        self.tc1.Enable(not self.cb_param.IsChecked())
        self.lb1.Enable(not self.cb_param.IsChecked())
        if self.cb_param.IsChecked():
            self.auto_set_param()
        else:
            self.lc.DeleteAllItems()
 
 



if __name__ == '__main__':
    app = wx.App()
    app.frame = GraphFrame()
    app.frame.Show()
    app.MainLoop()




