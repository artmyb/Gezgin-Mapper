from image_download import run as download
import cv2
import os
import tkinter as tk
from tkinter import ttk, colorchooser
from PIL import ImageTk, Image
from functools import partial
import numpy as np
from my_gui import LayerContainer
from graphic_objects import Line, Polygon, Contour, Grid, AerialImage
from pyhigh import get_elevation, get_elevation_batch, clear_cache
from elevation_plot import process_contour, elevation, process_shading
import threading
import time
"""
north = 39.907540
south = 39.895835
east = 32.777946
west = 32.764809
zoom = 16

image = download(north = north, south = south, east = east, west = west, zoom = zoom)

cv2.imwrite("image"+".png",image)
"""


class Map:
    def __init__(self, root):
        self.root = tk.Toplevel(root)
        self.root.title("Gezgin")
        self.root.state("zoomed")
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.icon_image = Image.open("images/OpenTopoMapperIcon.png")
        self.icon_photo = ImageTk.PhotoImage(self.icon_image)
        self.root.iconphoto(False, self.icon_photo)

        self.menubar = tk.Menu(self.root)

        self.filemenu = tk.Menu(self.menubar, tearoff = 0)
        self.filemenu.add_command(label="New Map", command = self.new_instance)
        self.menubar.add_cascade(label = "File", menu = self.filemenu)

        self.optionsmenu = tk.Menu(self.menubar, tearoff = 0)
        self.optionsmenu.add_command(label="Map settings", command = self.map_settings)
        self.menubar.add_cascade(label = "Settings", menu = self.optionsmenu)

        self.root.config(menu = self.menubar)


        self.top_frame = tk.Frame(self.root,height = 30)
        self.top_frame.pack()
        self.separator1 = ttk.Separator(self.root, orient='horizontal')
        self.separator1.pack(fill='x', pady=0)

        tk.Button(self.top_frame, text = '◀', command=self.to_left).pack(side= tk.LEFT)
        tk.Button(self.top_frame, text='▶', command=self.to_right).pack(side=tk.LEFT)
        tk.Button(self.top_frame, text='▲', command=self.to_up).pack(side=tk.LEFT)
        tk.Button(self.top_frame, text='▼', command=self.to_down).pack(side=tk.LEFT)
        tk.Button(self.top_frame, text="+", command = partial(self.zoom, 1)).pack(side=tk.LEFT)
        tk.Button(self.top_frame, text="-", command=partial(self.zoom, -1)).pack(side=tk.LEFT)
        self.create_line_button = tk.Button(self.top_frame, text= "Create Linear Feature", command= self.create_line)
        self.create_line_button.pack(side= tk.LEFT, padx = 5)
        self.create_polygon_button = tk.Button(self.top_frame, text="Create Polygon", command=self.create_polygon)
        self.create_polygon_button.pack(side=tk.LEFT, padx=5)

        self.export_button = tk.Button(self.top_frame, text="Export Map", command=self.export)
        self.export_button.pack(side=tk.LEFT, padx=5)

        self.undo_button = tk.Button(self.top_frame, text = "↺", command = self.undo)
        self.undo_button.pack(side=tk.LEFT, padx = 5)

        class ScrollableFrame(ttk.Frame):
            def __init__(self, container, *args, **kwargs):
                super().__init__(container, *args, **kwargs)

                # Create a canvas inside the scrollable frame
                self.canvas = tk.Canvas(self, width = 200)
                self.scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
                self.scrollbar2 = ttk.Scrollbar(container, orient="horizontal", command=self.canvas.xview)
                # Create an inner frame to hold the widgets and attach it to the canvas
                self.scrollable_frame = ttk.Frame(self.canvas)
                self.scrollable_frame.bind(
                    "<Configure>",
                    lambda e: self.canvas.configure(
                        scrollregion=self.canvas.bbox("all")
                    )
                )

                # Attach the inner frame to the canvas window
                self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

                # Configure the canvas to work with the scrollbar
                self.canvas.configure(yscrollcommand=self.scrollbar.set)
                self.canvas.configure(xscrollcommand=self.scrollbar2.set)

                # Pack the canvas and scrollbar to fill the entire height
                self.canvas.pack(side="left", fill="both", expand=True)
                self.scrollbar.pack(side="right", fill="y")
                self.scrollbar2.pack(side="bottom", fill="x")

                self.pack(fill="both", expand=True)
            def add_widget(self, widget):
                """Method to add a widget to the scrollable frame."""
                widget.pack(pady=10, padx=10)

        self.left_frame = ttk.Frame(self.root)
        self.left_frame.pack(side=tk.LEFT, fill='y')
        tk.Label(self.left_frame, text="Map Objects").pack(anchor = "w")
        self.scrollable_container_left = ScrollableFrame(self.left_frame)
        self.scrollable_container_left.pack(fill="both", expand=True)



        # Add multiple labels to the scrollable frame
        """
        for i in range(50):
            tk.Label(self.scrollable_container_left.scrollable_frame, text=f"Label {i}").pack()
        """

        self.aerial_image_on = True


        self.grids = LayerContainer(self.scrollable_container_left.scrollable_frame, text = "Grids", settings = self.grid_settings)
        self.geographic = LayerContainer(self.grids, text = "Geographic coordinates")
        self.geographic_labels = LayerContainer(self.geographic, text = "Labels")
        self.geographic_gridlines = LayerContainer(self.geographic, text = "Grid lines")
        self.utm = LayerContainer(self.grids, text="UTM coordinates")
        self.utm_labels = LayerContainer(self.utm, text = "Labels")
        self.utm_gridlines = LayerContainer(self.utm, text = "Grid lines")

        self.symbols = LayerContainer(self.scrollable_container_left.scrollable_frame, text = "Symbols")
        self.placemarks = LayerContainer(self.symbols, text = "Placemarks")
        self.linear_features = LayerContainer(self.symbols, text = "Linear features")

        self.contour_lines = LayerContainer(self.scrollable_container_left.scrollable_frame, text = "Contour lines", settings = self.contour_settings)
        self.contour_labels = LayerContainer(self.contour_lines, text="Contour Labels")
        self.index_contours = LayerContainer(self.contour_lines, text = "Index contours")
        self.intermediate_contours = LayerContainer(self.contour_lines, text = "Intermediate contours")

        self.shading = LayerContainer(self.scrollable_container_left.scrollable_frame, text="Gradient shading", settings = self.shading_settings)

        self.areas = LayerContainer(self.scrollable_container_left.scrollable_frame, text="Areas")

        self.base_map = LayerContainer(self.scrollable_container_left.scrollable_frame, text="Base map")

        def change_aerial():
            if self.aerial_image_on:
                self.aerial_image_on = False
            else:
                self.aerial_image_on = True
            self.display_aerial()
        self.aerial = LayerContainer(self.base_map, text="Aerial image", checkboxcommand=change_aerial)

        self.map_canvas = tk.Canvas(self.root, bg = "white")
        self.map_canvas.pack(fill="both", expand=True)
        self.map_canvas.bind("<Motion>", self.mouse_motion)
        self.map_canvas.bind("<Button-1>", self.on_click)
        self.map_canvas.bind("<ButtonRelease-1>", self.on_unclick)
        self.map_canvas.bind("<Button-3>",self.button_3)
        self.map_canvas.bind("<MouseWheel>", self.mouse_scroll)
        self.root.bind('<KeyPress-Control_L>', self.on_ctrl_press)
        self.root.bind('<KeyPress-Control_R>', self.on_ctrl_press)
        self.root.bind('<KeyRelease-Control_L>', self.on_ctrl_release)
        self.root.bind('<KeyRelease-Control_R>', self.on_ctrl_release)
        self.root.bind('<Control-z>', self.undo)
        self.image = None
        self.ctrl_pressed = False
        self.mouse_pressed = False

        self.reference_latitude = 40.664989
        self.reference_longitude = 32.766711
        self.center_latitude = self.reference_latitude
        self.center_longitude = self.reference_longitude
        self.cursor_latitude, self.cursor_longitude = self.center_latitude, self.center_longitude
        self.map_scale = 25000
        self.northernmost_lat = None
        self.southernmost_lat = None
        self.easternmost_lon = None
        self.westernmost_lon = None
        self.zoom_level = -7
        self.images_dict = {}
        self.image_thread_progress = False
        self.full_res_done = False
        self.dictionary_zoom_ok = False
        self.last_image_update = 0
        self.full_res_times = []
        self.creating_line = 0
        self.current_line = None
        self.creating_polygon = 0
        self.current_polygon = None
        self.lines = []
        self.polygons = []
        self.line_no = 1
        self.polygon_no = 1
        self.last_motion_time = 0
        self.zoom_in_progress = False

        self.last_call = None

        self.polygon_types = {"Building":("black", False,3),
                              "Lake": ("#eaf6fa", ("#00b4c8", 0.2,2)),
                             "Settlement": ("#eccaaf", False,1),
                              "Vegetation": ("#ecf5d8", False,0),
                              "Map Borders": ("#001122", False,0)
                              }


        self.contours = ([],[])
        self.contour_catche = None

        self.map_settings()

    def on_ctrl_press(self, event):
        print("prssed")
        self.ctrl_pressed = True
        self.map_canvas.config(cursor="hand2")

    def on_ctrl_release(self, event):
        self.ctrl_pressed = False
        self.map_canvas.config(cursor="arrow")

    def new_instance(self):
        global total_instances
        total_instances += 1
        video_recorder = Map(dummy)
        video_recorder.root.mainloop()

    def on_closing(self):
        global total_instances
        total_instances -= 1
        if total_instances == 0:
            global dummy
            dummy.destroy()
        else:
            self.root.destroy()

    def configure_borders(self, start = False):
        self.last_image_update = time.time()
        self.northernmost_lat = self.center_latitude + 2 ** -self.zoom_level * (
                self.map_canvas.winfo_height() / (5000)) * self.map_scale / 111000
        self.southernmost_lat = self.center_latitude - 2 ** -self.zoom_level * (
                self.map_canvas.winfo_height() / (5000)) * self.map_scale / 111000
        self.easternmost_lon = self.center_longitude + 2 ** -self.zoom_level * (
                1 / np.cos(self.reference_latitude * np.pi / 180)) * (
                                       self.map_canvas.winfo_width() / (5000)) * self.map_scale / 111000
        self.westernmost_lon = self.center_longitude - 2 ** -self.zoom_level * (
                1 / np.cos(self.reference_latitude * np.pi / 180)) * (
                                       self.map_canvas.winfo_width() / (5000)) * self.map_scale / 111000
        if start == True:
            self.start_northernmost, self.start_southernmost, self.start_easternmost, self.start_westernmost = self.northernmost_lat, self.southernmost_lat, self.easternmost_lon, self.westernmost_lon
        """
        if self.zoom_level<0:
            self.zoom_level = 0
        try:
            if self.northernmost_lat > self.start_northernmost:
                self.center_latitude -= self.northernmost_lat - self.start_northernmost
                self.configure_borders()
            if self.southernmost_lat < self.start_southernmost:
                self.center_latitude -= self.southernmost_lat - self.start_southernmost
                self.configure_borders()
            if self.easternmost_lon > self.start_easternmost:
                self.center_longitude -= self.easternmost_lon - self.start_easternmost
                self.configure_borders()
            if self.westernmost_lon < self.start_westernmost:
                self.center_longitude -= self.westernmost_lon - self.start_westernmost
                self.configure_borders()
            
        except Exception as e:
            print(e)
        """
    def mouse_scroll(self, event):
        if event == 0:
            pass
        else:
            delta = event.delta

        self.zoom_frames = 7
        increment = 1/self.zoom_frames
        self.last_call = time.time()
        self.lat_before_zoom = self.center_latitude
        self.lon_before_zoom = self.center_longitude
        self.northernmost_lat_prev, self.southernmost_lat_prev, self.easternmost_lon_prev, self.westernmost_lon_prev = self.northernmost_lat, self.southernmost_lat, self.easternmost_lon, self.westernmost_lon

        if delta > 0:
            #def scroll_in_thread():
            self.center_latitude = self.lat_before_zoom + 0.5 * 1 * (
                        self.cursor_latitude - self.lat_before_zoom)
            self.center_longitude = self.lon_before_zoom + 0.5 * 1 * (
                        self.cursor_longitude - self.lon_before_zoom)
            print(self.zoom_level)
            self.zoom_level += 1
            print(self.zoom_level)
            self.configure_borders()

            print(self.zoom_level)
            threading.Thread(target=partial(self.display_aerial, afterzoom=True, last_call = self.last_call)).start()
            self.zoom_level -= 1
            zoom_increments = np.diff(2**np.linspace(0,1,self.zoom_frames+1) -1)
            for i in range(self.zoom_frames):
                self.zoom_in_progress = True
                self.center_latitude = self.lat_before_zoom + 0.5*increment*(i+1)*(self.cursor_latitude -self.lat_before_zoom)
                self.center_longitude = self.lon_before_zoom + 0.5*increment*(i+1)*(self.cursor_longitude - self.lon_before_zoom)
                self.zoom_level += zoom_increments[i]
                print(self.zoom_level)
                self.configure_borders()
                self.display_aerial(animation=1)
                self.visualise_all_polygons()
                if self.current_polygon:
                    self.current_polygon.visualise(style="progress")
                self.visualise_contours()
                self.visualise_all_lines()
                if self.current_line:
                    self.current_line.visualise(style="progress")
                try:
                    self.grid.visualise()
                except:
                    pass
                self.map_canvas.after(10)
                self.map_canvas.update_idletasks()
            self.zoom_in_progress = False
            self.zoom_level = round(self.zoom_level)
            #threading.Thread(target = partial(self.display_aerial, last_call = self.last_call)).start()
            #threading.Thread(target = scroll_in_thread).start()

        else:

            #def zoom_out_thread():
            self.center_latitude = self.lat_before_zoom - 1 * (
                        self.cursor_latitude - self.lat_before_zoom)
            self.center_longitude = self.lon_before_zoom - 1 * (
                        self.cursor_longitude - self.lon_before_zoom)
            self.zoom_level -= 1
            self.configure_borders()

            threading.Thread(target=partial(self.display_aerial, afterzoom=True,last_call = self.last_call)).start()
            self.zoom_level += 1
            zoom_increments = np.diff(2**np.linspace(0,1,self.zoom_frames+1) -1)
            for i in range(self.zoom_frames):
                self.zoom_in_progress = True
                self.center_latitude = self.lat_before_zoom - increment*(i+1)*(self.cursor_latitude - self.lat_before_zoom)
                self.center_longitude = self.lon_before_zoom - increment*(i+1)*(self.cursor_longitude - self.lon_before_zoom)
                self.zoom_level -= zoom_increments[-1-i]
                self.configure_borders()
                self.display_aerial(animation=-1)
                self.visualise_all_polygons()
                if self.current_polygon:
                    self.current_polygon.visualise(style="progress")
                self.visualise_contours()
                self.visualise_all_lines()
                if self.current_line:
                    self.current_line.visualise(style="progress")
                try:
                    self.grid.visualise()
                except:
                    pass
                self.map_canvas.after(10)
                self.map_canvas.update_idletasks()
            self.zoom_in_progress = False
            self.zoom_level = round(self.zoom_level)
            #threading.Thread(target = partial(self.display_aerial, last_call = self.last_call)).start()
            #threading.Thread(target = zoom_out_thread).start()

        self.visualise_all_polygons()
        if self.current_polygon:
            self.current_polygon.visualise(style="progress")
        threading.Thread(target=self.visualise_contours).start()
        threading.Thread(target=self.visualise_all_lines).start()
        if self.current_line:
            self.current_line.visualise(style="progress")
        try:
            self.grid.visualise()
        except:
            pass

    def display_aerial(self, last_call=None, animation=False, afterzoom=False, motion=False):
        if animation == 1 and self.aerial_image_on:
            self.current_image.display()

        if animation == -1 and self.aerial_image_on:
            self.bigger.display()

        if motion == True and self.aerial_image_on:
            self.bigger.display()

        if animation == False:
            if motion == True:
                return
            if self.aerial_image_on:
                self.current_image = AerialImage(self, self.northernmost_lat, self.southernmost_lat, self.easternmost_lon, self.westernmost_lon, zoom = 13 + self.zoom_level)
            if afterzoom == True and self.aerial_image_on:
                while self.zoom_in_progress == True:
                    time.sleep(0.1)
            print("aafter")
            if last_call == self.last_call:
                self.map_canvas.delete("all")
                if self.aerial_image_on:
                    self.current_image.display()
                print("current image display")
                self.visualise_all_polygons()
                if self.current_polygon:
                    self.current_polygon.visualise(style="progress")
                self.visualise_contours()
                self.visualise_all_lines()
                if self.current_line:
                    self.current_line.visualise(style="progress")
                try:
                    self.grid.visualise()
                except:
                    pass

            def bigger_image():
                if last_call == self.last_call:
                    self.bigger = AerialImage(self,
                                              north = self.northernmost_lat + (self.northernmost_lat - self.southernmost_lat),
                                              south = self.southernmost_lat - (self.northernmost_lat - self.southernmost_lat),
                                              east = self.easternmost_lon + (self.easternmost_lon - self.westernmost_lon),
                                              west = self.westernmost_lon - (self.easternmost_lon - self.westernmost_lon),
                                              zoom = 12 + self.zoom_level)

                #self.map_canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
            if self.aerial_image_on:
                threading.Thread(target=bigger_image).start()


    def map_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.geometry("300x200")
        settings_window.title("Initialize")
        settings_window.wm_iconphoto(False, self.icon_photo)


        tk.Label(settings_window, text = "Reference Coordinates").pack()

        latitude_entry_frame = tk.Frame(settings_window, height = 25)
        latitude_entry_frame.pack()
        tk.Label(latitude_entry_frame, text = "    Latitude:").pack(side=tk.LEFT)
        lat_entry = tk.Entry(latitude_entry_frame)
        lat_entry.pack(side=tk.LEFT)


        if self.reference_latitude:
            lat_entry.insert(0, str(self.reference_latitude))


        longitude_entry_frame = tk.Frame(settings_window, height=25)
        longitude_entry_frame.pack()
        tk.Label(longitude_entry_frame, text="Longitude:").pack(side=tk.LEFT)
        lon_entry = tk.Entry(longitude_entry_frame)
        lon_entry.pack(side=tk.LEFT)
        if self.reference_longitude:
            lon_entry.insert(0, str(self.reference_longitude))

        scale_entry_frame = tk.Frame(settings_window, height=25)
        scale_entry_frame.pack(pady = 10)
        tk.Label(scale_entry_frame, text="          Scale:").pack(side=tk.LEFT)
        scale_entry = tk.Entry(scale_entry_frame)
        scale_entry.pack(side=tk.LEFT)
        if self.map_scale:
            scale_entry.insert(0, "1:"+str(self.map_scale))

        def set_settings():
            from coordinate_read import coordinateread
            self.reference_latitude, self.reference_longitude = coordinateread(lat_entry.get()), coordinateread(lon_entry.get())
            self.center_latitude, self.center_longitude = self.reference_latitude, self.reference_longitude
            self.map_scale = int(scale_entry.get().split(":")[-1])
            #print(self.reference_latitude, self.reference_longitude)
            self.configure_borders(start = True)
            tk.Label(settings_window, text = "Downloading aerial image...").pack(pady = 5)
            self.display_aerial()
            settings_window.destroy()
        tk.Button(settings_window, text = "Ok", command = set_settings).pack()



        settings_window.mainloop()

    def to_left(self):
        self.center_longitude = self.westernmost_lon
        self.configure_borders()
        self.display_aerial(last_call=self.last_call)
        return

    def to_right(self):
        self.center_longitude = self.easternmost_lon
        self.configure_borders()
        self.display_aerial(last_call=self.last_call)
        return

    def to_up(self):
        self.center_latitude = self.northernmost_lat
        self.configure_borders()
        self.display_aerial(last_call=self.last_call)
        return

    def to_down(self):
        self.center_latitude = self.southernmost_lat
        self.configure_borders()
        self.display_aerial(last_call=self.last_call)
        return

    def zoom(self, direction):
        self.zoom_level += direction
        self.configure_borders()
        self.display_aerial(last_call=self.last_call)
        return

    def after_motion(self):
        def a_m_thread():
            time.sleep(5)
            if time.time()- self.last_motion_time > 4.9:
                self.display_aerial(animation=False)

        threading.Thread(target = a_m_thread()).start()

    def mouse_motion(self,event):
        if self.ctrl_pressed and self.mouse_pressed:
            newlon = self.westernmost_lon + (event.x/self.map_canvas.winfo_width())*(self.easternmost_lon - self.westernmost_lon)
            newlat = self.southernmost_lat + ((1-event.y/self.map_canvas.winfo_height()))*(self.northernmost_lat - self.southernmost_lat)

            self.center_latitude -= newlat - self.cursor_latitude
            self.center_longitude -= newlon - self.cursor_longitude
            self.configure_borders()
            print("on motion, before display command")
            self.last_motion_time = time.time()
            self.display_aerial(motion = True, animation=False)
            self.after_motion()
            print("on motion, after display command")
            self.map_canvas.update_idletasks()
        if self.center_latitude:
            try:
                self.cursor_longitude = self.westernmost_lon + (event.x/self.map_canvas.winfo_width())*(self.easternmost_lon - self.westernmost_lon)

                self.cursor_latitude = self.southernmost_lat + ((1-event.y/self.map_canvas.winfo_height()))*(self.northernmost_lat - self.southernmost_lat)

                #print(latitude, longitude)
            except:
                pass
            if self.creating_line == 1:
                """
                try:
                    self.map_canvas.delete(self.dynamic_line)

                except:
                    pass
                self.dynamic_line = self.map_canvas.create_line(self.gps2pixels(self.current_line.longitudes[-1],0),
                                                                self.gps2pixels(self.current_line.latitudes[-1],1),
                                                                self.gps2pixels(self.cursor_longitude,0),
                                                                self.gps2pixels(self.cursor_latitude,1),
                                                                fill="#FF0000")
                """
                pass

            else:
                self.update_info(str(self.cursor_latitude)[:9] + "°" + ", " + str(
                                           self.cursor_longitude)[:9] + "°")

    def update_info(self, text):
        try:
            self.map_canvas.tag_raise(self.coordinate_label1)
            self.map_canvas.tag_raise(self.coordinate_label2)
            self.map_canvas.tag_raise(self.coordinate_label3)
            self.map_canvas.tag_raise(self.coordinate_label4)

            self.map_canvas.tag_raise(self.coordinate_label)

            self.map_canvas.itemconfig(self.coordinate_label1,
                                       text=text)
            self.map_canvas.itemconfig(self.coordinate_label2,
                                       text=text)
            self.map_canvas.itemconfig(self.coordinate_label3,
                                       text=text)
            self.map_canvas.itemconfig(self.coordinate_label4,
                                       text=text)
            self.map_canvas.itemconfig(self.coordinate_label,
                                       text=text)

        except:
            self.coordinate_label1 = self.map_canvas.create_text(self.map_canvas.winfo_width() // 2 + 1,
                                                                 self.map_canvas.winfo_height() - 10 + 1,
                                                                 text=text,
                                                                 font="Calibri 12 bold", anchor="s",
                                                                 fill="white")
            self.coordinate_label2 = self.map_canvas.create_text(self.map_canvas.winfo_width() // 2 + 1,
                                                                 self.map_canvas.winfo_height() - 10 - 1,
                                                                 text=text,
                                                                 font="Calibri 12 bold", anchor="s",
                                                                 fill="white")
            self.coordinate_label3 = self.map_canvas.create_text(self.map_canvas.winfo_width() // 2 - 1,
                                                                 self.map_canvas.winfo_height() - 10 + 1,
                                                                 text=text,
                                                                 font="Calibri 12 bold", anchor="s",
                                                                 fill="white")
            self.coordinate_label4 = self.map_canvas.create_text(self.map_canvas.winfo_width() // 2 - 1,
                                                                 self.map_canvas.winfo_height() - 10 - 1,
                                                                 text=text,
                                                                 font="Calibri 12 bold", anchor="s",
                                                                 fill="white")
            self.coordinate_label = self.map_canvas.create_text(self.map_canvas.winfo_width() // 2,
                                                                self.map_canvas.winfo_height() - 10,
                                                                text=text,
                                                                font="Calibri 12 bold", anchor="s", fill="black")

            self.map_canvas.tag_raise(self.coordinate_label1)
            self.map_canvas.tag_raise(self.coordinate_label2)
            self.map_canvas.tag_raise(self.coordinate_label3)
            self.map_canvas.tag_raise(self.coordinate_label4)

            self.map_canvas.tag_raise(self.coordinate_label)

    def on_unclick(self, event):
        self.mouse_pressed = False
        #self.display_aerial(animation=False, afterzoom=True, motion=False)

    def on_click(self,event):
        self.mouse_pressed = True

        #print(len(self.lines))
        if self.creating_line == 1:
            self.current_line.hide()
            self.current_line.append(self.cursor_longitude,self.cursor_latitude)
            self.current_line.visualise(style = "progress")

        if self.creating_polygon == 1:
            self.current_polygon.hide()
            self.current_polygon.append(self.cursor_longitude,self.cursor_latitude)
            self.current_polygon.visualise(style = "progress")

    def undo(self, event = 0):
        if self.creating_line == 1:
            self.current_line.hide()
            self.current_line.undo()
            self.current_line.visualise(style="progress")

        if self.creating_polygon == 1:
            self.current_polygon.hide()
            self.current_polygon.undo()
            self.current_polygon.visualise(style = "progress")


    def create_line(self, event = 0):
        if self.create_line_button.cget("state") == "normal":
            self.create_line_button.config(state = "disabled")
            self.map_canvas.config(cursor="target")
            self.creating_line = 1
            self.current_line = Line(self)
        else:
            self.create_line_button.config(state = "normal")
            self.map_canvas.config(cursor="arrow")
            self.creating_line = 0
            self.current_line.hide()
            self.lines.append(self.current_line)

            id = len(self.lines)-1
            def checkbox():
                #print(id)
                if self.lines[id].display is False or self.lines[id].display == None:
                    #print("CCC")
                    self.lines[id].visualise()
                else:
                    #print("DDD")
                    self.lines[id].hide()
                self.display_aerial(last_call=self.last_call)

            line = self.current_line

            def line_settings():
                line_settings = tk.Toplevel(self.root)
                line_settings.wm_geometry("200x100")
                line_settings.title("Line Settings")
                line_settings.wm_iconphoto(False,self.icon_photo)

                lines_combo = ttk.Combobox(line_settings, values = ["-Default-",
                                                                    "Dual highway",
                                                                  "Dual motorway",
                                                                  "Major road",
                                                                  "Minor road",
                                                                  "Major road, loose",
                                                                  "Minor road, loose",
                                                                  "Light duty road, paved",
                                                                  "Light duty road, gravel",
                                                                  "Unimproved road",
                                                                  "4WD road",
                                                                  "Trail",
                                                                  "Trail (small)",
                                                                  "River",
                                                                  "Stream",
                                                                  "Powerline"], state = "readonly")
                lines_combo.set("-Default-")
                if self.lines[id].path:
                    lines_combo.set(self.lines[id].path)
                lines_combo.pack()

                def ok():
                    line_settings.destroy()

                def select(event):
                    self.lines[id].path = lines_combo.get()
                    self.display_aerial(afterzoom=True, last_call=self.last_call)
                lines_combo.bind("<<ComboboxSelected>>",select)

                ok_button = tk.Button(line_settings, text = "Ok", command = ok)
                ok_button.pack()

                line_settings.mainloop()
            LayerContainer(
                self.linear_features,
                f"Path {self.line_no}",
                delete = line.delete,
                barren = True,
                checkboxcommand=checkbox,
                settings = line_settings
            )
            self.current_image.display()
            self.current_line = None
            self.line_no += 1
            self.visualise_all_polygons()
            self.visualise_contours()
            self.visualise_all_lines(last_line = True)
            try:
                self.grid.visualise()
            except:
                pass

    def create_polygon(self, event = 0):
        if self.create_polygon_button.cget("state") == "normal":
            self.create_polygon_button.config(state = "disabled")
            self.map_canvas.config(cursor="target")
            self.creating_polygon = 1
            self.current_polygon = Polygon(self, fill="white")
        else:
            self.create_polygon_button.config(state = "normal")
            self.map_canvas.config(cursor="arrow")
            self.creating_polygon = 0
            self.current_polygon.hide()
            self.polygons.append(self.current_polygon)

            id = len(self.polygons) - 1
            def checkbox():
                #print(id)
                if self.polygons[id].display is False or self.polygons[id].display == None:
                    #print("CCC")
                    self.polygons[id].visualise()
                else:
                    #print("DDD")
                    self.polygons[id].hide()
                self.display_aerial(last_call=self.last_call)

            def polygon_settings(id):
                polygon_settings = tk.Toplevel(self.root)
                polygon_settings.wm_geometry("200x100")
                polygon_settings.title("Polygon Settings")
                polygon_settings.wm_iconphoto(False, self.icon_photo)

                polygon_combo = ttk.Combobox(polygon_settings, values = ["-Default-"]+list(self.polygon_types.keys()),
                                                                         state = "readonly")
                polygon_combo.set("-Default-")
                if self.polygons[id].fill == "white":
                    polygon_combo.set("-Default-")
                if self.polygons[id].fill == "#ecf5d8":
                    polygon_combo.set("Vegetation")
                if self.polygons[id].fill == "black":
                    polygon_combo.set("Building")
                if self.polygons[id].fill == "#eccaaf":
                    polygon_combo.set("Settlement")
                if self.polygons[id].fill == "#eaf6fa" and self.polygons[id].outline[1] == "#00b4c8":
                    polygon_combo.set("Lake")
                if self.polygons[id].fill == "black":
                    polygon_combo.set("Building")
                polygon_combo.pack()

                def select_color(id):
                    color = colorchooser.askcolor(self.polygons[id].fill, title="Select fill color")
                    self.polygons[id].fill = color[1]
                    self.display_aerial(afterzoom=True, last_call=self.last_call)

                custom_color = tk.Button(polygon_settings, text = "Choose fill color", command=partial(select_color,id))
                custom_color.pack()

                def select_o_color(id):
                    color = colorchooser.askcolor(self.polygons[id].fill, title="Select outline color")
                    try:
                        self.polygons[id].outline = (color[1],self.polygons[id].outline[1])
                    except Exception as e:
                        print(e)
                        self.polygons[id].outline = (color[1],0.2)
                    self.display_aerial(afterzoom=True, last_call=self.last_call)

                outline_color = tk.Button(polygon_settings, text = "Choose outline color", command=partial(select_o_color,id))
                outline_color.pack()



                outline_width = tk.Entry(polygon_settings)
                outline_width.pack()

                def outline_width_change(event):
                    try:
                        self.polygons[id].outline = (self.polygons[id].outline[0],float(outline_width.get()))
                    except Exception as e:
                        print(e)
                        self.polygons[id].outline = ("black",float(outline_width.get()))
                    self.display_aerial(last_call=self.last_call)

                outline_width.bind("<Return>", outline_width_change)

                def ok():
                    polygon_settings.destroy()
                    self.display_aerial(last_call=self.last_call)

                def select(event):
                    polygon_style =  polygon_combo.get()
                    self.polygons[id].fill = self.polygon_types[polygon_style][0]
                    self.polygons[id].outline = self.polygon_types[polygon_style][1]
                    self.display_aerial(last_call=self.last_call)

                polygon_combo.bind("<<ComboboxSelected>>",select)

                ok_button = tk.Button(polygon_settings, text = "Ok", command = ok)
                ok_button.pack()

                polygon_settings.mainloop()

            polygon = self.current_polygon
            LayerContainer(
                self.areas,
                f"Polygon {self.polygon_no}",
                delete = polygon.delete,
                checkboxcommand=checkbox,
                barren = True,
                settings = partial(polygon_settings,id)
            )
            self.current_polygon = None
            self.polygon_no += 1
            self.current_image.display()
            self.visualise_all_polygons(last_polygon = True)
            self.visualise_contours()
            self.visualise_all_lines()

            try:
                self.grid.visualise()
            except:
                pass


    def button_3(self, event = 0):
        if self.creating_line == 1:
            self.create_line()
        elif self.creating_polygon == 1:
            self.create_polygon()
        else:
            return

    def visualise_all_lines(self, last_line = False):
        for j in range(5):
            for i in range(len(self.lines)):
            #print(self.lines[i] , self.lines[i].display)
                if self.lines[i] and (self.lines[i].display == None or self.lines[i].display == True):
                    if not self.lines[i].path or self.lines[i].path == "-Default-":
                        self.lines[i].visualise()
                    else:
                        self.lines[i].visualise(layer = j)
        if last_line == True:
            for i in range(5):
                try:
                    self.lines[-1].visualise(layer=i)
                except:
                        pass
        return

    def transfer_all_lines(self, last_line = False):
        for j in range(5):
            for i in range(len(self.lines)):
            #print(self.lines[i] , self.lines[i].display)
                if self.lines[i] and (self.lines[i].display == None or self.lines[i].display == True):
                    def line_thread():
                        if not self.lines[i].path or self.lines[i].path == "-Default-":
                            self.lines[i].visualise()
                            self.map_canvas.coords(self.lines[i].lineid, )
                        else:
                            self.lines[i].visualise(layer = j)
                    threading.Thread(target = line_thread).start()
        if last_line == True:
            for i in range(5):
                try:
                    self.lines[-1].visualise(layer=i)
                except:
                        pass
        return

    def visualise_all_polygons(self, last_polygon = False):
        if last_polygon == True:
            self.polygons[-1].visualise()
        for i in range(len(self.polygons)):
            #print(self.lines[i] , self.lines[i].display)
            if self.polygons[i] and (self.polygons[i].display == None or self.polygons[i].display == True):
                self.polygons[i].visualise()
        return

    def gps2pixels(self, input, axis = 0):
        if axis == 0: #longitude-x
            return int(((input - self.westernmost_lon) / (
                    self.easternmost_lon - self.westernmost_lon)) * self.map_canvas.winfo_width())
        if axis == 1:
            return int((1 - ((input - self.southernmost_lat) / (
                    self.northernmost_lat - self.southernmost_lat))) * self.map_canvas.winfo_height())


    def contour_settings(self):

        contour_settings = tk.Toplevel(self.root)

        contour_settings.title("Contour Settings")
        contour_settings.wm_iconphoto(False, self.icon_photo)
        contour_settings.wm_geometry("200x200")

        tk.Label(contour_settings,text = "Contour interval:").pack()
        contour_interval = tk.Entry(contour_settings)
        contour_interval.pack()

        tk.Label(contour_settings, text="Index contour interval:").pack()
        index_contour_interval = tk.Entry(contour_settings)
        index_contour_interval.pack()

        def ok():
            self.progress_text = tk.Label(contour_settings, text = "Retrieving elevation data...")
            self.progress_text.pack(pady = 10)
            self.progress_bar_contour = tk.Canvas(contour_settings, width=100, height=10, bg = "#999999")
            self.progress_bar_contour.pack()
            polygon_points = [0,0,
                              0,10,
                              1,10,
                              1,0]
            self.progress_polygon_contour = self.progress_bar_contour.create_polygon(polygon_points, fill="#333333")

            def contour_thread():
                self.contour_interval = int(contour_interval.get())
                self.index_contour_interval = int(index_contour_interval.get())

                self.contours_lines = process_contour(self, contour_interval=self.contour_interval)

                for i in range(len(self.contours_lines)):
                    def contour_thread():
                        line = Contour(self, self.contours_lines[i], width=1)
                        line.visualise()
                        self.contours[0].append(line)
                        self.progress = int(100*i/len(self.contours_lines))
                        polygon_points = [0,0,
                                  0,11,
                                  self.progress,11,
                                  self.progress,0]
                        self.progress_bar_contour.coords(self.progress_polygon_contour, polygon_points)
                        self.progress_text.config(text = f"Plotting contours... {self.progress} %")

                    threading.Thread(target = contour_thread).start()

                def checkbox_intermediate():
                    for i in self.contours[0]:
                        if i.display == False or i.display == None:
                            i.visualise()
                        else:
                            i.hide()
                    return

                def delete_intermediate():
                    for i in range(len(self.contours[0])):
                        self.contours[-1-i].delete()
                        del self.contours[-1-i]

                LayerContainer(self.intermediate_contours,
                               text = f"{self.contour_interval} m",
                               checkboxcommand=checkbox_intermediate,
                               delete = delete_intermediate, barren = True)

                self.index_contours_lines = process_contour(self, contour_interval=self.index_contour_interval)

                for i in range(len(self.index_contours_lines)):
                    def index_contour_thread():
                        line = Contour(self, self.index_contours_lines[i], width=2)
                        line.visualise()
                        self.contours[1].append(line)
                        self.progress = int(100 * i / len(self.index_contours_lines))
                        polygon_points = [0,0,
                                  0,11,
                                  self.progress,11,
                                  self.progress,0]
                        self.progress_bar_contour.coords(self.progress_polygon_contour, polygon_points)
                        self.progress_text.config(text=f"Plotting index contours... {self.progress} %")
                    threading.Thread(target=index_contour_thread).start()

                def checkbox_index():
                    for i in self.contours[1]:
                        if i.display == False or i.display == None:
                            i.visualise()
                        else:
                            i.hide()
                    return

                def delete_index():
                    for i in range(len(self.contours[1])):
                        self.contours[-1 - i].delete()
                        del self.contours[-1 - i]

                LayerContainer(self.index_contours,
                               text=f"{self.index_contour_interval} m",
                               checkboxcommand=checkbox_index,
                               delete=delete_index, barren = True)

                self.progress_text.config(text="Contour plot completed!")
                self.contour_catche = None
            threading.Thread(target = contour_thread).start()


        tk.Button(contour_settings, text = "Plot contours for the area", command = ok).pack(pady = 10)
        contour_settings.mainloop()



    def visualise_contours(self):
        for i in self.contours[0]:
            def thrd():
                i.visualise()
            threading.Thread(target = thrd).start()

        for i in self.contours[1]:
            def thrd2():
                i.visualise()

            threading.Thread(target=thrd2).start()

    def shading_settings(self):
        return

    def grid_settings(self):
        self.grid = Grid(map = self)
        self.grid.visualise()



    def export(self):
        borders_x, borders_y = None, None
        for i in self.polygons:
            if i.fill == "#001122":
                borders_x, borders_y = i.longitudes, i.latitudes
                break

        distance_x = (1/np.cos(borders_y[0]))*111390*(max(borders_x) - min(borders_x))
        distance_y = 111390 * (max(borders_y) - min(borders_y))

        orientation = None

        if distance_x > distance_y:
            orientation = "landscape"
        else:
            orientation = "portrait"

        metric_index = 5

        center_lon = 0.5*(max(borders_x) + min(borders_x))
        center_lat = 0.5*(max(borders_y) + min(borders_y))

        def half_paper(n,orientation):

            if orientation == "portrait":
                dx = (2 ** (5 - n)) * 0.5 * 0.1485 * self.map_scale / (111390 * (1 / 1 / np.cos(borders_y[0])))
                dy = (2 ** (5 - n)) * 0.5 * 0.210 * self.map_scale / 111390
                return center_lat+dy, center_lat-dy, center_lon-dx,center_lon+dx
            else:
                dx = (2 ** (5 - n)) * 0.5 * 0.210 * self.map_scale / (111390 * (1 / 1 / np.cos(borders_y[0])))
                dy = (2 ** (5 - n)) * 0.5 * 0.1485 * self.map_scale / 111390
                return center_lat+dy, center_lat-dy, center_lon-dx,center_lon+dx

        while True:
            north, south, east, west = half_paper(metric_index,orientation)
            if north > max(borders_y) and south < min(borders_y) and east > max(borders_x) and west < min(borders_x):
                break
            else:
                metric_index -= 1

        print(metric_index, center_lon, center_lat)

        from createpdf import Sheet

        x = 14.85*2**(5-metric_index)
        y = 21*2**(5-metric_index)
        if orientation == "portrait":
            width = x
            height = y
        else:
            width = y
            height = x
        mapsheet = Sheet(width, height, self.map_scale, self, "mapp")
        mapsheet.create_map()

        mapsheet.save()





def main():
    dummy = tk.Tk()
    dummy.title("OpenTopoMapper (host)")
    screen_width = dummy.winfo_screenwidth()
    screen_height = dummy.winfo_screenheight()

    window_width = 0
    window_height = 0

    # Calculate position x and y coordinates
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    dummy.geometry(f'{window_width}x{window_height}+{x}+{y}')
    dummy.overrideredirect(True)
    dummy.resizable(False,False)
    dummy.geometry(f'{window_width}x{window_height}+{99999}+{99999}')
    #root.iconphoto(False,main_icon)
    dummy.deiconify()
    global total_instances
    total_instances = 0
    def create_instance():
        global total_instances
        total_instances += 1
        map = Map(dummy)
        map.root.mainloop()
    #tk.Button(text = "Create Instance", command = create_instance).place(x=0,y = 0, anchor = "nw")

    create_instance()
    dummy.mainloop()

if __name__ == "__main__":
    main()
