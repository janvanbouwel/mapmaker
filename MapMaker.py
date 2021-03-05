import json
import tkinter as tk

import numpy as np
from PIL import ImageTk, Image, ImageDraw


def image_to_grid(room, image: Image):
    arr = np.array(image)

    spawn_pos = None

    out = []
    for y, row in enumerate(arr):
        out.append([])
        for x, cell in enumerate(row):
            if cell.all(0):
                out[-1].append(False)
            else:
                out[-1].append(True)
                if cell[0] == 255 and cell[1] == 0 and cell[2] == 0:
                    if spawn_pos is not None:
                        print(
                            f"Warning, multiple spawn positions in room {room}, fix and export again (bottom right one is included in json)")
                    spawn_pos = {"x": x, "y": y}

    if spawn_pos is None:
        print(f"Warning, no spawn position in room {room}, fix and export again")

    return out, spawn_pos


class MapMaker:
    def __init__(self, master: tk.Tk):
        self.master = master

        self.room_painter = RoomPainter(self, tk.Frame(master))
        self.menu_bar = MenuBar(self, tk.Frame(master))
        self.rl = RoomList(self, tk.Frame(master))

        self.menu_bar.master.grid(row=0, column=0, columnspan=2)
        self.rl.master.grid(row=1, column=0, sticky='n')

        self.room_painter.master.grid(row=1, column=1)

    def new_room(self):
        room_name = self.menu_bar.input.get()
        if room_name == "":
            print("Please fill room name")
            return

        self.rl.add_room(room_name, self.room_painter.image.copy())

        self.menu_bar.input.delete(0, "end")
        self.room_painter.new_image()

    def save(self):
        world_data = {"rooms": []}
        for room in self.rl.rooms:
            layout, spawn_pos = image_to_grid(room, self.rl.rooms[room])
            world_data["rooms"].append({"name": room, 'layout': layout, "spawnPos": spawn_pos})

        with open("world_data.json", "w") as f:
            f.write(json.dumps(world_data))


class RoomPainter:
    scale = 30
    wall = True

    def __init__(self, map_maker: MapMaker, master: tk.Frame):
        self.map_maker = map_maker
        self.master = master

        self.menu_bar = RoomPainterMenuBar(self, tk.Frame(master))
        self.menu_bar.master.grid(row=0, sticky='w')

        self.image_label = tk.Label(master)

        self.image = Image.new('RGB', (0, 0), color=(0, 0, 0))
        self.new_image()

        self.image_label.grid(row=1)

        self.image_label.bind('<Button-1>', self.motion)
        self.image_label.bind('<B1-Motion>', self.motion)
        self.image_label.bind('<Button-3>', self.spawn_pos)

    def new_image(self, size=(10, 10)):
        self.image = Image.new('RGB', size, color=(255, 255, 255))
        self.refresh_image()

    def motion(self, e):
        pos = (int(e.x / self.scale), int(e.y / self.scale))
        color = (0, 0, 0) if self.wall else (255, 255, 255)
        draw = ImageDraw.Draw(self.image)
        draw.point(pos, fill=color)
        del draw
        self.refresh_image()

    def spawn_pos(self, e):
        pos = (int(e.x / self.scale), int(e.y / self.scale))
        color = (255, 0, 0)
        draw = ImageDraw.Draw(self.image)
        draw.point(pos, fill=color)
        del draw
        self.refresh_image()

    def refresh_image(self):
        self.menu_bar.width.config(text=self.image.width)
        self.menu_bar.height.config(text=self.image.height)

        image = ImageTk.PhotoImage(self.image.resize(
            (self.image.width * self.scale, self.image.height * self.scale), Image.BOX), master=self.master)
        self.image_label.configure(image=image)
        self.image_label.image = image

    def set_wall(self):
        self.wall = True
        print("wall selected")

    def set_walkable(self):
        self.wall = False
        print("walkable selected")

    def inc_width(self):
        old_image = self.image
        self.new_image((old_image.width + 1, old_image.height))
        self.image.paste(old_image)
        self.refresh_image()

    def dec_width(self):
        self.image = self.image.crop((0, 0, self.image.width - 1, self.image.height))
        self.refresh_image()

    def inc_height(self):
        old_image = self.image
        self.new_image((old_image.width, old_image.height + 1))
        self.image.paste(old_image)
        self.refresh_image()

    def dec_height(self):
        self.image = self.image.crop((0, 0, self.image.width, self.image.height - 1))
        self.refresh_image()


class RoomPainterMenuBar:
    def __init__(self, room_painter: RoomPainter, master: tk.Frame):
        self.room_painter = room_painter
        self.master = master

        menubar = []

        self.width_label = tk.Label(master, text="Width:")
        self.width = tk.Label(master, text="")
        self.dec_width = tk.Button(master, text="-", command=room_painter.dec_width)
        self.inc_width = tk.Button(master, text="+", command=room_painter.inc_width)

        menubar.append(self.width_label)
        menubar.append(self.width)
        menubar.append(self.dec_width)
        menubar.append(self.inc_width)

        self.height_label = tk.Label(master, text="Height:")
        self.height = tk.Label(master, text="")
        self.dec_height = tk.Button(master, text="-", command=room_painter.dec_height)
        self.inc_height = tk.Button(master, text="+", command=room_painter.inc_height)

        menubar.append(self.height_label)
        menubar.append(self.height)
        menubar.append(self.dec_height)
        menubar.append(self.inc_height)

        self.wall_button = tk.Button(master, text="SetWall", command=room_painter.set_wall)
        menubar.append(self.wall_button)
        self.walkable_button = tk.Button(master, text="SetWalkable", command=room_painter.set_walkable)
        menubar.append(self.walkable_button)

        columns = 0
        for i, obj in enumerate(menubar):
            if isinstance(obj, tk.Entry):
                self.master.grid_columnconfigure(i, weight=1)
            obj.grid(row=0, column=i, sticky="we")
            columns = i


class MenuBar:
    def __init__(self, map_maker: MapMaker, master: tk.Frame):
        self.map_maker = map_maker
        self.master = master

        menubar = []
        self.input = tk.Entry(master)
        menubar.append(self.input)
        self.save_room_button = tk.Button(master, text="Save Room", command=map_maker.new_room)
        menubar.append(self.save_room_button)
        self.save_button = tk.Button(master, text="Save", command=map_maker.save)
        menubar.append(self.save_button)
        self.close_button = tk.Button(master, text="Close", command=master.master.quit)
        menubar.append(self.close_button)

        columns = 0
        for i, obj in enumerate(menubar):
            if isinstance(obj, tk.Entry):
                self.master.grid_columnconfigure(i, weight=1)
            obj.grid(row=0, column=i, sticky="we")
            columns = i


class RoomList:
    def __init__(self, map_maker: MapMaker, master: tk.Frame):
        self.map_maker = map_maker
        self.master = master

        tk.Label(master, text="Rooms:").grid(row=0)
        self.row = 1

        self.rooms = {}

    def add_room(self, name, image):
        if name not in self.rooms:
            tk.Button(self.master, text=name, command=(lambda: self.show_room(name))).grid(row=self.row)
            self.row += 1

        self.rooms[name] = image

    def show_room(self, room):
        self.map_maker.room_painter.image = self.rooms[room]
        self.map_maker.room_painter.refresh_image()
        self.map_maker.menu_bar.input.delete(0, 'end')
        self.map_maker.menu_bar.input.insert(0, room)


def run():
    root = tk.Tk()
    MapMaker(root)
    root.mainloop()
