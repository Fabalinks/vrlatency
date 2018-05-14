from abc import abstractmethod
import pyglet
import serial
import random
import numpy as np
# import pandas as pd
import ratcave as rc
import VRLatency as vrl
from struct import unpack
from itertools import cycle


# from Stimulus import *

class Device(object):
    """ Handles attributes and methods related to stimulation/recording device

    Attributes:
        channel:
        is_connected (bool):

    """

    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.channel = serial.Serial(self.port, baudrate=self.baudrate, timeout=2.)
        self.channel.readline()

    @staticmethod
    def find_all():
        """ Display a list of connected devices to the machine

        Returns:
            list of the ports and the connected devices to this machine

        """
        raise NotImplementedError()

    def disconnect(self):
        """Disconnect the device."""
        self.channel.close()

    @property
    def is_connected(self):
        return self.channel.isOpen()

    def read(self, n_points=240, packet_fmt='I2H'):
        return unpack('<' + packet_fmt * n_points, self.channel.read(8 * n_points))


class Window(pyglet.window.Window):
    """ Window object for the experiment

    Attributes:

    """

    def __init__(self, screen_ind=0, resizable=False, fullscreen=False, *args, **kwargs):
        """ initialize window object

        Args:
            screen_ind: inidicate which screen must contain the created window (if you have more than one screen)
            resizable: in case a resizable window is required, set this to True (default is False)
            fullscreen: for a fullscreen window, set this to True (default is False)
            args and kwargs: all other inputs that pyglet window objects can accept (look into pyglet documentaion)

        """
        platform = pyglet.window.get_platform()
        display = platform.get_default_display()
        screen = display.get_screens()[screen_ind]
        super().__init__(screen=screen, resizable=resizable, fullscreen=fullscreen, *args, **kwargs)


class Stim():
    """ initialize an stimulation object

    Attributes:
        mesh: the object appearing on the screen

    """
    def __init__(self, type='Plane', position=(0, 0)):
        self.mesh = rc.WavefrontReader(rc.resources.obj_primitives).get_mesh(type, drawmode=rc.POINTS, position=(0, 0, -3))
        self.position = position

    @property
    def position(self):
        return self.mesh.position.xy

    @position.setter
    def position(self, value):
        self.mesh.position.xy = value

    def draw(self):
        self.mesh.draw()


class Data(object):
    """ Data object handling data-related matters

    Attributes:
        _array: stores the recorded data during the experiment (if record is set to True, and there exist a recording device)

    """

    def __init__(self):

        self._array = []

    @property
    def array(self):
        return self._array

    def record(self):
        raise NotImplementedError()

    def store(self):
        raise NotImplementedError()

        # dd = np.array(data).reshape(-1, 3)
        # df = pd.DataFrame(data=dd, columns=['Time', "Chan1", 'Trial'])
        # df.to_csv('../Measurements/' + filename + '.csv', index=False)

    def analyze(self):
        raise NotImplementedError()


class BaseExperiment(object):
    """ Experiment object integrates other components and let's use to run, record and store experiment data

    """
    def __init__(self, window, device, trials=20, stim=None, n_points=None, packet_fmt=None, on_width=.5, off_width=.5):
        """ Initialize an experiment object

        Args:
                - trials: number of trials
                - filename: name for the recorded data
                - path: path for saving the recorded data (if not given it will be saved in current directory)
        """

        # create window
        self.device = device
        self.window = window
        self.stim = stim
        self.n_points = n_points
        self.packet_fmt = packet_fmt

        # create Data object
        self.data = Data()

        self.trials = trials
        self._trial = 0
        self.__last_trial = self._trial
        self.on_width = _gen_iter(on_width)
        self.off_width = _gen_iter(off_width)

        self._init_window_events()

    @property
    def trial(self):
        return self._trial

    def _init_window_events(self):
        @self.window.event
        def on_draw():
            self.window.clear()
            with rc.default_shader:
                self.stim.draw()
                self.send_msg_on_draw()

    def start_next_trial(self, dt):
        self._trial += 1
        if self.stim:
            self.stim.visible = True
        self.paradigm()
        pyglet.clock.schedule_once(self.end_trial, next(self.on_width))

    def end_trial(self, dt):
        if self.stim:
            self.stim.visible = False
        if self.device:
            dd = self.device.read(n_points=self.n_points, packet_fmt=self.packet_fmt)
            self.data.array.extend(dd)
        if self._trial > self.trials:
            pyglet.app.exit()  # exit the pyglet app
            if self.device:
                self.device.disconnect()  # close the serial communication channel
        pyglet.clock.schedule_once(self.start_next_trial, next(self.off_width))

    def run(self, record=False):
        """ runs the experiment in the passed application window

        Input:

        return:

        """

        if record and (self.device is None):
            self.window.close()
            raise ValueError("No recording device attached.")


        # run the pyglet application
        pyglet.clock.schedule(lambda dt: dt)
        pyglet.clock.schedule_once(self.start_next_trial, 0)
        pyglet.app.run()

    def paradigm(self):
        pass

    def send_msg_on_draw(self):
        pass


def _gen_iter(vals):
    if not hasattr(vals, '__iter__'):
        for val in cycle([vals]):
            yield val
    elif len(vals) == 2:
        while True:
            yield random.uniform(vals[0], vals[1])
    else:
        raise TypeError("'vals' must contain one or two values")




class DisplayExperiment(BaseExperiment):
    """ Experiment object to measure display latency measurement

    """

    def __init__(self, window, device, n_points=240, packet_fmt='I2H', *args, **kwargs):
        super(self.__class__, self).__init__(window, device, n_points=n_points, packet_fmt=packet_fmt, *args, **kwargs)


    def paradigm(self):
        print('Starting Trial', self._trial)

class TrackingExperiment(BaseExperiment):
    """ Experiment object for tracking latency measurement

    """
    def _init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

    def paradigm(self):
        raise NotImplementedError()


class TotalExperiment(BaseExperiment):
    """ Experiment object for total latency measurement

    """

    def _init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

    def paradigm(self):
        vrl.Stim_without_tracking(window=self.window, mesh=self.stim.mesh)
        # while len(self.data) < TOTAL_POINTS * 11:
        #     self.data.extend(unpack('<' + 'I3H?' * POINTS, device.read(11 * POINTS)))
