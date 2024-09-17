import wx

class SimpleInputTest(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='wxPython Input Test')
        panel = wx.Panel(self)
        
        self.text_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        
        button = wx.Button(panel, label='Print Content')
        button.Bind(wx.EVT_BUTTON, self.print_content)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.Show()

    def print_content(self, event):
        content = self.text_ctrl.GetValue()
        print("Text content:", repr(content))

if __name__ == '__main__':
    app = wx.App()
    frame = SimpleInputTest()
    app.MainLoop()