import wx
from wx import glcanvas

from OpenGL.GL import *
from OpenGL.GLU import *

from legacy_display_2d.LegacyGlDrawingPrimitives import draw_circle
from display_2d.EpitheliumGlTranslator import determine_cell_fill
from display_2d.EpitheliumGlTranslator import determine_cell_color

import math


class LegacyDisplayCanvas(glcanvas.GLCanvas):
    """OpenGL canvas used to display an epithelium"""
    def __init__(self, parent: wx.Panel):
        glcanvas.GLCanvas.__init__(self, parent, size=(parent.GetSize()), name='epithelium_display_canvas')

        # GL
        self.context = None  # type: glcanvas.GLContext
        self.__camera_x = 0  # type: float
        self.__camera_y = 0  # type: float
        self.__scale = 0.001  # type: float

        # event handling
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse_events)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.__panning = False  # type: bool
        self.__last_mouse_position = [0, 0]  # type: list
        self.camera_listeners = []  # type: list

    def on_paint(self, e: wx.PaintEvent):
        """Callback executed when an instance of this widget repaints

        (re)initializes all OpenGL settings and draws the epithelium."""

        # context setup
        self.context = glcanvas.GLContext(self)
        self.SetCurrent(self.context)

        # gl settings
        glClearColor(.9, .9, .9, 1)
        glLoadIdentity()

        # display epithelium
        self._draw_epithelium()

        if e:
            e.Skip(False)

    def on_size(self, e: wx.SizeEvent):
        """Event handler for resizing Does not consume the size event.
        Flags on_paint to fix aspect ratio"""
        self.SetSize(self.GetParent().GetSize())
        e.Skip()

    def on_mouse_events(self, event: wx.MouseEvent):
        """Handle all mouse event logic.
        This includes: camera panning
        :param event: the mouse event to handle
        """

        # get mouse position
        current_mouse_position = [event.GetX(), event.GetY()]

        # left mouse button down
        if event.ButtonDown(wx.MOUSE_BTN_LEFT):
            self.__panning = True

        # left mouse button up
        if event.ButtonUp(wx.MOUSE_BTN_LEFT):
            self.__panning = False

        # mouse drag
        if event.Dragging():

            # panning
            if self.__panning:
                self.pan_camera(self.__last_mouse_position[0] - current_mouse_position[0],
                                -(self.__last_mouse_position[1] - current_mouse_position[1]))

        # scroll wheel
        wheel_rotation = event.GetWheelRotation()
        if wheel_rotation > 0:
            self.set_scale(1.1)
        elif wheel_rotation < 0:
            self.set_scale(0.9)

        # update mouse position
        self.__last_mouse_position = current_mouse_position

    def pan_camera(self, delta_x: float, delta_y: float, active_canvas: bool = True) -> None:
        """Pan the camera by the specified deltas
        :param delta_x: change in the x of the camera
        :param delta_y: change in the y of the camera
        :param active_canvas: An active canvas repaints and signals all of its camera_listeners to pan.
        """

        distance_modifier = 0.01  # type: float

        self.__camera_x += delta_x * distance_modifier
        self.__camera_y += delta_y * distance_modifier

        if active_canvas:
            for listener in self.camera_listeners:
                listener.pan_camera(delta_x, delta_y, False)
            self.on_paint(None)

    def set_scale(self, relative_scale: float, active_canvas: bool = True) -> None:
        """
        Scales the displayed epithelium.
        :param active_canvas: An active canvas repaints and signals all of its camera_listeners to set their scale.
        :param relative_scale: The new scale to display the epithelium
        relative to the current scale. Example: 1.1 will produce a zooming effect
        resulting in a 10% greater scale
        :return:
        """
        self.__scale *= relative_scale
        if active_canvas:
            for listener in self.camera_listeners:
                listener.set_scale(relative_scale, False)
            self.on_paint(None)

    def _draw_epithelium(self) -> None:
        """
        Draws the epithelium stored by this widgets parent.
        Draws the epithelium to a pre-selected GL context.
        :return:
        """

        # camera position
        glMatrixMode(GL_PROJECTION)
        gluLookAt(self.__camera_x, self.__camera_y, 0,  # eye
                  self.__camera_x, self.__camera_y, -1,  # target
                  0, 1, 0)  # up vector
        glScalef(self.__scale, self.__scale, 1)
        gluPerspective(60, self.GetSize().width/self.GetSize().height, 1, 1.1)

        # draw
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_MODELVIEW)
        glLineWidth(2)
        for cell in self.GetParent().epithelium.cells:
            # determine the color of the circle
            color = determine_cell_color(cell)
            fill = determine_cell_fill(cell)
            draw_circle((cell.position_x, cell.position_y), cell.radius, fill, (*color, 1))

        self.SwapBuffers()
