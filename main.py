import os
import sys
import random
from typing import Union

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

import quantumrandom


loadPrcFileData("", "load-file-type p3assimp")
forward_speed = 5.0 # units per second
backward_speed = 2.0
forward_button = KeyboardButton.ascii_key('w')
backward_button = KeyboardButton.ascii_key('s')

class Position:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class SlotMachine:
    def __init__(self, cost, winningCombos, name, x, y, z, loader, render, cTrav, collisionHandler, taskMgr):
        self.x = x
        self.y = y
        self.z = z
        self.name = name
        self.loader = loader
        self.obj = self.loader.loadModel("models/slot/scene.gltf")
        self.obj.reparentTo(render)
        self.obj.setPos(self.x, self.y, self.z)
        self.obj.setHpr(0, 90, 0)
        self.obj.setScale(4, 4, 4)
        self.cTrav = cTrav
        self.collisionHandler = collisionHandler
        self.taskMgr = taskMgr
        self.combinations = [0,1,2,3,4,5,6,7,8,9,10,"BAR"]
        self.winningCombinations = winningCombos
        self.cost = cost

        # add a tag to the object
        self.obj.setPythonTag("cost", self.cost)
        self.obj.setPythonTag("winningCombinations", self.winningCombinations)
        self.obj.setPythonTag("id", self.name)

        # use collisionHandler to add a collider to the slot machine

        self.collide = self.obj.attachNewNode(CollisionNode('slot'))
        self.collide.node().addSolid(CollisionBox(Point3(0, 0, -0.5), Point3(1.5, 2, 0.5)))
        self.collisionHandler.addCollider(self.collide, self.obj)
        #self.cTrav.addCollider(self.collide, self.collisionHandler)


    def spin(self):


        slot1 = self.combinations
        slot2 = self.combinations
        slot3 = self.combinations

        slot1 = random.sample(slot1, len(slot1))
        slot2 = random.sample(slot2, len(slot2))
        slot3 = random.sample(slot3, len(slot3))



        print(slot1, slot2, slot3)
        try:
            return self.winningCombinations[f"{slot1[-1]}, {slot2[-1]}, {slot3[-1]}"], slot1, slot2, slot3
        except:
            return None, slot1, slot2, slot3


class ExchangeDesk:
    def __init__(self, x, y, z, collisionHandler, loader, render):
        self.x = x
        self.y = y
        self.z = z

        self.render = render

        self.loader = loader

        self.obj = self.loader.loadModel("models/main_desk/scene.gltf")
        self.obj.reparentTo(self.render)
        self.obj.setPos(self.x, self.y, self.z)
        self.obj.setScale(0.07, 0.07, 0.07)
        self.obj.setHpr(0, 90, 0)
        self.collisionHandler = collisionHandler
        self.collide = self.obj.attachNewNode(CollisionNode('desk'))
        self.collide.node().addSolid(CollisionBox(Point3(-150, 0, -150), Point3(150, 120, 75)))
        self.collisionHandler.addCollider(self.collide, self.obj)

class Game(ShowBase):
    def __init__(self):
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_relative)

        super().__init__(self)
        self.win.requestProperties(props)


        self.disableMouse()
        self.setBackgroundColor(0, 0, 0)
        self.setFrameRateMeter(True)
        self.camera.setPos(0, 0, 2)

        self.mpos = (0, 0)

        self.pos = Position(0, 0, 2)

        # To set relative mode and hide the cursor:

        self.vel = 0.2
        self.jumpHeight = 0.5
        self.jumpVel = 0.3

        self.w = KeyboardButton.ascii_key('w')
        self.a = KeyboardButton.ascii_key('a')
        self.s = KeyboardButton.ascii_key('s')
        self.d = KeyboardButton.ascii_key('d')
        self.space = KeyboardButton.space()

        self.canJump = True

        self.collide = self.camera.attachNewNode(CollisionNode('cam'))
        self.collide.node().addSolid(CollisionSphere(0, 0, 0, 1))
        self.collide.show()



        self.cTrav = CollisionTraverser()
        self.collisionHandler = CollisionHandlerPusher()
        self.cTrav.addCollider(self.collide, self.collisionHandler)
        self.collisionHandler.addCollider(self.collide, self.camera)

        self.collisionHandler.add_in_pattern("%fn-into-%in")
        self.collisionHandler.add_out_pattern("%fn-out-%in")
        self.accept("cam-into-slot", self.collided)
        self.accept("cam-out-slot", self.notCollided)
        self.accept("cam-into-desk", self.collided)
        self.accept("cam-out-desk", self.notCollided)

        self.chips = 1000
        self.money = 1000


        # create a frame that fills up the bottom of the screen
        self.bottomFrame = DirectFrame(frameColor=(1, 1, 1, 1), frameSize=(-1, 1, -1, -0.8))

        self.chipsText = OnscreenText(text=f"Chips: {self.chips}", pos=(-0.9, -0.93), scale=0.1, fg=(0, 0, 0, 1), align=TextNode.ALeft)
        self.moneyText = OnscreenText(text=f"Money: {self.money}", pos=(0.9, -0.93), scale=0.1, fg=(0, 0, 0, 1), align=TextNode.ARight)
        self.chipsText.reparentTo(self.bottomFrame)
        self.moneyText.reparentTo(self.bottomFrame)
        self.popupText = OnscreenText(text="", pos=(0, -0.93), scale=0.07, fg=(1, 0.1, 0.2, 1), align=TextNode.ACenter, mayChange=1)
        self.popupText.reparentTo(self.bottomFrame)
        self.taskMgr.add(self.update_stats, "update_stats")

        self.exchangeDesk = ExchangeDesk(0, 40, -5, self.collisionHandler, self.loader, self.render)


        self.in_menu = False

    def update_stats(self, task):
        self.chipsText.setText(f"Chips: {self.chips}")
        self.moneyText.setText(f"Money: {self.money}")
        return task.cont

    def collided(self, entry):
        if entry.getIntoNodePath().getName() == "slot":
            self.popupText.setText("Press E to play")
            self.accept("e", self.play_slot_machine, extraArgs=[entry.getIntoNodePath().getParent()])
        elif entry.getIntoNodePath().getName() == "desk":
            self.popupText.setText("Press E to exchange")
            self.accept("e", self.exchange)
    def notCollided(self, entry):
        if entry.getIntoNodePath().getName() == "slot":
            self.set_text_after_time("", 0.5, lambda: self.accept("e", self.empty_function))
            self.in_menu = False
        elif entry.getIntoNodePath().getName() == "desk":
            self.set_text_after_time("", 0.5, lambda: self.accept("e", self.empty_function))
            try:
                self.popupScreen.destroy()
            except AttributeError as e:
                print(e)
            self.in_menu = False
    def empty_function(self):
        pass

    def exchange(self):
        self.in_menu = True
        self.popupScreen = DirectFrame(frameColor=(1, 1, 1, 1), frameSize=(-0.5, 0.5, -0.5, 0.5))
        self.popupScreen.setPos(0, 0, 0)

        self.title = OnscreenText(text="Exchange", pos=(0, 0.4), scale=0.1, fg=(0, 0, 0, 1), align=TextNode.ACenter)
        self.title.reparentTo(self.popupScreen)

        self.to_or_from = OnscreenText(text="Chips to Money", pos=(0, 0.2), scale=0.1, fg=(0, 0, 0, 1), align=TextNode.ACenter)
        self.to_or_from.reparentTo(self.popupScreen)

        self.input = DirectEntry(text="", scale=0.1, pos=(-0.4, 0, 0), initialText="0", numLines=1, focus=1, width=8, frameColor=(0, 0, 0, 1), text_fg=(1, 1, 1, 1), text_align=TextNode.ALeft)
        self.input.reparentTo(self.popupScreen)
        self.mode = False
        self.change = DirectButton(text="Change Mode", scale=0.1, pos=(0, 0, -0.2), command=lambda : self.change_mode())
        self.change.reparentTo(self.popupScreen)

        self.convertButton = DirectButton(text="Convert", scale=0.1, pos=(0, 0, -0.4), command=lambda : self.convert(self.input.get(), self.mode))
        self.convertButton.reparentTo(self.popupScreen)

    def change_mode(self):
        if self.mode == False:
            self.to_or_from.setText("Money to Chips")
            self.mode = True
        else:
            self.to_or_from.setText("Chips to Money")
            self.mode = False
    def convert(self, chips, to_chips=False):
        if not to_chips:
            if isinstance(chips, Union[int, float]):
                if self.chips >= int(self.input.get()):
                    self.chips -= int(self.input.get())
                    self.money += int(self.input.get())
                    self.input.enterText("0")
                    self.set_text_after_time("Converted", 0, lambda: self.popupScreen.destroy())
                    self.in_menu = False
                else:
                    self.set_text_after_time("Not enough chips", 0)
                    return
            else:
                try:
                    chips = int(chips)
                    if self.chips >= int(self.input.get()):
                        self.chips -= int(self.input.get())
                        self.money += int(self.input.get())
                        self.input.enterText("0")
                        self.set_text_after_time("Converted", 0, lambda: self.popupScreen.destroy())
                        self.in_menu = False
                    else:
                        self.set_text_after_time("Not enough chips", 0)
                        return
                except ValueError:
                    self.set_text_after_time("Invalid input", 0)
                    return

        else:
            if isinstance(chips, Union[int, float]):
                if self.money >= int(self.input.get()):
                    self.money -= int(self.input.get())
                    self.chips += int(self.input.get())
                    self.input.enterText("0")
                    self.set_text_after_time("Converted", 0, lambda: self.popupScreen.destroy())
                    self.in_menu = False
                else:
                    self.set_text_after_time("Not enough money", 0)
                    return
            else:
                try:
                    chips = int(chips)
                    if self.money >= int(self.input.get()):
                        self.money -= int(self.input.get())
                        self.chips += int(self.input.get())
                        self.input.enterText("0")
                        self.set_text_after_time("Converted", 0, lambda: self.popupScreen.destroy())
                        self.in_menu = False
                    else:
                        self.set_text_after_time("Not enough money", 0)
                        return
                except ValueError:
                    self.set_text_after_time("Invalid input", 0)
                    return


    def play_slot_machine(self, slotObj):
        winningCombos = slotObj.getPythonTag("winningCombinations")
        cost = slotObj.getPythonTag("cost")

        if self.chips >= cost:
            self.chips -= cost
            slot = self.slots[slotObj.getPythonTag("id")]
            winnings, slot1, slot2, slot3 = slot.spin()

            print(winnings)


        else:
            self.set_text_after_time("Not enough chips", 0, lambda: self.set_text_after_time("Press E to play", 1))
            return





    def set_text_after_time(self, text, time, after=None):
        self.taskMgr.doMethodLater(time, self.set_text, "set_text", extraArgs=[text, after])

    def set_text(self, text, after=None):
        self.popupText.setText(text)
        if after is not None:
            after()
    def render_casino(self):
        # make a floor



        model = self.loader.loadModel("models/casino/scene.gltf")
        model.reparentTo(self.render)
        model.setScale(0.1, 0.1, 0.1)
        model.setHpr(0, 90, 0)
        model.setPos(0, 0, -5)

        wall1Collider = model.attachNewNode(CollisionNode('wall1'))
        wall1Collider.node().addSolid(CollisionInvSphere(0, 0, 0, 500))
        # add a floor collider
        wall1Collider.node().addSolid(CollisionBox(Point3(-500, 0, -500), Point3(500, 5, 500)))
        wall1Collider.setPos(0, 0, 0)


        self.cTrav.addCollider(wall1Collider, self.collisionHandler)
        self.collisionHandler.addCollider(wall1Collider, model)




        self.slot1 = SlotMachine(10, {"7, 7, 7":50, "3, 3, 3":20, "2, 2, 2":10, "1, 1, 1":5, "0, 0, 0":2, "BAR, 7, 7":10, "BAR, 3, 3":5, "BAR, 2, 2":3, "BAR, 1, 1":2, "BAR, 0, 0":1, "2, BAR, 2": 5, "3, BAR, 3": 10, "7, BAR, 7": 20, "BAR, BAR, BAR": 100},
                                 "slot1", -45, 0, -5, self.loader, self.render, self.cTrav, self.collisionHandler, self.taskMgr)
        self.slot2 = SlotMachine(20, {"7, 7, 7":50, "3, 3, 3":20, "2, 2, 2":10, "1, 1, 1":5, "0, 0, 0":2, "BAR, 7, 7":10, "BAR, 3, 3":5, "BAR, 2, 2":3, "BAR, 1, 1":2, "BAR, 0, 0":1, "2, BAR, 2": 5, "3, BAR, 3": 10, "7, BAR, 7": 20, "BAR, BAR, BAR": 100},
                                "slot2", -42, 7, -5, self.loader, self.render, self.cTrav, self.collisionHandler, self.taskMgr)
        self.slot3 = SlotMachine(40, {"7, 7, 7":50, "3, 3, 3":20, "2, 2, 2":10, "1, 1, 1":5, "0, 0, 0":2, "BAR, 7, 7":10, "BAR, 3, 3":5, "BAR, 2, 2":3, "BAR, 1, 1":2, "BAR, 0, 0":1, "2, BAR, 2": 5, "3, BAR, 3": 10, "7, BAR, 7": 20, "BAR, BAR, BAR": 100},
                                "slot3", -42, -7, -5, self.loader, self.render, self.cTrav, self.collisionHandler, self.taskMgr)

        self.slots = {"slot1":self.slot1, "slot2":self.slot2, "slot3":self.slot3}


        self.taskMgr.add(self.camera_control, 'mouse-task')
        self.taskMgr.add(self.gravity, 'gravity-task')
        self.taskMgr.add(self.looking_at, 'looking-task')
        t = Thread(target=self.move_task, daemon=True)
        t.start()

    def gravity(self, task):
        pass


        return task.cont
    def camera_control(self, task):
        if self.mouseWatcherNode.hasMouse() and self.in_menu == False:
            props = WindowProperties()
            props.setCursorHidden(True)
            self.win.requestProperties(props)

            _mpos = self.mouseWatcherNode.getMouse()
            self.mpos = (self.mpos[0] + ((_mpos.getX() * -1)*10), self.mpos[1] + ((_mpos.getY())*10))

            # make the camera not be able to move up or down more than 90 degrees
            if self.mpos[1] > 90:
                self.mpos = (self.mpos[0], 90)
            elif self.mpos[1] < -90:
                self.mpos = (self.mpos[0], -90)


            self.camera.setHpr(self.mpos[0], self.mpos[1], 0)
            # move mouse to center
            self.win.movePointer(0, int(self.win.getProperties().getXSize() / 2), int(self.win.getProperties().getYSize() / 2))

        else:
            # unhide the mouse
            props = WindowProperties()
            props.setCursorHidden(False)
            self.win.requestProperties(props)


        return task.cont

    def move_task(self):
        while True:

            if not self.in_menu:
                is_down = self.mouseWatcherNode.is_button_down

                quat = self.camera.getQuat()

                forwardVec = quat.getForward()
                forwardVec.normalize()

                # get the other vectors based on the forward vector
                backwardVec = forwardVec * -1
                rightVec = forwardVec.cross(Vec3.up())
                leftVec = rightVec * -1


                if is_down(self.w):
                    self.pos.x += forwardVec.getX() * self.vel
                    self.pos.y += forwardVec.getY() * self.vel
                    #self.pos.z += forwardVec.getZ() * self.vel

                if is_down(self.s):
                    self.pos.x += backwardVec.getX() * self.vel
                    self.pos.y += backwardVec.getY() * self.vel
                    #self.pos.z += backwardVec.getZ() * self.vel

                if is_down(self.a):
                    self.pos.x += leftVec.getX() * self.vel
                    self.pos.y += leftVec.getY() * self.vel
                    #self.pos.z += leftVec.getZ() * self.vel

                if is_down(self.d):
                    self.pos.x += rightVec.getX() * self.vel
                    self.pos.y += rightVec.getY() * self.vel
                    #self.pos.z += rightVec.getZ() * self.vel

                if is_down(self.space):
                    t = Thread(target=self.jump, daemon=True)
                    t.start()






                sleep(0.01)
            self.camera.setPos(self.pos.x, self.pos.y, self.pos.z)

    def jump(self):
        return
        if not self.canJump:
            return
        self.canJump = False
        i = 0
        while i < self.jumpHeight:
            self.pos.z += self.jumpVel
            self.camera.setPos(self.pos.x, self.pos.y, self.pos.z)
            i += self.jumpVel
            sleep(0.01)

    def looking_at(self, task):






        return task.cont






g = Game()
g.render_casino()
g.run()


