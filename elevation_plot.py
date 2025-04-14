from matplotlib import pyplot as plt
import numpy as np
import os
from dted import Tile, LatLon
import tkinter as tk
from matplotlib.path import Path
from PIL import Image
import tkinter.messagebox


def elevation(latitude, longitude, elevations):
    try:
        if latitude >= 0:
            a = "n"
        else:
            a = "s"
        if longitude >= 0:
            b = "e"
        else:
            b = "w"
        dted_file = os.path.join("elevation_data", f"{a}{int(latitude)}_{b}0{int(longitude)}_1arc_v3.dt2")

        if dted_file not in elevations:
            tile = Tile(dted_file)
            elevations[dted_file] = tile
        else:
            tile = elevations[dted_file]
        return tile.get_elevation(LatLon(latitude, longitude))
    except:
        tk.messagebox.showerror(title="Elevation Data Missing",
                                message=f"{a}{int(latitude)}_{b}0{int(longitude)}_1arc_v3.dt2" + " could not be found.")
    return


def process_contour(map, contour_interval= 10):
    max_latitude = map.northernmost_lat
    min_latitude = map.southernmost_lat
    max_longitude = map.easternmost_lon
    min_longitude = map.westernmost_lon

    longitude_length = 111*(max_latitude - min_latitude)
    latitude_length = 111*(max_longitude - min_longitude)*np.cos(np.deg2rad(0.5*(min_latitude+max_latitude)))



    elevations = {}

    if not map.contour_catche:
        x = []
        y = []
        z = []
        lats = np.arange(min_latitude, max_latitude+1/3600, 1/3600)
        lons = np.arange(min_longitude, max_longitude+1/3600, 1 / 3600)
        Z = []
        for i in range(len(lats)):
            Z.append([])
            for j in lons:
                Z[i].append(elevation(lats[i],j,elevations))
                x.append(j)
                y.append(lats[i])
                z.append(elevation(lats[i],j,elevations))
            map.progress_text.config(text = f"Retrieving elevation data... {int(100*i/len(lats))} %")
            map.progress = int(100 * i / len(lats))
            polygon_points = [0, 0,
                              0, 11,
                              map.progress, 11,
                              map.progress, 0]
            map.progress_bar_contour.coords(map.progress_polygon_contour, polygon_points)
        x = np.array(x)
        y = np.array(y)
        z = np.array(z)

        map.contour_catche = (x,y,z)

    else:
        x,y,z = map.contour_catche[0], map.contour_catche[1], map.contour_catche[2]



    #hight_levels = (max(z) - min(z)) / contour_spacing
    #hight_levels = int(hight_levels)
    hight_levels = np.arange(0,max(z)+contour_interval,contour_interval)
    #rounding = min(z) % contour_spacing
    #z = z - rounding

    lowest_index = np.argmin(z)
    highest_index = np.argmax(z)

    plt.figure().clear()
    fig, (ax) = plt.subplots(nrows=1, figsize=(abs(latitude_length), abs(longitude_length)))

    tri = ax.tricontour(x, y, z, levels=hight_levels)

    ax.set(xlim=(min_longitude, max_longitude), ylim=(min_latitude, max_latitude))
    ax.axis('off')
    fig.subplots_adjust(bottom=0)
    fig.subplots_adjust(top=1)
    fig.subplots_adjust(left=0)
    fig.subplots_adjust(right=1)

    contours = []

    for collection in tri.collections:
        for path in collection.get_paths():
            # If path.codes is not None, there might be disjoint segments
            if path.codes is not None:
                # Find where MOVETO (1) occurs in path.codes to split disjoint segments
                split_indices = np.where(path.codes == Path.MOVETO)[0]

                # Split the vertices array at those indices
                segments = np.split(path.vertices, split_indices)

                # Append each segment as a separate contour
                for segment in segments:
                    if len(segment) > 1:
                        contours.append(segment)
            else:
                # If no codes, treat it as a single continuous path
                if len(path.vertices) > 1:
                    contours.append(path.vertices)

    return contours

def process_shading(map, horizontal_azimuth = 30, vertical_azimuth = 30):
    max_latitude = map.northernmost_lat
    min_latitude = map.southernmost_lat
    max_longitude = map.easternmost_lon
    min_longitude = map.westernmost_lon

    longitude_length = 111*(max_latitude - min_latitude)
    latitude_length = 111*(max_longitude - min_longitude)*np.cos(np.deg2rad(0.5*(min_latitude+max_latitude)))

    elevations = {}
    if not map.contour_catche:
        x = []
        y = []
        z = []
        lats = np.arange(min_latitude, max_latitude+1/3600, 1/3600)
        lons = np.arange(min_longitude, max_longitude+1/3600, 1 / 3600)
        Z = []
        for i in range(len(lats)):
            Z.append([])
            for j in lons:
                Z[i].append(elevation(lats[i],j,elevations))
                x.append(j)
                y.append(lats[i])
                z.append(elevation(lats[i],j,elevations))
            map.progress_text.config(text = f"Retrieving elevation data... {int(100*i/len(lats))} %")
            map.progress = int(100 * i / len(lats))
            polygon_points = [0, 0,
                              0, 11,
                              map.progress, 11,
                              map.progress, 0]
            map.progress_bar_contour.coords(map.progress_polygon_contour, polygon_points)
        x = np.array(x)
        y = np.array(y)
        z = np.array(z)

        map.contour_catche = (x,y,z)

    else:
        x,y,z = map.contour_catche[0], map.contour_catche[1], map.contour_catche[2]

    # hight_levels = (max(z) - min(z)) / contour_spacing
    # hight_levels = int(hight_levels)
    # rounding = min(z) % contour_spacing
    # z = z - rounding

    lowest_index = np.argmin(z)
    highest_index = np.argmax(z)
    dy = 111390 / 3600
    dx = dy * np.cos(map.southernmost_lat)


    Z_gradient = []
    for i in range(len(Z) - 1):
        Z_gradient.append([])
        for j in range(len(Z[0]) - 1):
            gradientx = (Z[i][j] - Z[i + 1][j]) / dx
            gradienty = (Z[i][j] - Z[i][j + 1]) / dy
            gradientz = 1

            magnitude = (gradientx ** 2 + gradienty ** 2 + gradientz ** 2) ** 0.5
            gradientx = gradientx / magnitude
            gradienty = gradienty / magnitude
            gradientz = gradientz / magnitude

            Z_gradient[i].append([gradientx, gradienty, gradientz])

    alfa = horizontal_azimuth #horizontal azimuth
    beta = vertical_azimuth #vertical azimuth
    lightsource = [np.sin(-beta * np.pi / 180), np.sin(alfa * np.pi / 180), 1]
    lightsource_magnitude = (lightsource[0]**2+lightsource[1]**2+lightsource[2]**2)**0.5
    lightsource[0] = lightsource[0] / lightsource_magnitude
    lightsource[1] = lightsource[1] / lightsource_magnitude
    lightsource[2] = lightsource[2] / lightsource_magnitude

    if beta == 0 and alfa == 0:
        azimuth = "undefined"
    elif beta == 0 and alfa > 0:
        azimuth = 90
    elif beta == 0 and alfa < 0:
        azimuth = 270
    elif alfa == 0 and beta > 0:
        azimuth = 0
    elif alfa == 0 and beta < 0:
        azimuth = 180
    elif beta >= 0:
        azimuth = (180/np.pi)*np.arctan(np.cos(beta * np.pi / 180)*np.sin(alfa * np.pi / 180)/(np.cos(alfa * np.pi / 180)*np.sin(beta * np.pi / 180)))
    elif alfa >= 0:
        azimuth = 90 - (180 / np.pi) * np.arctan(np.cos(beta * np.pi / 180) * np.sin(alfa * np.pi / 180) / (
                    np.cos(alfa * np.pi / 180) * np.sin(beta * np.pi / 180)))
    else:
        azimuth = 360 - (180 / np.pi) * np.arctan(np.cos(beta * np.pi / 180) * np.sin(alfa * np.pi / 180) / (
                    np.cos(alfa * np.pi / 180) * np.sin(beta * np.pi / 180)))

    azimuth_vertical = 90
    if alfa*beta > 0:
        if alfa > 0:
            azimuth_vertical = abs( (90-alfa)*np.cos(-beta * np.pi / 180) )
        else:
            azimuth_vertical = abs((90+alfa) * 0.5 * np.cos(beta * np.pi / 180))
    elif alfa*beta <0:
        if alfa <0:
            azimuth_vertical = abs( (90+alfa)*np.cos(-beta * np.pi / 180) )
        else:
            azimuth_vertical = abs( (90-alfa)*np.cos(beta * np.pi / 180) )

    Z_shading = Z_gradient


    for i in range(len(Z_shading)):
        for j in range(len(Z_shading[0])):
            A = Z_shading[i][j][0] * lightsource[0] + Z_shading[i][j][1] * lightsource[1] + Z_shading[i][j][2] * lightsource[2]
            Z_shading[i][j] = (0.5*(abs(A)+A)) ** 1

    plt.figure().clear()
    x_size = int(latitude_length*1000)
    y_size = int(longitude_length*1000)
    shading = plt.imshow(Z_shading, cmap='gray', origin='lower',aspect = x_size/y_size)
    plt.axis('off')

    plt.subplots_adjust(bottom=0)
    plt.subplots_adjust(top=1)
    plt.subplots_adjust(left=0)
    plt.subplots_adjust(right=1)
    plt.savefig("images/temp_images/temp_shading.png", transparent=True, bbox_inches = 'tight',
    pad_inches = 0)
    plt.close()
    plt.figure().clear()
    #plt.show()
    grad_shading = Image.open("images/temp_images/temp_shading.png")

    print(x_size)
    print(y_size)
    #grad_shading = grad_shading.resize( (x_size, y_size) )
    grad_shading = grad_shading.convert("RGBA")
    pixdata = grad_shading.load()
    transparencyv = 1
    for y in range(grad_shading.size[1]):
        for x in range(grad_shading.size[0]):
                grad_shading.putpixel((x, y), (0,0,0,int(transparencyv*(255-pixdata[x,y][0]))))

