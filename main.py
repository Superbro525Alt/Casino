import os
import sys
import random

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

import pygame
from pygame.locals import *
# import K_LEFT
pygame.init()

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
    def __init__(self, x, y, z, loader, render, cTrav, collisionHandler):
        self.x = x
        self.y = y
        self.z = z
        self.loader = loader
        self.obj = self.loader.loadModel("models/slot/scene.gltf")
        self.obj.reparentTo(render)
        self.obj.setPos(self.x, self.y, self.z)
        self.obj.setHpr(0, 90, 0)
        self.obj.setScale(4, 4, 4)
        self.cTrav = cTrav
        self.collisionHandler = collisionHandler
        self.combinations = [0,1,2,3,4,5,6,7,8,9,10,"BAR"]
        self.winningCombinations = {"7, 7, 7":50, "3, 3, 3":20, "2, 2, 2":10, "1, 1, 1":5, "0, 0, 0":2, "BAR, 7, 7":10, "BAR, 3, 3":5, "BAR, 2, 2":3, "BAR, 1, 1":2, "BAR, 0, 0":1, "2, BAR, 2": 5, "3, BAR, 3": 10, "7, BAR, 7": 20, "BAR, BAR, BAR": 100}

    def spin(self):
        slot1 = self.combinations
        slot2 = self.combinations
        slot3 = self.combinations

        random.shuffle(slot1)
        random.seed(random.randint(0, 100))
        random.shuffle(slot2)
        random.seed(random.randint(0, 100))
        random.shuffle(slot3)

        print(slot1, slot2, slot3)
        try:
            print(self.winningCombinations[f"{slot1[-1]}, {slot2[-1]}, {slot3[-1]}"])
        except:
            print("No win")



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




    def add_box_collider(self, model):


        # these collisions dont work if the model is in negative space

        cnodePath = model.attachNewNode(CollisionNode('cnode'))
        self.cTrav.addCollider(cnodePath, self.collisionHandler)
        self.collisionHandler.addCollider(cnodePath, model)

        # Get the model's bounds in model space
        bounds = model.get_tight_bounds()

        # Get the model's transformation
        transform = model.get_transform().get_mat()

        # Calculate the transformed bounding box
        min_point = Point3(bounds[0])
        max_point = Point3(bounds[1])
        min_point = transform.xform_point(min_point)
        max_point = transform.xform_point(max_point)

        # Create the collider using the transformed bounding box\
        if model.get_pos() == (0, 0, 0):
            print("0")
            cnodePath.node().addSolid(CollisionBox(min_point, max_point))
        else:
            # move the min and max points to the model's position based off distance from 0, 0, 0


            if model.get_pos().getX() > 0 and model.get_pos().getY() > 0:
                cnodePath.node().addSolid(CollisionBox(min_point + model.get_pos(), max_point + model.get_pos()))
            elif model.get_pos().getX() < 0 and model.get_pos().getY() > 0:
                cnodePath.node().addSolid(CollisionBox(min_point + model.get_pos(), max_point + model.get_pos()))
            elif model.get_pos().getX() < 0 and model.get_pos().getY() < 0:
                cnodePath.node().addSolid(CollisionBox(min_point + model.get_pos(), max_point + model.get_pos()))
            elif model.get_pos().getX() > 0 and model.get_pos().getY() < 0:
                cnodePath.node().addSolid(CollisionBox(min_point + model.get_pos(), max_point + model.get_pos()))
            else:
                cnodePath.node().addSolid(CollisionBox(min_point + model.get_pos(), max_point + model.get_pos()))



        cnodePath.show()




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




        self.slot1 = SlotMachine(-45, 0, -5, self.loader, self.render, self.cTrav, self.collisionHandler)
        self.slot2 = SlotMachine(-42, 7, -5, self.loader, self.render, self.cTrav, self.collisionHandler)
        self.slot3 = SlotMachine(-42, -7, -5, self.loader, self.render, self.cTrav, self.collisionHandler)

        self.slot1.spin()
        self.slot2.spin()
        self.slot3.spin()


        self.taskMgr.add(self.camera_control, 'mouse-task')
        self.taskMgr.add(self.gravity, 'gravity-task')
        t = Thread(target=self.move_task, daemon=True)
        t.start()

    def gravity(self, task):
        pass


        return task.cont
    def camera_control(self, task):
        if self.mouseWatcherNode.hasMouse():
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


        return task.cont

    def move_task(self):
        while True:


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



            self.camera.setPos(self.pos.x, self.pos.y, self.pos.z)



            sleep(0.01)

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







g = Game()
g.render_casino()
g.run()


