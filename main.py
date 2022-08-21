import numpy as np
import cv2
import pathlib
import pyautogui
import time
import mouse
from PIL import ImageGrab

import kivy
from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import (Color, Ellipse, Rectangle, Line, Translate, Scale)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.behaviors.togglebutton import ToggleButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.config import Config
from kivy.uix.scatter import Scatter
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ListProperty

from kivy.config import Config
from kivy.core.window import Window
# height = "200"
# width = "400"
#
# Config.set("graphics", "width", width)
# Config.set("graphics", "height", height)
Config.set("graphics", "resizable", 1)
Config.write()

width, height = Window.size

autodrawer = None
accuracy = 2
img = None


class AutoDrawer():
    def __init__(self, img, blur = 3):
        self.img = img
        self.blur = int(blur) * 2 + 1

    def draw_fast(self, pos = None, size = None):
        self.draw(self.draw_point_fast, pos, size)

    def draw_norm(self, pos = None, size = None):
        self.draw(self.draw_point, pos, size)

    def draw(self, draw_p, pos = None, size = None):
        try:
            if size:
                self.img = self.resize_nodisortion(self.img, size)
            self.get_outlines()
            self.get_points(self.outlines)
            point = self.points[np.random.randint(1, len(self.points))]
            i = 0
            time.sleep(3)
            if not pos:
                pos = mouse.get_position()
            print(len(self.points))
            while len(self.points) > 2:
                i += 1
                draw_p(point, pos)
                self.points.remove(point)
                point = self.clossest_point(self.points, point)
                if i % 500 == 0: print(i)
        except:
            print("Something gone wrong")

    def resize_nodisortion(self, im, size):
        h, w = im.shape[:2]
        w_scale = size[0] / w
        h_scale = size[1] / h
        if w_scale <= h_scale:
            return cv2.resize(im, (int(w * h_scale), int(h * h_scale)))
        else:
            return cv2.resize(im, (int(w * w_scale), int(h * w_scale)))

    def get_outlines(self):
        self.gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        self.blured = cv2.GaussianBlur(self.gray, (self.blur, self.blur), 0)
        self.canny = cv2.Canny(self.blured, 100, 120)
        _, self.outlines = cv2.threshold(self.canny, 127, 255, cv2.THRESH_BINARY_INV)

    def draw_point(self, p, pos):
        ps = (p[0] + pos[0], p[1] + pos[1])
        pyautogui.click(ps, button="left")

    def draw_point_fast(self, p, pos):
        ps = (p[0] + pos[0], p[1] + pos[1])
        mouse.move(*ps)
        mouse.click()

    def get_points(self, outl):
        self.points = [(j, i) for i, line in enumerate(outl) for j, x in enumerate(line) if x < 127]
        self.points = list(map(tuple, self.points))
        return self.points

    def clossest_point(self, points, p):
        return min([(self.distance(p, p2), p2) for p2 in points], key=lambda x: x[0])[1]

    def distance(self, p1, p2):
        return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2


class Background(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(.5, .5, .7)
            Rectangle(pos=(0, 0), size=(10000,10000))


class MainScreen(Screen, FloatLayout):
    accuracy: int

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.img = None
        self.accuracy = 2
        self.first = None
        self.second = None
        btn_color = (.56, .44, .67)
        y_btns = 0.65
        self.fc = FileChooserListView(filters = ["*.png", "*.jpg"], on_submit = self.selec)
        self.popup = Popup(
            title = "Choose picture", content = self.fc,
            auto_dismiss = True, size_hint = (0.9, 0.9)
        )
        self.lbl_rd = Label(
            text = "", font_size = width/15,
            size_hint = (0.4, 0.3), pos_hint = {"x": 0.1, "y_center": 0.05}
        )
        clipboard_btn = Button(
            text="From clipboard", size_hint=(0.4, 0.3),
            on_press=self.grab_clipboard, pos_hint={"x": 0.55, "y": y_btns},
            background_color=btn_color,
            font_size=15
        )
        source_btn = Button(
            text="Download\n picture",
            size_hint=(0.4, 0.3), on_press=self.popup.open,
            pos_hint={"x": 0.05, "y": y_btns}, background_color=btn_color,
        )

        l_pad, w_tgl, h_tgl, y_tgl, tgl_color = .05, .18, .2, .35, (.9, .1, .9)
        size_tgl = (w_tgl, h_tgl)

        btn_ideal = ToggleButton(
            text="Ideal", group="res",
            size_hint=size_tgl, pos_hint={"x": l_pad, "y": y_tgl},
            background_color=(0, .8, .8), on_press = self.ideal
        )
        btn_good = ToggleButton(
            text="Good", group="res",
            size_hint=size_tgl, pos_hint={"x": l_pad  + w_tgl, "y": y_tgl},
            background_color=(.1, .9, .4), on_press = self.good
        )
        btn_norm = ToggleButton(
            text="Norm", group="res",
            size_hint=size_tgl, pos_hint={"x": l_pad + 2 * w_tgl, "y": y_tgl},
            background_color=(1, 1, 0), on_press = self.norm
        )
        btn_low = ToggleButton(
            text="Low", group="res",
            size_hint=size_tgl, pos_hint={"x": l_pad + 3 * w_tgl, "y": y_tgl},
            background_color=(.6, .3, .3), on_press = self.low
        )

        btn_draw = Button(
            text = "Draw",
            size_hint = (.25, .25), pos_hint = {"x": .7, "y": .05},
            background_color = (1, .6, .55), on_press = self.draw
        )
        wd = Widget()
        lbl = Label(text = "Target the left-up corner \nof your planing drawing(by right click)", font_size = 20)
        wd.add_widget(lbl)

        self.add_widget(Background())
        self.add_widget(clipboard_btn)
        self.add_widget(source_btn)
        self.add_widget(btn_ideal)
        self.add_widget(btn_good)
        self.add_widget(btn_norm)
        self.add_widget(btn_low)
        self.add_widget(btn_draw)
        self.add_widget(self.lbl_rd)

    def draw(self, instance):
        global sm, autodrawer
        autodrawer = AutoDrawer(self.img, 2 * self.accuracy - 1)
        sm.current = "draw"

    def ideal(self, instance):
        self.accuracy = 1

    def good(self, instance):
        self.accuracy = 2

    def norm(self, instance):
        self.accuracy = 3

    def low(self, instance):
        self.accuracy = 4

    def grab_clipboard(self, instance):
        self.img = ImageGrab.grabclipboard()
        if self.img is None:
            self.lbl_rd.text = "Image loading failed"
            self.lbl_rd.color = (1, 0, 0)
        else:
            if isinstance(self.img, list):
                self.img = cv2.imread(self.img[0])
            else:
                self.img = np.array(self.img)
            self.lbl_rd.text = "Image loaded \nsuccessfully"
            self.lbl_rd.color = (0, 1, 0)
    def selec(self, chooser, selection, *args):
        if len(selection):
            self.img = cv2.imread(selection[0])
            self.popup.dismiss()
            self.lbl_rd.text = "Image loaded successfully"
            self.lbl_rd.color = (1, 1, 1)
        else:
            self.lbl_rd.text = "Image loading failed"
            self.lbl_rd.color = (1, 0, 0)


class DrawScreen(Screen, Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.first = None
        self.second = None
        bl = BoxLayout(orientation = "vertical", padding = 5, spacing = 10)
        bl1 = BoxLayout(orientation = "horizontal", padding = 5, spacing = 0)
        self.lbl = Label(
            text = "1)Firstly, press button 'Start'. \n"
                   "2)After Choose right-top corner by clicking right button of mouse\n"
                   "3)After Сhoose left-bottom corner by clicking right button of mouse\n"
                   "4) Wait a bit and don't touch mouse while app is drawing",
            font_size = Window.width/25,
            size_hint = (1, 0.4), pos_hint = {"center_x": 0.5}
                         )
        self.pict = Image(source = "1_corner.jpg", size_hint = (1, 1))
        btn = Button(
            text = "Back", font_size = 14,
            size_hint = (0.35, 0.35), pos_hint = {"center_x": 0.15, "center_y": 0.5},
            background_color = (.4, .4, .4), on_press = self.back
        )
        btn_start = Button(
            text = "Start", font_size = 20,
            size_hint = (.3, .5), pos_hint = {"center_x": 0.5, "center_y": 0.5},
            on_press = self.first_point, background_color = (.2, .9, .1)
        )
        bl.add_widget(self.lbl)
        bl.add_widget(bl1)
        bl1.add_widget(btn)
        bl1.add_widget(self.pict)
        bl1.add_widget(btn_start)
        self.add_widget(Background())
        self.add_widget(bl)

    def back(self, instance):
        global sm
        sm.current = "main"
        self.first = None
        self.second = None

    def first_point(self, instance):
        time.sleep(0.5)
        self.get_point()
        self.first = mouse.get_position()
        print(self.first)
        self.second_point()

    def second_point(self):
        while mouse.is_pressed(button = "right"):
            pass
        self.get_point()
        self.second = mouse.get_position()
        print(self.second)
        self.draw()

    def get_point(self):
        while not mouse.is_pressed(button = "right"):
            pass

    def draw(self):
        global autodrawer
        time.sleep(2)
        self.size = (abs(self.first[0] - self.second[0]), abs(self.first[1] - self.second[1]))
        autodrawer.draw_fast(pos = self.first, size = self.size)


sm = ScreenManager()
ms = MainScreen(name = "main")
sm.add_widget(ms)
ds = DrawScreen(name = "draw")
sm.add_widget(ds)
sm.current = "main"

class MainApp(App):
    def build(self):
        global sm
        return sm


if __name__ == "__main__":
    MainApp().run()
