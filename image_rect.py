from image_download import run as download
import numpy as np
import cv2

class AerialImages:
    def __init__(self, map, max_zoom = 6):
        self.map = map
        self.center_lat = map.center_latitude
        self.center_lon = map.center_longitude
        self.images = {}
        self.max_zoom = max_zoom
        self.zoom_level = self.map.zoom_level


        self.northernmost_lat = self.center_lat + 2 ** -self.zoom_level * (
                self.map.map_canvas.winfo_height() / (5000)) * self.map.map_scale / 111000
        self.southernmost_lat = self.map.center_latitude - 2 ** -self.zoom_level * (
                self.map.map_canvas.winfo_height() / (5000)) * self.map.map_scale / 111000
        self.easternmost_lon = self.map.center_longitude + 2 ** -self.zoom_level * (
                1 / np.cos(self.map.reference_latitude * np.pi / 180)) * (
                                       self.map.map_canvas.winfo_width() / (5000)) * self.map.map_scale / 111000
        self.westernmost_lon = self.map.center_longitude - 2 ** -self.zoom_level * (
                1 / np.cos(self.map.reference_latitude * np.pi / 180)) * (
                                       self.map.map_canvas.winfo_width() / (5000)) * self.map.map_scale / 111000

        for i in range(self.max_zoom):
            for j in range(2**i):
                for k in range(2**i):
                    horizontal_spacing = (self.easternmost_lon - self.westernmost_lon)/(2**i)
                    westernmost = self.westernmost_lon + j*horizontal_spacing
                    easternmost = self.westernmost_lon + (j+1)*horizontal_spacing

                    vertical_spacing = (self.northernmost_lat - self.southernmost_lat)/(2**i)
                    southernmost = self.southernmost_lat + k*vertical_spacing
                    northernmost = self.southernmost_lat + (k+1)*vertical_spacing

                    image = download(north=northernmost, south=southernmost, east=easternmost, west=westernmost, zoom=i+14)
                    self.images.update({str(i) + "," + str(j) + "," + str(k), image})

    def get_image(self,zoom_level, northernmost, southernmost, easternmost, westernmost):
        def get_parse(zoom,a,b):
            return self.images[zoom+","+a+","+b]

        topleft_a = (westernmost - self.westernmost_lon) // ((self.northernmost_lat - self.southernmost_lat)/(2**zoom_level))
        topleft_b = (northernmost - self.southernmost_lat) // ((self.northernmost_lat - self.southernmost_lat)/(2**zoom_level))

        horizontal_spacing = (self.easternmost_lon - self.westernmost_lon) / (2 ** zoom_level)
        westernmost1 = self.westernmost_lon + topleft_a * horizontal_spacing
        easternmost1 = self.westernmost_lon + (topleft_a + 1) * horizontal_spacing

        vertical_spacing = (self.northernmost_lat - self.southernmost_lat) / (2 ** zoom_level)
        southernmost1 = self.southernmost_lat + topleft_b * vertical_spacing
        northernmost1 = self.southernmost_lat + (topleft_b + 1) * vertical_spacing
        topleft = get_parse(zoom_level,topleft_a, topleft_b)
        topleft_cropped = topleft[((westernmost-westernmost1)/(easternmost1-westernmost1))*topleft.shape[0]:,
                          ((northernmost-southernmost1)/(northernmost1-southernmost1))*topleft.shape[1]:]

        #BELOW WILL BE CHANGED

        topleft_a = (westernmost - self.westernmost_lon) // ((self.northernmost_lat - self.southernmost_lat)/(2**zoom_level))
        topleft_b = (northernmost - self.southernmost_lat) // ((self.northernmost_lat - self.southernmost_lat)/(2**zoom_level))

        horizontal_spacing = (self.easternmost_lon - self.westernmost_lon) / (2 ** zoom_level)
        westernmost1 = self.westernmost_lon + topleft_a * horizontal_spacing
        easternmost1 = self.westernmost_lon + (topleft_a + 1) * horizontal_spacing

        vertical_spacing = (self.northernmost_lat - self.southernmost_lat) / (2 ** zoom_level)
        southernmost1 = self.southernmost_lat + topleft_b * vertical_spacing
        northernmost1 = self.southernmost_lat + (topleft_b + 1) * vertical_spacing
        topleft = get_parse(zoom_level,topleft_a, topleft_b)
        topleft_cropped = topleft[((westernmost-westernmost1)/(easternmost1-westernmost1))*topleft.shape[0]:,
                          ((northernmost-southernmost1)/(northernmost1-southernmost1))*topleft.shape[1]:]


