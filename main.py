import os
import sys

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import panda3d.core as p3d
from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import *
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import render2d
from direct.task import Task
from panda3d.core import *
from panda3d.core import TextNode
from panda3d.core import loadPrcFileData
from panda3d.core import WindowProperties
from direct.directtools.DirectGeometry import LineNodePath
from direct.interval.IntervalGlobal import *
from direct.interval.IntervalManager import ivalMgr

from direct.actor.Actor import Actor

from threading import Thread
from time import sleep

loadPrcFileData("", "load-file-type p3assimp")
forward_speed = 5.0 # units per second
backward_speed = 2.0
forward_button = KeyboardButton.ascii_key('w')
backward_button = KeyboardButton.ascii_key('s')

class Game(ShowBase):
    def __init__(self):
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_relative)

        super().__init__(self)
        self.win.requestProperties(props)
        print(self.win)


        self.disableMouse()
        self.setBackgroundColor(0, 0, 0)
        self.setFrameRateMeter(True)
        self.camera.setPos(0, -10, 0)

        self.mpos = (0, 0)
        self.pos = (0, -10, 0)
        # To set relative mode and hide the cursor:







    def render_casino(self):
        # make a floor
        self.floor = self.loader.loadModel("models/floor.egg")
        self.floor.reparentTo(self.render)
        self.floor.setPos(0, 0, 0)
        self.floor.setScale(1, 1, 1)
        self.taskMgr.add(self.camera_control, 'mouse-task')
        self.taskMgr.add(self.move_task, 'move-task')

    def camera_control(self, task):
        if self.mouseWatcherNode.hasMouse():
            _mpos = self.mouseWatcherNode.getMouse()
            self.mpos = (self.mpos[0] + ((_mpos.getX() * -1)*10), self.mpos[1] + ((_mpos.getY())*10))
            if self.mpos[1] > 90:
                self.mpos = (self.mpos[0], 90)
            if self.mpos[1] < -90:
                self.mpos = (self.mpos[0], -90)

            self.camera.setHpr(self.mpos[0], self.mpos[1], 0)
            # move mouse to center
            self.win.movePointer(0, int(self.win.getProperties().getXSize() / 2), int(self.win.getProperties().getYSize() / 2))


        return task.cont

    def move_task(self, task):
        speed = 0.0

        # Check if the player is holding W or S
        is_down = self.mouseWatcherNode.is_button_down

        if is_down(forward_button):
            speed += forward_speed

        if is_down(backward_button):
            speed -= backward_speed

        # Move the player
        y_delta = speed * self.gl.get_dt()
        self.camera.setY(self.camera, y_delta)

g = Game()
g.render_casino()
g.run()


