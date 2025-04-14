import numpy as np

def coordinateread(coordinate):
    multiply = 1
    try:
        x = coordinate.index("-")
        multiply = -1
        coordinate = coordinate[x + 1:]
    except:
        pass

    try:
        x = coordinate.index("+")
        multiply = 1
    except:
        pass

    try:
        x = coordinate.index("N")
    except:
        pass

    try:
        x = coordinate.index("n")
    except:
        pass

    try:
        x = coordinate.index("E")
    except:
        pass

    try:
        x = coordinate.index("e")
    except:
        pass

    try:
        x = coordinate.index("S")
        multiply = -1

    except:
        pass

    try:
        x = coordinate.index("s")
        multiply = -1
    except:
        pass

    try:
        x = coordinate.index("W")
        multiply = -1
    except:
        pass

    try:
        x = coordinate.index("w")
        multiply = -1
    except:
        pass

    #print(multiply)

    try:
        degreeindex = coordinate.index("°")
    except:
        coordinate = coordinate + "°"
        degreeindex = coordinate.index("°")

    degrees = coordinate.split("°")[0]
    try:
        minutes = coordinate[degreeindex + 1:].split("'")[0]

        minindex = coordinate.index("'")
        try:
            seconds = coordinate[minindex + 1:].split('"')[0]
            float(seconds)
        except:
            seconds = 0

    except:
        minutes = 0
        seconds = 0

    return multiply * (np.float64(degrees) + np.float64(minutes) / 60 + np.float64(seconds) / 3600)