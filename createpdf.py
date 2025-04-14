from reportlab.pdfgen import canvas


class Sheet:
    def __init__(self, width, height, scale, map, filename):
        self.width = 182.88*width
        self.height = 182.88*height
        self.scale = scale
        self.file = canvas.Canvas(f"{filename}.pdf")
        self.map = map

    def create_map(self):
        layers = 4
        for i in range(layers):
            for j in self.map.lines:
                j.visualise(layer = i, canvas = "pdf")

        return

    def save(self):
        self.file.save()