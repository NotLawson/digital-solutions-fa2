## Digital Soltions FA2
import os, sys, asyncio
import pygame as pg
import json
from storage import Storage
#from auth import Auth

class Tilemap:
    # Tile types
    #
    # 0. Walkable - Player is able to move to this tile
    # 1. Solid - Player is unable to move to this tile
    # 2. Stateful
    def __init__(self, filepath):
        self._filepath = filepath
        self._data = json.load(filepath.open())
        self.tilemap = self._data["tilemap"]
        self.spawn = self._data["spawn"]
        self.assets = self._data["assets"]

    def getTile(self, id: int):
        return pg.image.load(self.assets[int])
    
class Player:
    coords: tuple = (None, None)
    def __init__(self, assets: dict):
        self.assets = assets
    



class Game:
    state: int = 0
    # 0: Initialize, 1: Main Menu, 2: Loading, 3: In-game, 4: Dialogue, 5: Event, 6: Pause, 7: Quit
    QUIT: bool = False
    KEYS: list = []
    MOUSE: list = [False, False, 0, 0]
    CURRFUNC = None
    FPS: int = 120
    FLOW_FIRST_ITERATION: bool = True
    
    
    screen: pg.Surface
    storage: Storage

    def __init__(self):
        # init pygame
        pg.init()

        # set screen
        self.screen = pg.display.set_mode()

        # init storage
        self.storage = Storage()

        # set the intitalisation screen
        self.set_flow(self.FLOW_START_ANIMATION)

    def set_flow(self, flow):
        self.FLOW_FIRST_ITERATION = True
        self.CURRFUNC = flow
        
    async def mainloop(self):
        # mainloop
        while True:
            # Handle Event Loop
            for event in pg.event.get():
                match event.type:
                    case pg.QUIT:
                        self.QUIT = True
                    case pg.KEYDOWN:
                        self.KEYS.append(event.key)
                    case pg.KEYUP:
                        self.KEYS.remove(event.key)
                    case pg.MOUSEBUTTONDOWN:
                        match event.button:
                            case 3: # right click
                                pass
                            case _: # left click + others
                                pass
                    case pg.MOUSEBUTTONUP:
                        match event.button:
                            case 3: # right click
                                pass
                            case _: # left click + others
                                pass
                    case pg.MOUSEMOTION:
                        self.MOUSE[2] = event.pos[0]
                        self.MOUSE[3] = event.pos[1]
            
            # call current function
            self.CURRFUNC()

            if self.QUIT or (pg.K_ESCAPE in self.KEYS): return
            await self.update()
            await asyncio.sleep(1 / self.FPS)
    
    async def update(self):
        # push display changes
        pg.display.update()


    # Flows
    def FLOW_START_ANIMATION(self):
        if self.FLOW_FIRST_ITERATION:
            self.BRIGHTNESS = 0
            self.i = 0
            self.FLOW_FIRST_ITERATION = False
        
       
        if self.BRIGHTNESS >= 248:
            self.BRIGHTNESS = 255
        elif self.BRIGHTNESS < 255:
            self.BRIGHTNESS += 3
        
        if self.BRIGHTNESS == 255:
            # end of animation
            if self.i >= 50:
                # end sequence
                self.set_flow(self.FLOW_TUTORIAL)
            self.i += 1

        b = self.BRIGHTNESS
        self.screen.fill((b, b, b))

    def FLOW_TUTORIAL(self):
        if self.FLOW_FIRST_ITERATION:
            self.FADE_ANIMATION_ACTIVE = True
            self.i = 0
            self.FLOW_FIRST_ITERATION = False
        
        # blank the screen 
        self.screen.fill("black")
        


        # fade animation
        if self.FADE_ANIMATION_ACTIVE and (self.BRIGHTNESS > 0):
            surf = pg.Surface((self.screen.get_width(), self.screen.get_height()))
            surf.set_alpha(self.BRIGHTNESS)
            surf.fill((255, 255, 255))
            self.screen.blit(surf, (0,0))
            self.BRIGHTNESS -= 5
        elif self.FADE_ANIMATION_ACTIVE: # fully invisible
            self.FADE_ANIMATION_ACTIVE = False
        




async def start():
    game = Game()
    await game.mainloop()
    pg.quit()


if __name__ == "__main__":
    asyncio.run(start())