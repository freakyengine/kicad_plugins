# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.9.0 Jul 11 2020)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class TrackArcGeneratorParameterDialog
###########################################################################

class TrackArcGeneratorParameterDialog ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 190,196 ), style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( -1, -1 )

        bSizer1 = wx.BoxSizer( wx.VERTICAL )

        self.label_radius = wx.StaticText( self, wx.ID_ANY, u"Arc radius in µm", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.label_radius.Wrap( -1 )

        bSizer1.Add( self.label_radius, 0, wx.ALL, 5 )

        self.input_radius = wx.TextCtrl( self, wx.ID_ANY, u"3000", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer1.Add( self.input_radius, 0, wx.ALL, 5 )

        self.label_arc_segments = wx.StaticText( self, wx.ID_ANY, u"Track segments per circle", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.label_arc_segments.Wrap( -1 )

        bSizer1.Add( self.label_arc_segments, 0, wx.ALL, 5 )

        self.input_segments = wx.TextCtrl( self, wx.ID_ANY, u"60", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer1.Add( self.input_segments, 0, wx.ALL, 5 )

        self.buttom_okay = wx.Button( self, wx.ID_OK, u"Okay", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer1.Add( self.buttom_okay, 0, wx.ALL, 5 )


        self.SetSizer( bSizer1 )
        self.Layout()

        self.Centre( wx.BOTH )

    def __del__( self ):
        pass


