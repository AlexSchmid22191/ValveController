from functools import wraps
from os import name

import wx
from pubsub.pub import subscribe, sendMessage
from serial.tools.list_ports import comports


def in_main_thread(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        wx.CallAfter(func, *args, **kwargs)

    return wrapper


class ValvolinoGUI(wx.Frame):
    def __init__(self, channels, *args, **kwargs):
        super().__init__(title='Valvolino', style=wx.DEFAULT_FRAME_STYLE, *args, **kwargs)

        self.SetIcon(wx.Icon('Icons/Icon.jpg'))

        self.channels = channels

        self.timer = wx.Timer(self)
        self.Bind(event=wx.EVT_TIMER, source=self.timer, handler=self.update)

        if name == 'nt':
            self.SetBackgroundColour('white')

        self.menu_bar = Menubar(style=wx.BORDER_NONE, timer=self.timer)
        self.SetMenuBar(self.menu_bar)
        self.Bind(wx.EVT_MENU, self.on_quit, id=wx.ID_CLOSE)
        self.Bind(wx.EVT_MENU, self.on_connect, source=self.menu_bar.rod_com_menu.connect)

        self.status_bar = wx.StatusBar(parent=self)
        self.SetStatusBar(self.status_bar)
        subscribe(listener=self.set_status, topicName='ETG_status')

        self.valves = []
        if channels == 1:
            sizer = wx.GridSizer(rows=1, cols=1, vgap=0, hgap=0)
        elif channels == 2:
            sizer = wx.GridSizer(rows=1, cols=2, vgap=0, hgap=0)
        else:
            sizer = wx.GridSizer(rows=2, cols=2, vgap=0, hgap=0)

        for channel in range(channels):
            self.valves.append(ValvePanel(parent=self, channel=channel + 1))
            sizer.Add(self.valves[channel], border=5, flag=wx.ALL, proportion=1)

        sizer.Fit(self)
        self.SetSizer(sizer)
        self.SetMinSize(self.GetSize())
        self.Show(True)

    def on_quit(self, *args):
        self.Close()

    @in_main_thread
    def set_status(self, text=''):
        """Display text in status bar, clear status bar after 4 seconds. Can be called from external Thread"""
        self.status_bar.SetStatusText(text)
        wx.CallLater(millis=4000, callableObj=self.status_bar.SetStatusText, text='')

    def update(self, *args):
        """Request data from the engine"""
        sendMessage(topicName='GTE_request_valve_state')

        self.timer.Start(1000)

    def on_connect(self, *args):
        """Start timer for GUI update on serial conection"""
        self.timer.Start(2000)


class ValvePanel(wx.Panel):
    def __init__(self, channel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.channel = channel
        subscribe(topicName='ETG_answer_valve_state', listener=self.update_state)

        self.state_label = wx.StaticText(parent=self, label='Closed')
        self.red_valve_image = wx.Image(name='Icons/Valve_Red.png', type=wx.BITMAP_TYPE_ANY).\
            Scale(width=50, height=50, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
        self.green_valve_image = wx.Image(name='Icons/Valve_Green.png', type=wx.BITMAP_TYPE_ANY).\
            Scale(width=50, height=50, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
        self.valve_icon = wx.StaticBitmap(parent=self, bitmap=self.red_valve_image)

        vboxsizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        vboxsizer.Add(self.state_label, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, proportion=1)
        vboxsizer.Add(self.valve_icon, flag=wx.EXPAND | wx.ALL, proportion=1, border=0)

        self.toggle_button = wx.Button(parent=self, label='Toggle Valve')
        self.toggle_button.Bind(wx.EVT_BUTTON, self.toggle_valve)

        box = wx.StaticBox(parent=self, label='Valve {:1d}'.format(channel))
        boxsizer = wx.StaticBoxSizer(box, orient=wx.VERTICAL)
        boxsizer.Add(self.toggle_button, border=5, flag=wx.ALL | wx.EXPAND)
        boxsizer.Add(vboxsizer, border=5, flag=wx.ALL | wx.EXPAND)

        self.SetSizerAndFit(boxsizer)

    def toggle_valve(self, *args):
        sendMessage(topicName='GTE_toggle_valve', channel=self.channel)

    @in_main_thread
    def update_state(self, channel, state):
        if channel == self.channel:
            if state:
                self.state_label.SetLabel('Open')
                self.valve_icon.SetBitmap(self.green_valve_image)
            else:
                self.state_label.SetLabel('Closed')
                self.valve_icon.SetBitmap(self.red_valve_image)


class Menubar(wx.MenuBar):
    def __init__(self, timer, _=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.port = None
        self.timer = timer

        filemenu = wx.Menu()
        filemenu.Append(item='Quit', id=wx.ID_CLOSE)

        self.rod_com_menu = PortMenu(timer=self.timer)

        self.Append(filemenu, 'File')
        self.Append(self.rod_com_menu, 'Serial Connection')


class PortMenu(wx.Menu):
    def __init__(self, timer):
        super().__init__()

        self.timer = timer

        self.portdict = self.port_dict = {port[1]: port[0] for port in comports()}
        self.portItems = [wx.MenuItem(parentMenu=self, id=wx.ID_ANY, text=port, kind=wx.ITEM_RADIO)
                          for port in list(self.port_dict.keys())]

        for item in self.portItems:
            self.Append(item)

        self.AppendSeparator()

        self.refresh = self.Append(id=wx.ID_ANY, item='Refresh')
        self.connect = self.Append(id=wx.ID_ANY, item='Connect', kind=wx.ITEM_CHECK)
        self.Bind(event=wx.EVT_MENU, handler=self.on_connect, source=self.connect)

    def on_connect(self, source):
        if source.IsChecked():
            for item in self.portItems:
                if item.IsChecked():
                    sendMessage(topicName='GTE_connect', port=self.port_dict[item.GetItemLabelText()])
                    source.Skip()

        else:
            self.timer.Stop()
            sendMessage(topicName='GTE_disconnect')
