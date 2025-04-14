import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont

class LayerContainer:
    def __init__(self, parent, text, checkboxcommand = None, settings = None, delete = None, barren = False):


        self.parent = parent
        if type(parent) == LayerContainer:
            self.separator = ttk.Separator(parent.container_frame, orient='horizontal')
            self.frame_main = tk.Frame(parent.container_frame, padx = 0, pady = 0)
        else:
            self.separator = ttk.Separator(parent, orient='horizontal')
            self.frame_main = tk.Frame(parent, padx=0, pady=0)
        self.separator.pack(fill='x', pady=0)
        self.frame_main.pack(fill="x", side = tk.TOP)
        self.frame_top = tk.Frame(self.frame_main, padx = 0, pady = 0)
        self.frame_top.pack(fill="x", side=tk.TOP)
        self.checkbox_command = checkboxcommand
        self.check = tk.IntVar(value=1)
        self.children = []
        if barren == False:
            self.expand_button = tk.Button(self.frame_top, text='▶', anchor="w", bd=0, highlightthickness=0,
                                       command=self._expand, width=3)

            self.expand_button.pack(side=tk.LEFT)
            self.checkbox = tk.Checkbutton(self.frame_top, text=text, variable=self.check, onvalue=1, offvalue=0, command = checkboxcommand)
            self.checkbox.pack(side=tk.LEFT, anchor="w")



        else:
            self.frame_top_move = tk.Frame(self.frame_top, width = 10)
            self.frame_top_move.pack(side=tk.LEFT)
            self.checkbox = tk.Checkbutton(self.frame_top, text="", variable=self.check, onvalue=1, offvalue=0,
                                           command=checkboxcommand)
            self.checkbox.pack(side=tk.LEFT, anchor="w")
            self.name = tk.Entry(self.frame_top, bd = 0, highlightthickness=0)
            self.name.pack(side=tk.LEFT, anchor = "w")
            self.name.insert(0,text)
            self.name.config(state = "disabled")
            self.child_no = len(self.parent.children)
            def adjust_width(event=0):
                # Get the current text from the Entry
                entry = self.name
                text = entry.get()

                # Create a font object based on the Entry's font
                font = tkFont.Font(font=entry['font'])

                # Measure the width of the text in pixels
                text_width = 2 + font.measure(text)*2 - int(font.measure(text)/10)

                # Adjust the entry width accordingly (divide by 10 for character count)
                # The division factor can be tweaked based on font size
                entry.config(width=(text_width // 10))

            adjust_width()

            self.name.bind("<KeyRelease>", adjust_width)
            def state_normal(event = 0):
                self.name.config(state = "normal")
            def state_readonly(event = 0):
                self.name.config(state = "readonly")
            self.name.bind("<Button-1>", state_normal)
            self.name.bind("<Return>", state_readonly)

        if delete:
            def delete_command():
                delete()
                self.frame_main.pack_forget()
                self.separator.pack_forget()
                #print(self.parent.container_frame.winfo_children())
                """
                if len(self.parent.container_frame.winfo_children()) < 3:
                    self.parent.expand_button.config(text='▶')
                    self.parent.frame_bottom.pack_forget()
                """
                initial_length = len(self.parent.children)
                for i in range(initial_length):
                    if self == self.parent.children[initial_length-i-1]:
                        del self.parent.children[initial_length-i-1]
                if not self.parent.children:
                    self.parent._expand()
            self.delete_button = tk.Button(self.frame_top, text = "\u2716", command = delete_command, bd = 0, highlightthickness=0)
            self.delete_button.pack(side=tk.RIGHT, anchor="e")

        if settings:
            self.settings_button = tk.Button(self.frame_top, text = "\u2699", command = settings, bd = 0, highlightthickness=0)
            self.settings_button.pack(side = tk.RIGHT, anchor = "e")


        self.frame_bottom = tk.Frame(self.frame_main, padx = 0, pady = 0)
        self.frame_bottom.pack(fill="x", side=tk.TOP)

        self.dummy_frame = tk.Frame(self.frame_bottom, width=5)
        self.dummy_separator = ttk.Separator(self.frame_bottom, orient='vertical')

        self.container_frame = tk.Frame(self.frame_bottom, padx = 0, pady = 0)

        if not checkboxcommand:
            def checkboxcommand_total():
                def update_children(layer):
                    print(text)
                    if layer.check.get() == 1:  # If parent is ticked
                        print(text)
                        for child in layer.children:
                            # Only select and call the command if the child is not already selected
                            if child.check.get() != 1:
                                child.checkbox.select()  # Tick child checkbox
                            if child.checkbox_command:  # If the child has a command
                                child.checkbox_command()  # Manually call the child's command
                            update_children(child)  # Recurse for children's children
                    else:  # If parent is unticked
                        for child in layer.children:
                            # Only deselect and call the command if the child is not already deselected
                            if child.check.get() != 0:
                                child.checkbox.deselect()  # Untick child checkbox
                            if child.checkbox_command:  # If the child has a command
                                child.checkbox_command()  # Manually call the child's command
                            update_children(child)  # Recurse for children's children

                # Start updating children recursively
                update_children(self)

            # Save the original command to manually invoke later
            self.checkbox_command = self.checkbox.cget('command')
            # Set the parent's checkbox command to update the children
            self.checkbox.config(command=checkboxcommand_total)

        if type(parent) == LayerContainer:
            self.parent.append(self)

    def update_display(self):
        for child in self.children:
            child.frame_main.pack_forget()  # Hide all
            child.separator.pack_forget()
        for child in self.children:
            child.separator.pack(fill='x', pady=0)
            child.frame_main.pack(fill="x", side=tk.TOP)


    def _expand(self):
        if self.expand_button.cget('text') == '▶' and self.children:
            self.expand_button.config(text='▼')
            self.frame_bottom.pack(fill="x", side=tk.TOP)
            self.dummy_separator.pack(fill='y', padx=7, pady = 7, side=tk.LEFT)
            self.dummy_frame.pack(side=tk.LEFT)
            self.container_frame.pack(fill = "x", side=tk.LEFT)
        elif self.expand_button.cget('text') == '▼':
            self.expand_button.config(text='▶')
            self.frame_bottom.pack_forget()
        return

    def append(self, child):
        self.children.append(child)