import wx
from pubsub.pub import addTopicDefnProvider, TOPIC_TREE_FROM_CLASS

import topic_def
from Engine import Valvolino
from Interface import ValvolinoGUI

addTopicDefnProvider(topic_def, TOPIC_TREE_FROM_CLASS)


if __name__ == '__main__':
    ex = wx.App()
    eng = Valvolino()
    gui = ValvolinoGUI(parent=None, channels=4)
    ex.MainLoop()
