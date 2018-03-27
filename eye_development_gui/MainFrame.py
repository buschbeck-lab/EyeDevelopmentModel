"""Subclass of MainFrameBase, which is generated by wxFormBuilder."""

from epithelium_backend.Epithelium import Epithelium
from quick_change.FurrowEventList import furrow_event_list
from eye_development_gui.FieldType import FieldType
from eye_development_gui.eye_development_gui import MainFrameBase
import wx
import wx.xrc
from wx.core import TextCtrl


# Implementing MainFrameBase
class MainFrame(MainFrameBase):
    """Wx frame that contains the entire gui.
     Also acts as both the model and the control for the GUI."""

    def __init__(self, parent):
        """Initializes the GUI and all the data of the model."""
        MainFrameBase.__init__(self, parent)

        self.Bind(wx.EVT_CLOSE, self.on_close)

        MainFrame.add_fields(self.m_scrolledWindow4, furrow_event_list)

        self.__active_epithelium = Epithelium(0)  # type: Epithelium
        self._simulating = False

        # Track all the panels that need to be notified when the
        # active epithelium is changed
        self.epithelium_listeners = [self.m_epithelium_gen_display_panel,
                                     self.m_sim_overview_display_panel,
                                     self.m_simulation_display_panel]  # type: list

        # Track panels that can control the simulation of the active epithelium
        # (this is an observer of these objects)
        self.simulation_controllers = [self.m_sim_overview_display_panel,
                                       self.m_simulation_display_panel]  # type: list
        for controller in self.simulation_controllers:
            controller.simulation_listeners.append(self)

        # establish camera listeners
        sim_canvas = self.m_simulation_display_panel.m_epithelium_display.gl_canvas
        overview_canvas = self.m_sim_overview_display_panel.m_epithelium_display.gl_canvas
        generation_canvas = self.m_epithelium_gen_display_panel.gl_canvas
        sim_canvas.camera_listeners.extend((overview_canvas, generation_canvas))
        overview_canvas.camera_listeners.extend((sim_canvas, generation_canvas))
        generation_canvas.camera_listeners.extend((sim_canvas, overview_canvas))

        # Timer for updating the epithelium
        self.simulation_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_epithelium, self.simulation_timer)

    # region dynamic input creation

    @staticmethod
    def create_callback(field_type: FieldType, text_control: wx.TextCtrl):
        """
        Create a callback that validates/sets the field type's value
        when the text_control's input changes.
        """
        def callback(event):
            # If valid, sets the value to it and returns True. Otherwise returns False.
            field_type.validate(text_control.GetLineText(0))
            event.Skip()
        return callback

    @staticmethod
    def add_fields(window: wx.Window, events: list):
        """
        Dynamically generate input fields from the furrow events.

        :param window: the wxform window to add the inputs to.
        :param events: a list of furrow events to generate gui inputs from.
        """
        # This was copied from the dynamically generated code that wxFormBuilder spits out.
        # I don't totally understand it.
        g_sizer = wx.GridSizer(0, 2, 0, 0)
        for event in events:
            for param_name, field_type in event.field_types.items():
                # The left hand side -- the label of the input
                static_text = wx.StaticText(window, wx.ID_ANY, param_name, wx.DefaultPosition, wx.DefaultSize, 0)
                static_text.Wrap(-1)
                g_sizer.Add(static_text, 0, wx.ALL, 5)
                # The right hand side -- the input box
                text_control =  wx.TextCtrl(window , wx.ID_ANY, str(field_type.value), wx.DefaultPosition, wx.DefaultSize, 0 )
                # Bind the input box to the field_type value
                text_control.Bind(wx.EVT_TEXT, MainFrame.create_callback(field_type, text_control))
                g_sizer.Add(text_control, 0, wx.ALL, 5)
        window.SetSizer(g_sizer)
        window.Layout()
        g_sizer.Fit(window)

    # endregion dynamic input creation

    # region event handling

    def ep_gen_create_callback(self, event):
        """
        Callback for ep_gen_create_button. Attempts to create a
        new epithelium from the epithelium generation inputs
        and sets it as the active epithelium. If creation fails the
        user is notified of the invalid parameters.

        Pauses any ongoing simulations.
        """

        # pause any ongoing simulations
        self.simulating = False

        # validate inputs
        if self.ep_gen_input_validation():

            # convert inputs to usable value

            # min cell count
            min_cell_count_str = self.str_from_text_input(self.min_cell_count_text_ctrl)  # type: str
            min_cell_count = int(min_cell_count_str)  # type: int

            # avg cell size
            avg_cell_size_str = self.str_from_text_input(self.avg_cell_size_text_ctrl)  # type: str
            avg_cell_size = float(avg_cell_size_str)

            # cell size variance
            cell_size_variance_str = self.str_from_text_input(self.cell_size_variance_text_ctrl)  # type: str
            cell_size_variance = float(cell_size_variance_str)

            # create epithelium from inputs
            self.active_epithelium = Epithelium(cell_quantity=min_cell_count,
                                                cell_avg_radius=avg_cell_size,
                                                cell_radius_divergence=cell_size_variance/avg_cell_size)

            furrow_velocity_str = self.str_from_text_input(self.furrow_velocity_text_ctrl)
            furrow_velocity = float(furrow_velocity_str)
            self.active_epithelium.furrow.velocity = furrow_velocity

    def on_close(self, event: wx.CloseEvent):
        """Callback invoked when closing the application.
        Halts simulation then allows the default close handler to exit the application."""
        self.simulating = False
        event.Skip()

    def on_ep_gen_user_input(self, event: wx.Event):
        """
        Callback invoked whenever a user alters an epithelium generation input.
        Validates all epithelium generation options.
        :param event: event generated by the user input
        """
        self.ep_gen_input_validation()
        event.Skip()

    # endregion event handling

    # region input validation

    def ep_gen_input_validation(self):
        """validates all epithelium generation inputs"""

        # have to calculate and return values separately to avoid short circuiting the validation
        avg_cell_size = self.validate_ep_gen_avg_cell_size()
        variance = self.validate_ep_gen_cell_size_variance()
        cell_count = self.validate_ep_gen_min_cell_count()
        furrow_velocity = self.validate_ep_gen_furrow_velocity()
        return avg_cell_size and variance and cell_count and furrow_velocity

    def validate_ep_gen_min_cell_count(self) -> bool:
        """Validates user input to min_cell_count_text_ctrl
        :return: Return True if the validation was successful. Return False otherwise.
        """
        min_cell_count_str = self.str_from_text_input(self.min_cell_count_text_ctrl)  # type: str

        validated = True
        try:
            # min cell count must be a positive integer value
            min_cell_count_value = int(min_cell_count_str)
            if min_cell_count_value <= 0:
                validated = False
        except ValueError:
            validated = False

        self.display_text_control_validation(self.min_cell_count_text_ctrl, validated)
        self.min_cell_count_text_ctrl.Refresh()
        return validated

    def validate_ep_gen_avg_cell_size(self) -> bool:
        """
        Validates the user input to avg_cell_size_text_ctrl
        :return: Return True if the validation was successful. Return False otherwise.
        """
        avg_cell_size_str = self.str_from_text_input(self.avg_cell_size_text_ctrl)  # type: str

        try:
            # cell size must be a positive floating point value
            avg_cell_size_value = float(avg_cell_size_str)
            validated = avg_cell_size_value > 0
        except ValueError:
            validated = False

        self.display_text_control_validation(self.avg_cell_size_text_ctrl, validated)
        self.avg_cell_size_text_ctrl.Refresh()
        return validated

    def validate_ep_gen_cell_size_variance(self) -> bool:
        """
        Validates the user input to cell_size_variance_text_ctrl
        :return: Return True if the validation was successful. Return False otherwise.
        """
        variance_str = self.str_from_text_input(self.cell_size_variance_text_ctrl)

        try:
            # variance must be a floating point value
            variance_value = float(variance_str)
            # variance must not be greater than the average cell size
            if self.validate_ep_gen_avg_cell_size():
                avg_size = float(self.str_from_text_input(self.avg_cell_size_text_ctrl))
                validated = variance_value < avg_size
            else:
                # variance cannot be validated if there is an invalid average cell size
                validated = False
        except Exception:
            validated = False

        self.display_text_control_validation(self.cell_size_variance_text_ctrl, validated)
        self.cell_size_variance_text_ctrl.Refresh()
        return validated

    def validate_ep_gen_furrow_velocity(self) -> bool:
        """
        Validates the user input to furrow_velocity_text_ctrl
        :return: Return True if the validation was successful. Return False otherwise.
        """
        velocity_str = self.str_from_text_input(self.furrow_velocity_text_ctrl)

        try:
            # value must be non-zero positive float
            velocity = float(velocity_str)
            validated = velocity > 0
        except Exception:
            validated = False

        self.display_text_control_validation(self.furrow_velocity_text_ctrl, validated)
        return validated

    @staticmethod
    def display_text_control_validation(txt_control: TextCtrl, validated: bool = True) -> None:
        """
        Visualy displays the validation state of a text control
        Controls that have failed validation are displayed red. Controls that have not are displayed
        normally.
        :param txt_control: The validated text control.
        :param validated: The state of the controls validation. True for successful validation.
        False for unsuccessful validation.
        """
        if validated:
            txt_control.SetBackgroundColour(wx.NullColour)
        else:
            txt_control.SetBackgroundColour("Red")

    # endregion input validation

    # region simulation

    @ property
    def active_epithelium(self) -> Epithelium:
        """returns the active epithelium"""
        return self.__active_epithelium

    @ active_epithelium.setter
    def active_epithelium(self, value: Epithelium) -> None:
        """
        Sets the active epithelium and sets the epithelium for
        all listeners.
        :param value: The new active epithelium
        :return: None
        """
        self.__active_epithelium = value

        # notify listeners of change
        for listener in self.epithelium_listeners:
            listener.epithelium = self.__active_epithelium

    def update_epithelium(self, event: wx.EVT_TIMER):
        """Simulates the active epithelium for one tick.
        Draws the updated epithelium."""
        self.active_epithelium.update()
        event.Skip(False)

        for listener in self.epithelium_listeners:
            listener.draw()

    @ property
    def simulating(self) -> bool:
        """Returns true if the active epithelium is being simulated. Returns false otherwise."""
        return self._simulating

    @ simulating.setter
    def simulating(self, simulate: bool) -> None:
        """
        Begins or ends the simulation of the active epithelium.
        :param simulate: begins simulation if true. Ends simulation otherwise.
        :return: None
        """
        self._simulating = simulate
        if simulate and len(self.active_epithelium.cells):
            self.simulation_timer.Start(100)
        else:
            self.simulation_timer.Stop()

    # endregion simulation

    # region misc

    @staticmethod
    def str_from_text_input(txt_control: TextCtrl):
        """
        Returns the string contained by a passed text control.
        :param txt_control: The contents of this TextCtrl will be returned.
        :return: The complete contents of the passed TextCtrl.
        """
        string_value = ''
        for i in range(txt_control.GetNumberOfLines()):
            string_value += txt_control.GetLineText(i)
        return string_value

    # endregion misc
