import math
import pcbnew
import os
import wx
from .track_arc_generator_parameter_dialog import TrackArcGeneratorParameterDialog

class TrackArcGenerator(pcbnew.ActionPlugin):
    
    def defaults(self):
        self.name = "Track Arc Generator"
        self.category = "RF Toolbox"
        self.description = "Generates arc tracks out of random, non parallel track segments"
        self.show_toolbar_button = True # Optional, defaults to False
        #self.icon_file_name = os.path.join(os.path.dirname(__file__), 'icon.png') # Optional
    
    def Run(self):
        
        board = pcbnew.GetBoard()

        tracks_selected = []

        for track in board.GetTracks():
            if track.IsSelected():
                tracks_selected.append(track)

        
        if len(tracks_selected) != 2:
            msg = "Please select exact two tracks to create an arc."
            wx.MessageBox(msg, 'Error', wx.OK | wx.ICON_ERROR)
            return -1
        
        # create parameter dialog (defaults hardcoded in wx python script)
        parameter_dialog = TrackArcGeneratorParameterDialog(None)
        button_result = parameter_dialog.ShowModal()
        
        # get values from parameter dialog
        arc_radius = float(parameter_dialog.input_radius.GetValue()) * 1000
        n_circle_segments = float(parameter_dialog.input_segments.GetValue())
        
        # destroy dialog handle
        parameter_dialog.Destroy()
        
        if button_result == wx.ID_OK:
            
            # track coordinates: [ [start_x, start_y], [end_x, end_y] ]
            track0 = [ [tracks_selected[0].GetStart().x, tracks_selected[0].GetStart().y], [tracks_selected[0].GetEnd().x, tracks_selected[0].GetEnd().y] ]
            track1 = [ [tracks_selected[1].GetStart().x, tracks_selected[1].GetStart().y], [tracks_selected[1].GetEnd().x, tracks_selected[1].GetEnd().y] ]

            track0_dist_to_intersect, track1_dist_to_intersect = self.calculate_line_intersect_point(track0, track1)

            # if intersect point is on origin or behind, change origin to far end point
            if track0_dist_to_intersect <= 0:
                track0 = [ [tracks_selected[0].GetEnd().x, tracks_selected[0].GetEnd().y], [tracks_selected[0].GetStart().x, tracks_selected[0].GetStart().y] ]
               
            if track1_dist_to_intersect <= 0:
                track1 = [ [tracks_selected[1].GetEnd().x, tracks_selected[1].GetEnd().y], [tracks_selected[1].GetStart().x, tracks_selected[1].GetStart().y] ]

            track0_dist_to_intersect, track1_dist_to_intersect = self.calculate_line_intersect_point(track0, track1)

            # normalize lines based on confirmed far end origin
            track0_orig, track0_dir, track0_phi, track0_len = self.twopointline_to_orig_dir_len(track0)
            track1_orig, track1_dir, track1_phi, track1_len = self.twopointline_to_orig_dir_len(track1)

            track0_dist_to_intersect = track0_dist_to_intersect * track0_len
            track1_dist_to_intersect = track1_dist_to_intersect * track1_len

            # calc arc angle
            arc_angle = math.pi - self.calc_intersect_angle(track0_dir, track1_dir)

            # construct first arc
            arc, segments_to_draw = self.construct_unit_arc(arc_angle, n_circle_segments, 0)

            # get arc end segment direction for side decision
            arc_end_orig, arc_end_dir, arc_end_phi, arc_end_len = self.twopointline_to_orig_dir_len([ arc[-2], arc[-1] ])

            # rotate it to target angle
            arc_end_dir = self.calc_coordinate_rotation(arc_end_dir, track0_phi)

            # get intersect angle and check
            arc_end_intersect_angle = self.calc_intersect_angle(arc_end_dir, track1_dir)
            
            if arc_end_intersect_angle < (math.pi*3/4):
                arc, segments_to_draw = self.construct_unit_arc(arc_angle, n_circle_segments, 1)
               

            # rotate, scale and move to position relative to track0 origin
            for segment in range(0, segments_to_draw+1):
                # scale
                arc[segment][0] = arc[segment][0] * arc_radius
                arc[segment][1] = arc[segment][1] * arc_radius
                # rotate
                arc[segment] = self.calc_coordinate_rotation(arc[segment], track0_phi)
                # place
                rounding_backoff_dist = arc_radius * math.tan(arc_angle/2)
                arc[segment][0] = round( arc[segment][0] + track0_orig[0] + (track0_dist_to_intersect-rounding_backoff_dist) * track0_dir[0] )
                arc[segment][1] = round( arc[segment][1] + track0_orig[1] + (track0_dist_to_intersect-rounding_backoff_dist) * track0_dir[1] )

            # store information from old track and remove them
            track_width = tracks_selected[0].GetWidth()
            track_net = tracks_selected[0].GetNet()
            track_layer = tracks_selected[0].GetLayer()
            tracks_selected[0].DeleteStructure()
            tracks_selected[1].DeleteStructure()

            # add track segments according to coordinates

            # track0 origin to begin of arc
            track = pcbnew.TRACK(board)
            track.SetStart(pcbnew.wxPoint(track0_orig[0], track0_orig[1]))
            track.SetEnd(pcbnew.wxPoint(arc[0][0], arc[0][1]))
            track.SetWidth(track_width)
            track.SetLayer(track_layer)
            track.SetNet(track_net)
            board.Add(track)

            # track1 origin to end of arc
            track = pcbnew.TRACK(board)
            track.SetStart(pcbnew.wxPoint(track1_orig[0], track1_orig[1]))
            track.SetEnd(pcbnew.wxPoint(arc[-1][0], arc[-1][1]))
            track.SetWidth(track_width)
            track.SetLayer(track_layer)
            track.SetNet(track_net)
            board.Add(track)

            # arc segments
            for segment in range(0, segments_to_draw):
                track = pcbnew.TRACK(board)
                track.SetStart(pcbnew.wxPoint(arc[segment][0], arc[segment][1]))
                track.SetEnd(pcbnew.wxPoint(arc[segment+1][0], arc[segment+1][1]))
                track.SetWidth(track_width)
                track.SetLayer(track_layer)
                track.SetNet(track_net)
                board.Add(track)

            # update board
            pcbnew.Refresh()

            return 0
            
        else:
            return 0

    ## ---- functions ----

    def calculate_line_intersect_point(self, line0, line1):
        # INPUTS: line coordinates, format [ [start_x, start_y], [end_x, end_y] ]
        # RETURNS: u distance to intersect from (x1,y1), v distance to intersect from (x3,y3)
       
        # MATH follows here :P
        # taken from: https://en.wikipedia.org/wiki/Line%E2%80%93line_intersection
        # Line0 = (x1,y1) to (x2,y2)
        # Line1 = (x3,y3) to (x4,y4)
       
        x1 = line0[0][0]
        y1 = line0[0][1]
        x2 = line0[1][0]
        y2 = line0[1][1]
       
        x3 = line1[0][0]
        y3 = line1[0][1]
        x4 = line1[1][0]
        y4 = line1[1][1]
       
        u = ( (x1-x3)*(y3-y4)-(y1-y3)*(x3-x4) )/( (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4) )
        v = ( (x1-x2)*(y1-y3)-(y1-y2)*(x1-x3) )/( (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4) ) * (-1)
       
        return u,v

    def twopointline_to_orig_dir_len(self, line):
        # INPUTS: line coordinates, format [ [start_x, start_y], [end_x, end_y] ]
        # RETURNS: origin[x, y], direction[x, y]

        import math

        line_length = math.sqrt( math.pow((line[1][0]-line[0][0]),2) + math.pow((line[1][1]-line[0][1]),2) )

        origin = [ line[0][0], line[0][1] ]
        direction_xy = [ (line[1][0]-line[0][0])/line_length, (line[1][1]-line[0][1])/line_length ]
        direction_phi = math.atan2(direction_xy[1],direction_xy[0])
       
        return origin, direction_xy, direction_phi, line_length

    def calc_intersect_angle(self, dir0, dir1):
        # INPUTS: two normalized direction vectors, format [x, y]
        # RETURNS: intersect_angle
       
        import math
       
        return math.acos(dir0[0]*dir1[0] + dir0[1]*dir1[1])

    def calc_coordinate_rotation(self, point, angle):
        # INPUTS: point, format [x, y] coordinates, angle in radians
        # RETURNS: rotated coordinates [x, y]
       
        import math
       
        return [ point[0] * math.cos(angle) - point[1] * math.sin(angle), point[0] * math.sin(angle) + point[1] * math.cos(angle) ]

    def construct_unit_arc(self, arc_angle, circle_segments, direction_downwards):
        # INPUTS: arc_angle in radians, circle_segments as number, direction_downwards as true/false
        # RETURNS: arc segments in format [segment_count][x, y], segment_count
       
        import math
       
        segment_count = int( math.ceil( circle_segments * (arc_angle/(2*math.pi)) ) )
        segment_angle = arc_angle / segment_count
        
        if direction_downwards == 0:
            direction_multiplier = 1
        else:
            direction_multiplier = -1
       
        arc = []
        for segment in range(0, segment_count+1):
            dx = math.sin(segment*segment_angle)
            dy = ( 1 - math.cos(segment*segment_angle) ) * direction_multiplier
            arc.append([dx, dy])
           
        return arc, segment_count


