import tkinter as tk
import numpy as np
from pyproj import Proj, transform
from image_download import run as download
import cv2
from PIL import ImageTk, Image

class Line:
    def __init__(self, map, path = None):
        self.longitudes = []
        self.latitudes = []
        self.line_id = None
        self.line_id0 = None
        self.line_id1 = None
        self.line_id2 = None
        self.line_id3 = None
        self.line_id4 = None
        self.map = map
        self.canvas = map.map_canvas
        self.northernmost = self.map.northernmost_lat
        self.southernmost = self.map.southernmost_lat
        self.easternmost = self.map.easternmost_lon
        self.westernmost = self.map.westernmost_lon
        self.display = None
        self.path = path

    def update_borders(self):
        self.northernmost = self.map.northernmost_lat
        self.southernmost = self.map.southernmost_lat
        self.easternmost = self.map.easternmost_lon
        self.westernmost = self.map.westernmost_lon

    def append(self, longitude, latitude):
        self.longitudes.append(longitude)
        self.latitudes.append(latitude)

    def undo(self):
        del self.longitudes[-1]
        del self.latitudes[-1]

    def transfer(self):
        self.update_borders()
        coords_x = ((np.array(self.longitudes) - self.westernmost) / (
                self.easternmost - self.westernmost)) * self.canvas.winfo_width()
        coords_y = (1 - ((np.array(self.latitudes) - self.southernmost) / (
                self.northernmost - self.southernmost))) * self.canvas.winfo_height()
        coords = []
        for i in range(len(coords_y)):
            coords.append(int(coords_x[i]))
            coords.append(int(coords_y[i]))

        self.canvas.coords(self.line_id, coords)
        if self.line_id0:
            self.canvas.coords(self.line_id0, coords)
            self.canvas.tag_raise(self.line_id0)
        if self.line_id1:
            self.canvas.coords(self.line_id1, coords)
            self.canvas.tag_raise(self.line_id1)
        if self.line_id2:
            self.canvas.coords(self.line_id2, coords)
            self.canvas.tag_raise(self.line_id2)
        if self.line_id3:
            self.canvas.coords(self.line_id3, coords)
            self.canvas.tag_raise(self.line_id3)
        if self.line_id4:
            self.canvas.coords(self.line_id4, coords)
            self.canvas.tag_raise(self.line_id4)


    def visualise(self, layer = None, style = "default", dots = 0, canvas = "app"):
        self.display = True
        self.update_borders()
        coords_x = ((np.array(self.longitudes) - self.westernmost) / (
                self.easternmost - self.westernmost)) * self.canvas.winfo_width()
        coords_y = (1 - ((np.array(self.latitudes) - self.southernmost) / (
                self.northernmost - self.southernmost))) * self.canvas.winfo_height()
        coords = []
        for i in range(len(coords_y)):
            coords.append(int(coords_x[i]))
            coords.append(int(coords_y[i]))
        if style == "progress":
            color = "#FFFF00"
        else:
            color = "#FF0000"
        #print(coords)
        if len(coords) > 3:
            if self.path == None:
                self.line_id = self.canvas.create_line(coords, fill= color,width = 2)
            elif self.path == "Dual motorway":
                if layer == 0:
                    if canvas == "pdf":
                        pass
                    else:
                        self.line_id0 = self.canvas.create_line(coords, fill = "#822828", width = 2*1.65*2**self.map.zoom_level)
                if layer == 1:
                    self.line_id1 = self.canvas.create_line(coords, fill = "#af494b", width = 2*1.5*2**self.map.zoom_level)
                if layer == 2:
                    self.line_id2 = self.canvas.create_line(coords, fill="#822828", width=2*0.3*2**self.map.zoom_level)
            elif self.path == "Major road":
                if layer == 0:
                    self.line_id0 = self.canvas.create_line(coords, fill = "#822828", width = 2*1*2**self.map.zoom_level)
                if layer == 1:
                    self.line_id1 = self.canvas.create_line(coords, fill = "#af494b", width = 2*0.85*2**self.map.zoom_level)
            elif self.path == "Minor road":
                if layer == 0:
                    self.line_id0 = self.canvas.create_line(coords, fill = "#822828", width = 2*0.6*2**self.map.zoom_level)
                if layer == 1:
                    self.line_id1 = self.canvas.create_line(coords, fill = "#af494b", width = 2*0.45*2**self.map.zoom_level)
            elif self.path == "Major road, loose":
                if layer == 0:
                    self.line_id0 = self.canvas.create_line(coords, fill="#000000",
                                                            width=2 * 1 * 2 ** self.map.zoom_level)
                if layer == 1:
                    self.line_id1 = self.canvas.create_line(coords, fill="#FFFFFF",
                                                            width=2 * 0.80 * 2 ** self.map.zoom_level)
                if layer == 2:
                    dash =  (int(10* 2 ** self.map.zoom_level),int(15* 2 ** self.map.zoom_level))
                    if dash[0] > 255 or dash[1] > 255:
                        dash = (255, 255)
                    self.line_id2 = self.canvas.create_line(coords, fill="#af494b",
                                                            width=2 * 0.80 * 2 ** self.map.zoom_level,
                                                            dash =dash)
            elif self.path == "Minor road, loose":
                if layer == 0:
                    self.line_id0 = self.canvas.create_line(coords, fill="#000000",
                                                            width=2 * 0.6 * 2 ** self.map.zoom_level)
                if layer == 1:
                    self.line_id1 = self.canvas.create_line(coords, fill="#FFFFFF",
                                                            width=2 * 0.45 * 2 ** self.map.zoom_level)
                if layer == 2:
                    dash =  (int(10 * 2 ** self.map.zoom_level), int(15 * 2 ** self.map.zoom_level))
                    if dash[0] > 255 or dash[1] > 255:
                        dash = (255, 255)
                    self.line_id2 = self.canvas.create_line(coords, fill="#af494b",
                                                            width=2 * 0.45 * 2 ** self.map.zoom_level, dash=dash)
            elif self.path == "Light duty road, gravel":
                if layer == 0:
                    self.line_id0 = self.canvas.create_line(coords, fill="#000000",
                                                            width=2 * 0.6 * 2 ** self.map.zoom_level)
                if layer == 1:
                    self.line_id1 = self.canvas.create_line(coords, fill="#FFFFFF",
                                                            width=2 * 0.45 * 2 ** self.map.zoom_level)
                if layer == 2:
                    dash = (int(10 * 2 ** self.map.zoom_level), int(15 * 2 ** self.map.zoom_level))
                    if dash[0] > 255 or dash[1] > 255:
                        dash = (255, 255)
                    self.line_id2 = self.canvas.create_line(coords, fill="#AAAAAA",
                                                            width=2 * 0.45 * 2 ** self.map.zoom_level,
                                                            dash = dash)
            elif self.path == "Unimproved road":
                dash = (
                    int(7 * 2 ** self.map.zoom_level),
                    int(10 * 2 ** self.map.zoom_level))
                if dash[0] > 255 or dash[1] > 255:
                    dash = (255,255)
                if layer == 0:
                    self.line_id0 = self.canvas.create_line(coords, fill="#000000",
                                                            width=2 * 0.5 * 2 ** self.map.zoom_level,
                                                            dash = dash)
                if layer == 1:
                    self.line_id1 = self.canvas.create_line(coords, fill="#FFFFFF",
                                                            width=2 * 0.37 * 2 ** self.map.zoom_level)
            elif self.path == "4WD road":
                if layer == 0:
                    self.line_id0 = self.canvas.create_line(coords, fill="#AAAAAA",
                                                            width=2 * 0.4 * 2 ** self.map.zoom_level)
            elif self.path == "Trail":
                if layer == 0:
                    dash = (
                        int(10 * 2 ** self.map.zoom_level),
                        int(10 * 2 ** self.map.zoom_level))
                    if dash[0] > 255 or dash[1] > 255:
                        dash = (255, 255)
                    self.line_id0 = self.canvas.create_line(coords, fill="#000000",
                                                            width=2 * 0.3 * 2 ** self.map.zoom_level, dash = dash)
            elif self.path == "Trail (small)":
                if layer == 0:
                    dash = (int(10 * 2 ** self.map.zoom_level),
                        int(5 * 2 ** self.map.zoom_level),
                        int(5 * 2 ** self.map.zoom_level),
                        int(5 * 2 ** self.map.zoom_level))
                    if dash[0] > 255 or dash[1] > 255 or dash[2] > 255 or dash[3] > 255:
                        dash = (255, 150, 150, 150)
                    self.line_id0 = self.canvas.create_line(coords, fill="#000000",
                                                            width=2 * 0.15 * 2 ** self.map.zoom_level, dash = dash)
            elif self.path == "River":
                if layer == 0:
                    self.line_id0 = self.canvas.create_line(coords, fill="#00b4c8",
                                                            width=2 * 3.3 * 2 ** self.map.zoom_level)
                if layer == 1:
                    self.line_id1 = self.canvas.create_line(coords, fill="#eaf6fa",
                                                            width=2 * 3.1 * 2 ** self.map.zoom_level)
            elif self.path == "Stream":
                if layer == 0:
                    self.line_id0 = self.canvas.create_line(coords, fill="#00b4c8",
                                                            width=2 * 0.3 * 2 ** self.map.zoom_level)
            elif self.path == "Powerline":
                if layer == 2:
                    self.line_id2 = self.canvas.create_line(coords, fill="#000000",
                                                            width=2 * 0.15 * 2 ** self.map.zoom_level)
                if layer == 3:
                    self.dots = []
                    for i in range(len(coords_y) - 1):
                        radius =  2*0.3*2**self.map.zoom_level
                        dot = self.canvas.create_oval(
                            [coords_x[i] - (radius + 1), coords_y[i] - (radius + 1), coords_x[i] + radius,
                             coords_y[i] + radius], fill="#000000")
                        self.dots.append(dot)

        if style == "progress":
            self.dots = []
            for i in range(len(coords_y)-1):
                radius = 3
                dot = self.canvas.create_oval([coords_x[i]-(radius+1),coords_y[i]-(radius+1),coords_x[i]+radius,coords_y[i]+radius], fill = "#FF0000")
                self.dots.append(dot)
            i = -1
            radius = 3
            dot = self.canvas.create_oval(
                [coords_x[i] - (radius + 1), coords_y[i] - (radius + 1), coords_x[i] + radius, coords_y[i] + radius],
                fill="#0000FF")
            self.dots.append(dot)


    def hide(self):
        self.display = False
        self.canvas.delete(self.line_id)
        try:
            self.canvas.delete(self.line_id0)
        except:
            pass
        try:
            self.canvas.delete(self.line_id1)
        except:
            pass
        try:
            self.canvas.delete(self.line_id2)
        except:
            pass
        try:
            self.canvas.delete(self.line_id3)
        except:
            pass
        try:
            self.canvas.delete(self.line_id4)
        except:
            pass
        try:
            if self.dots:
                for i in self.dots:
                    self.canvas.delete(i)
        except:
            pass

    def delete(self):
        self.hide()
        initial_length = len(self.map.lines)
        for i in range(initial_length):
            if self.map.lines[initial_length-i-1]:
                if self.map.lines[initial_length-i-1].line_id == self.line_id or self.map.lines[initial_length-i-1].line_id == self.line_id0 or self.map.lines[initial_length-i-1].line_id == self.line_id1 or self.map.lines[initial_length-i-1].line_id == self.line_id2 or self.map.lines[initial_length-i-1].line_id == self.line_id3 or self.map.lines[initial_length-i-1].line_id == self.line_id4:
                    self.map.lines[initial_length-i-1] = None

        try:
            if self.dots:
                for i in self.dots:
                    self.canvas.delete(i)
        except:
            pass
        self.map.display_aerial(afterzoom=True, last_call=self.map.last_call)

class Polygon:
    def __init__(self, map, fill, outline = False):
        self.map = map
        self.longitudes = []
        self.latitudes = []
        self.line_id = None
        self.outline = outline
        self.fill = fill
        self.northernmost = self.map.northernmost_lat
        self.southernmost = self.map.southernmost_lat
        self.easternmost = self.map.easternmost_lon
        self.westernmost = self.map.westernmost_lon
        self.display = None


    def update_borders(self):
        self.northernmost = self.map.northernmost_lat
        self.southernmost = self.map.southernmost_lat
        self.easternmost = self.map.easternmost_lon
        self.westernmost = self.map.westernmost_lon

    def append(self, longitude, latitude):
        self.longitudes.append(longitude)
        self.latitudes.append(latitude)

    def undo(self):
        del self.latitudes[-1]
        del self.longitudes[-1]

    def visualise(self, style = "default"):
        self.display = True
        self.update_borders()
        coords_x = ((np.array(self.longitudes) - self.westernmost) / (
                self.easternmost - self.westernmost)) * self.map.map_canvas.winfo_width()
        coords_y = (1 - ((np.array(self.latitudes) - self.southernmost) / (
                self.northernmost - self.southernmost))) * self.map.map_canvas.winfo_height()
        coords = []
        for i in range(len(coords_y)):
            coords.append(int(coords_x[i]))
            coords.append(int(coords_y[i]))
        try:
            if style == "progress":
                self.line_id = self.map.map_canvas.create_polygon(coords, outline = "#FFFF00",fill="")
            else:
                self.line_id = self.map.map_canvas.create_polygon(coords, fill=self.fill)
                if self.outline:
                    self.line_id0 = self.map.map_canvas.create_line(coords+[coords[0],coords[1]], fill=self.outline[0],
                                                                width=2 * self.outline[1] * 2 ** self.map.zoom_level)
        except Exception as e:
            print(e)
        if style == "progress":
            self.dots = []
            for i in range(len(coords_y)-1):
                dot = self.map.map_canvas.create_oval([coords_x[i]-3,coords_y[i]-3,coords_x[i]+2,coords_y[i]+2], fill = "#FF0000")
                self.dots.append(dot)
            i = -1
            dot = self.map.map_canvas.create_oval([coords_x[i] - 3, coords_y[i] - 3, coords_x[i] + 2, coords_y[i] + 2],
                                                  fill="#0000FF")
            self.dots.append(dot)

    def hide(self):
        self.display = False
        self.map.map_canvas.delete(self.line_id)
        try:
            self.map.map_canvas.delete(self.line_id0)
        except:
            pass
        try:
            if self.dots:
                for i in self.dots:
                    self.map.map_canvas.delete(i)
        except:
            pass

    def delete(self):
        self.hide()
        initial_length = len(self.map.polygons)
        for i in range(initial_length):
            if self.map.polygons[initial_length-i-1]:
                if self.map.polygons[initial_length-i-1].line_id == self.line_id:
                    self.map.polygons[initial_length-i-1] = None
        try:
            if self.dots:
                for i in self.dots:
                    self.map.map_canvas.delete(i)
        except:
            pass
        self.map.display_aerial(afterzoom=True, last_call=self.map.last_call)


class Contour:
    def __init__(self, map, coords, width = 1):
        self.longitudes = []
        self.latitudes = []
        for i in coords:
            self.longitudes.append(i[0])
            self.latitudes.append(i[1])
        self.line_id = None
        self.map = map
        self.canvas = map.map_canvas
        self.northernmost = self.map.northernmost_lat
        self.southernmost = self.map.southernmost_lat
        self.easternmost = self.map.easternmost_lon
        self.westernmost = self.map.westernmost_lon

        self.width = width

        self.display = None

    def update_borders(self):
        self.northernmost = self.map.northernmost_lat
        self.southernmost = self.map.southernmost_lat
        self.easternmost = self.map.easternmost_lon
        self.westernmost = self.map.westernmost_lon

    def append(self, longitude, latitude):
        self.longitudes.append(longitude)
        self.latitudes.append(latitude)

    def visualise(self):
        self.display = True
        self.update_borders()
        coords_x = ((np.array(self.longitudes) - self.westernmost) / (
                self.easternmost - self.westernmost)) * self.canvas.winfo_width()
        coords_y = (1 - ((np.array(self.latitudes) - self.southernmost) / (
                self.northernmost - self.southernmost))) * self.canvas.winfo_height()
        coords = []
        for i in range(len(coords_y)):
            coords.append(int(coords_x[i]))
            coords.append(int(coords_y[i]))

        self.line_id = self.canvas.create_line(coords, fill='#B55431', width=self.width)

    def hide(self):
        self.display = False
        self.canvas.delete(self.line_id)

    def delete(self):
        self.hide()
        self.canvas.delete(self.line_id)
        for i in range(len(self.map.lines)):
            if self.map.lines[i].line_id == self.line_id:
                del self.map.lines[i]

class Grid:
    def __init__(self, map, spacing_seconds = 36, coordinate="geographic", labels=True):
        self.map = map
        self.coordinate = coordinate
        self.labels = labels
        self.spacing = spacing_seconds/3600
        self.display = None

    def update_borders(self):
        self.northernmost = self.map.northernmost_lat
        self.southernmost = self.map.southernmost_lat
        self.easternmost = self.map.easternmost_lon
        self.westernmost = self.map.westernmost_lon

    def visualise(self):
        self.display = True
        self.update_borders()
        if self.coordinate == "geographic":
            remainder_lon = self.westernmost % self.spacing
            non_remainder_lon = self.spacing-remainder_lon
            first_lon = self.westernmost + non_remainder_lon
            lons = []
            i = first_lon
            while i <= self.easternmost:
                lons.append(i)
                i += self.spacing

            remainder_lat = self.southernmost % self.spacing
            non_remainder_lat = self.spacing-remainder_lat
            first_lat = self.southernmost + non_remainder_lat
            lats = []
            i = first_lat
            while i <= self.northernmost:
                lats.append(i)
                i += self.spacing

            longitudes = []
            for i in lats:
                longitudes.append([self.easternmost,i,self.westernmost,i])

            latitudes = []
            for i in lons:
                latitudes.append([i,self.northernmost,i,self.southernmost])


            self.grid_ids = []
            for i in longitudes:
                line = self.map.map_canvas.create_line(self.map.gps2pixels(i[0],0),
                                                self.map.gps2pixels(i[1],1),
                                                self.map.gps2pixels(i[2],0),
                                                self.map.gps2pixels(i[3],1),
                                                fill = "blue")



                self.grid_ids.append(line)

            for i in latitudes:
                line = self.map.map_canvas.create_line(self.map.gps2pixels(i[0], 0),
                                                       self.map.gps2pixels(i[1], 1),
                                                       self.map.gps2pixels(i[2], 0),
                                                       self.map.gps2pixels(i[3], 1),
                                                       fill="blue")

                self.grid_ids.append(line)

    def hide(self):
        self.display = False
        for i in self.grid_ids:
            self.map.map_canvas.delete(i)

    def delete(self):
        self.hide()
        self.grid_ids = []


class AerialImage:
    def __init__(self, parentmap,  north, south, east, west, zoom):
        self.north = north
        self.south = south
        self.east = east
        self.west = west
        self.zoom = zoom
        self.parentmap = parentmap
        self.image = download(north=north, south=south, east=east, west=west, zoom=zoom)

    def display(self):
        height, width, channels = self.image.shape
        print(width, height)
        width_ratio = (self.parentmap.map_canvas.winfo_width()/width)*(self.east - self.west) / (self.parentmap.easternmost_lon - self.parentmap.westernmost_lon)
        height_ratio = (self.parentmap.map_canvas.winfo_height()/height)*(self.north - self.south) / (self.parentmap.northernmost_lat - self.parentmap.southernmost_lat)
        new_width = int(width * width_ratio)
        new_height = int(height * height_ratio)
        print(width, height, width_ratio, height_ratio)

        img_rgb = cv2.resize(cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB), (
            new_width, new_height))
        self.img_pil = Image.fromarray(img_rgb)


        left = new_width * (self.parentmap.westernmost_lon - self.west) / (self.east - self.west)
        upper = new_height * (self.north - self.parentmap.northernmost_lat) / (self.north - self.south)
        right = new_width
        lower = new_height
        cropped = self.img_pil.crop((left, upper, right, lower))
        x = 0
        y = 0
        self.tk_image = ImageTk.PhotoImage(cropped)
        self.parentmap.map_canvas.create_image(x, y, anchor=tk.NW, image=self.tk_image)
