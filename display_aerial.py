def display_aerial(self, start=False, tryzoom=False):
    if self.aerial_image_on:
        if start:
            # cv2.imwrite("imagee.png", image)
            def zoom_thread():
                self.image_thread_progress = True
                self.images_dict = {}
                for i in range(4):
                    try:
                        image = download(north=self.start_northernmost, south=self.start_southernmost,
                                         east=self.start_easternmost,
                                         west=self.start_westernmost, zoom=14 + i)
                    except:
                        continue
                    """
                    img_rgb = cv2.convertScaleAbs(
                        cv2.resize(cv2.cvtColor(image, cv2.COLOR_BGR2RGB),(self.map_canvas.winfo_width()*2**i, self.map_canvas.winfo_height()*2**i)),
                        alpha = 1,
                        beta = 100
                    )
                    """
                    img_rgb = cv2.resize(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), (
                    self.map_canvas.winfo_width() * 2 ** i, self.map_canvas.winfo_height() * 2 ** i))
                    if not img_rgb[0][0][0] and not img_rgb[0][0][1] and not img_rgb[0][0][2] and not img_rgb[-1][0][
                        0] and not img_rgb[-1][0][1] and not img_rgb[-1][0][2]:
                        break
                    img_pil = Image.fromarray(img_rgb)

                    self.images_dict.update({i: img_pil})
                    # Convert the PIL image to a Tkinter-compatible image (PhotoImage)

                    # Add the image to the canvas (keep a reference to avoid garbage collection)
                    if i == 0:
                        img_tk = ImageTk.PhotoImage(img_pil)

                        self.image = img_tk
                        self.map_canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
                    self.display_aerial()
                    self.update_info(text=f"Zoom level {i} constructed!")
                self.image_thread_progress = False
                self.update_info(text="3 zoom levels constructed!")

            threading.Thread(target=zoom_thread).start()
            if self.image_thread_progress == False:
                self.visualise_all_polygons()
                self.visualise_contours()
                self.visualise_all_lines()
                try:
                    self.grid.visualise()
                except:
                    pass
        else:
            def try_zooms(zoom):
                if self.full_res_done == True:
                    return
                if zoom < 0:
                    print("Invalid zoom level!")
                    return
                if self.zoom_level <= len(self.images_dict) - 1:
                    self.dictionary_zoom_ok = True
                else:
                    self.dictionary_zoom_ok = False
                if zoom < len(self.images_dict):
                    image = self.images_dict[int(zoom)]
                    width, height = image.size
                    left = round(width * (self.westernmost_lon - self.start_westernmost) / (
                                self.start_easternmost - self.start_westernmost))
                    top = round(height * (self.start_northernmost - self.northernmost_lat) / (
                                self.start_northernmost - self.start_southernmost))
                    right = round(width * (self.easternmost_lon - self.start_westernmost) / (
                                self.start_easternmost - self.start_westernmost))
                    bottom = round(height * (self.start_northernmost - self.southernmost_lat) / (
                            self.start_northernmost - self.start_southernmost))

                    crop_area = (left + 1, top + 1, right, bottom + 1)
                    cropped = image.crop(crop_area)
                    img_tk = ImageTk.PhotoImage(
                        cropped.resize((self.map_canvas.winfo_width(), self.map_canvas.winfo_height()), Image.LANCZOS))

                    self.image = img_tk
                    if self.full_res_done == True:
                        return
                    self.map_canvas.delete("all")
                    self.map_canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
                    self.aerial_done = True
                else:
                    try_zooms(zoom=zoom - 1)

            def full_res_thread():
                self.full_res_done = False
                center_lat, center_lon = self.center_latitude, self.center_longitude
                if self.dictionary_zoom_ok == True:
                    return
                i = self.zoom_level
                """
                if time.time() - self.last_image_update < 2:
                    print(time.time() - self.last_image_update)
                    return
                """
                if self.zoom_level == 0:
                    return
                request_time = time.time()
                self.full_res_times.append(request_time)
                time.sleep(1)
                zoom_normalise = int(self.zoom_level) + 14
                if zoom_normalise > 19:
                    zoom_normalise = 19
                while True:
                    if self.image_thread_progress:
                        time.sleep(2)
                    else:
                        break
                if max(self.full_res_times) == request_time:
                    image_full = download(north=self.northernmost_lat, south=self.southernmost_lat,
                                          east=self.easternmost_lon,
                                          west=self.westernmost_lon, zoom=zoom_normalise)
                    if not image_full[0][0][0] and not image_full[0][0][1] and not image_full[0][0][2] and not \
                    image_full[-1][0][0] and not image_full[-1][0][1] and not image_full[-1][0][2]:
                        return
                else:
                    return
                """
                img_rgb = cv2.convertScaleAbs(
                    cv2.resize(cv2.cvtColor(image, cv2.COLOR_BGR2RGB),(self.map_canvas.winfo_width()*2**i, self.map_canvas.winfo_height()*2**i)),
                    alpha = 1,
                    beta = 100
                )
                """
                if i != self.zoom_level or (center_lat, center_lon) != (self.center_latitude, self.center_longitude):
                    return
                img_rgb_full = cv2.resize(cv2.cvtColor(image_full, cv2.COLOR_BGR2RGB), (
                    self.map_canvas.winfo_width(), self.map_canvas.winfo_height()))
                img_pil_full = Image.fromarray(img_rgb_full)

                img_tk_full = ImageTk.PhotoImage(img_pil_full)

                self.image_full = img_tk_full
                self.map_canvas.delete("all")
                self.map_canvas.create_image(0, 0, anchor=tk.NW, image=img_tk_full)
                print("full res")
                self.full_res_done = True

                self.visualise_all_polygons()
                if self.current_polygon:
                    while not self.aerial_done:
                        time.sleep(0.2)
                    self.current_polygon.visualise(style="progress")
                self.visualise_contours()
                self.visualise_all_lines()
                if self.current_line:
                    while not self.aerial_done:
                        time.sleep(0.2)
                    self.current_line.visualise(style="progress")
                try:
                    self.grid.visualise()
                except:
                    pass

            try_zooms(self.zoom_level)
            if not tryzoom:
                threading.Thread(target=full_res_thread).start()

    else:
        self.map_canvas.delete("all")
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