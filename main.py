## Digital Soltions FA2
import os, sys, asyncio
import pygame as pg
import pathlib as pl
import json
import queue
import csv
import math
from storage import Storage, AssetManager
#from auth import Auth

class Game:
    MAP = None
    PLAYER = {
        "pos": (None, None),
        "sprite": None
    }
    OBJECTIVE = {}
    STORY = 0
    DECISIONS = []

    # Story Element: objectives, cutscenes, etc.
    # Stages: tilemaps, minigames

    def __init__(self):
        pass

    def progress_story(self):
        pass

    def load_map(self, map):
        pass

    def move_player(self, vector: pg.Vector2):
        pass


# Tilemaps
class TileSprite:
    def __init__(self, tileset: pg.Surface, id: int):
        self.surface = pg.Surface((32, 32))
        if id != -1:
            self.surface.blit(tileset, -1 * pg.Vector2(32 * int(id), 0))

class Tilemap:
    def __init__(self, path: pl.Path, tileset: pg.Surface):
        self.map = []
        self.tileset = tileset
        with path.open("r") as f:
            self.csv = csv.reader(f.readlines())

        size = [0, 0]
        for row in self.csv:
            size[1] += 1
            size[0] = 0
            r = []
            for tile in row:
                size[0] += 1
                r.append(TileSprite(self.tileset, tile))
            self.map.append(r)

        self.w = size[0] * 32
        self.h = size[1] * 32
    
    def draw(self, screen: pg.Surface):
        c = pg.Vector2((32, 0))
        r = pg.Vector2((0, 32))
        current_r = pg.Vector2((0, 0))
        map_surface = pg.Surface((self.w, self.h))
        for row in self.map:
            current_c = pg.Vector2((0, 0))
            for col in row:
                map_surface.blit(col.surface, current_r + current_c)
                current_c += c
            current_r += r


        print("screen:", (screen.get_width(), screen.get_height()), "map(w):", (pg.transform.scale_by(map_surface, screen.get_width() / self.w).get_width(), pg.transform.scale_by(map_surface, screen.get_width() / self.w).get_height()))
        if pg.transform.scale_by(map_surface, screen.get_width() / self.w).get_height() > screen.get_height():
            # scale to height
            print("h")
            screen.blit(pg.transform.scale_by(map_surface, screen.get_height() / self.h), pg.Vector2(0, 0))
            return
        print("w")
        screen.blit(pg.transform.scale_by(map_surface, screen.get_width() / self.w).get_height(), pg.Vector2(0, 0))

class App:
    FPS: int = 60
    #SCREEN: pg.Surface = pg.display.set_mode((1600, 900), pg.RESIZABLE)
    DISPLAY: pg.Surface = pg.display.set_mode((1600, 900), pg.RESIZABLE)
    DISPLAY_RATIO: tuple = (16 / 9, 9 / 16)
    SCREEN: pg.Surface = pg.Surface((DISPLAY.get_width(), DISPLAY.get_height()))
    PADDING_VECTOR: pg.Vector2 = pg.Vector2((0, 0))
    STORAGE: Storage = Storage()
    ASSETS: AssetManager = AssetManager(json.load(pl.Path("assets/inventory.json").open("r")))
    GAME: Game = Game()
    NEXT = queue.Queue()

    def __init__(self):
        pg.init()
        self.NEXT.put(self.STATE_intro)

    # Utils
    async def tick(self):
        self.DISPLAY.fill((0, 0, 0))
        self.DISPLAY.blit(self.SCREEN, self.PADDING_VECTOR)
        pg.display.update()
        await asyncio.sleep(1 / self.FPS)

    async def window_resize(self, size: tuple):
        size = list(size)
        # ensure h & w are even
        if size[0] % 2 != 0:
            size[0] -= 1
        if size[1] % 2 != 0:
            size[1] -= 1
        
        # match height
        h = size[0] * self.DISPLAY_RATIO[1] # h = w * (9/16)
        if h <= size[1]:
            self.SCREEN = pg.Surface((size[0], h))
            # find the padding vector
            self.PADDING_VECTOR = pg.Vector2((0, (size[1] - h) / 2))
            print('h', self.PADDING_VECTOR, size[1], h)
        else:
            # match width
            w = size[1] * self.DISPLAY_RATIO[0] # w = h * (16/9)
            self.SCREEN = pg.Surface((w, size[1]))
            # find the padding vector
            self.PADDING_VECTOR = pg.Vector2(((size[0] - w) / 2, 0))
            print('w', self.PADDING_VECTOR, size[0], w)

    async def BASIC_EVENT_HANDLE(self):
        for event in pg.event.get():
            match event.type:
                case pg.QUIT:
                    await self.STATE_QUIT()
                case pg.VIDEORESIZE:
                    await self.window_resize(event.size)

    async def main(self):
        while True:
            try:
                func = self.NEXT.get_nowait()
                await func()
            except queue.Empty:
                self.NEXT.put(self.STATE_blank)

    # States
    async def STATE_blank(self):
        self.SCREEN.fill((0,0,0))
        await self.BASIC_EVENT_HANDLE()
        await self.tick()

    def main_menu_draw(self):
        BG_COLOUR = (38, 102, 152)
        AC_COLOUR = (243, 178, 67)
        TXT_COLOUR = (255, 255, 255)

        ## left side
        left_domain = (0, self.SCREEN.get_width() / 2)
        # left top: logo
        left_top_range = (0, self.SCREEN.get_height() /2)
        left_top_surface = pg.Surface((left_domain[1]-left_domain[0], left_top_range[1]-left_top_range[0]))
        left_top_surface.fill(BG_COLOUR)
        ### content
        left_top_font = pg.font.SysFont(name=pg.font.get_default_font(), size=int(2 * ((left_top_surface.get_height()) / 3)))
        left_top_text = left_top_font.render('MWBI', True, TXT_COLOUR)
        left_top_surface.blit(left_top_text, ((left_top_surface.get_width() - left_top_text.get_width()) / 2, (left_top_surface.get_height() - left_top_text.get_height()) / 2))

        self.SCREEN.blit(left_top_surface, (left_domain[0], left_top_range[0]))

        # left bottom: "Press any button to start"
        left_bottom_range = (self.SCREEN.get_height() / 2, self.SCREEN.get_height())
        left_bottom_surface = pg.Surface((left_domain[1]-left_domain[0], left_bottom_range[1]-left_bottom_range[0]))
        left_bottom_surface.fill(BG_COLOUR)
        self.SCREEN.blit(left_bottom_surface, (left_domain[0], left_bottom_range[0]))

        ## right side
        right_domain = (self.SCREEN.get_width() / 2, self.SCREEN.get_width())
        # section 1: start button
        right_sect1_range = (0, self.SCREEN.get_height() / 4)
        right_sect1_surface = pg.Surface((right_domain[1]-right_domain[0], right_sect1_range[1]-right_sect1_range[0]))
        right_sect1_surface.fill(BG_COLOUR)
        ### content
        # button sizes will be 2/3 of the container wide and long.
        right_sect1_button = pg.Surface((2 * ((right_domain[1] - right_domain[0] )/ 3), 2 * ((right_sect1_range[1] - right_sect1_range[0]) / 3)))
        right_sect1_button.fill(AC_COLOUR)
        right_sect1_button_font = pg.font.SysFont(name=pg.font.get_default_font(), size=int(2 * ((right_sect1_button.get_height()) / 3)))
        right_sect1_button_text = right_sect1_button_font.render('Play', True, TXT_COLOUR)
        right_sect1_button.blit(right_sect1_button_text, ((right_sect1_button.get_width() - right_sect1_button_text.get_width()) / 2, (right_sect1_button.get_height() - right_sect1_button_text.get_height()) / 2))
        right_sect1_button_vector = pg.Vector2(((right_domain[1] - right_domain[0]) / 3) / 2, ((right_sect1_range[1] - right_sect1_range[0]) / 3) / 2)
        right_sect1_button_endvector = pg.Vector2(right_sect1_button.get_width(), right_sect1_button.get_height())
        right_sect1_surface.blit(right_sect1_button, right_sect1_button_vector)
        right_sect1_surface_vector = pg.Vector2(right_domain[0], right_sect1_range[0])
        self.SCREEN.blit(right_sect1_surface, right_sect1_surface_vector)

        # section 2: options
        right_sect2_range = (self.SCREEN.get_height() / 4, 2 * (self.SCREEN.get_height() / 4))
        right_sect2_surface = pg.Surface((right_domain[1]-right_domain[0], right_sect2_range[1]-right_sect2_range[0]))
        right_sect2_surface.fill(BG_COLOUR)
        ### content
        right_sect2_button = pg.Surface((2 * ((right_domain[1] - right_domain[0] )/ 3), 2 * ((right_sect2_range[1] - right_sect2_range[0]) / 3)))
        right_sect2_button.fill(AC_COLOUR)
        right_sect2_button_font = pg.font.SysFont(name=pg.font.get_default_font(), size=int(2 * ((right_sect2_button.get_height()) / 3)))
        right_sect2_button_text = right_sect2_button_font.render('Options', True, TXT_COLOUR)
        right_sect2_button.blit(right_sect2_button_text, ((right_sect2_button.get_width() - right_sect2_button_text.get_width()) / 2, (right_sect2_button.get_height() - right_sect2_button_text.get_height()) / 2))
        right_sect2_button_vector = pg.Vector2(((right_domain[1] - right_domain[0]) / 3) / 2, ((right_sect2_range[1] - right_sect2_range[0]) / 3) / 2)
        right_sect2_button_endvector = pg.Vector2(right_sect2_button.get_width(), right_sect2_button.get_height())
        right_sect2_surface.blit(right_sect2_button, right_sect2_button_vector)
        right_sect2_surface_vector = pg.Vector2(right_domain[0], right_sect2_range[0])
        self.SCREEN.blit(right_sect2_surface, right_sect2_surface_vector)

        # section 3: account
        right_sect3_range = (2 * (self.SCREEN.get_height() / 4), 3 * (self.SCREEN.get_height() / 4))
        right_sect3_surface = pg.Surface((right_domain[1]-right_domain[0], right_sect3_range[1]-right_sect3_range[0]))
        right_sect3_surface.fill(BG_COLOUR)
        ### content
        right_sect3_button = pg.Surface((2 * ((right_domain[1] - right_domain[0] )/ 3), 2 * ((right_sect3_range[1] - right_sect3_range[0]) / 3)))
        right_sect3_button.fill(AC_COLOUR)
        right_sect3_button_font = pg.font.SysFont(name=pg.font.get_default_font(), size=int(2 * ((right_sect3_button.get_height()) / 3)))
        right_sect3_button_text = right_sect3_button_font.render('Account', True, TXT_COLOUR)
        right_sect3_button.blit(right_sect3_button_text, ((right_sect3_button.get_width() - right_sect3_button_text.get_width()) / 2, (right_sect3_button.get_height() - right_sect3_button_text.get_height()) / 2))
        right_sect3_button_vector = pg.Vector2(((right_domain[1] - right_domain[0]) / 3) / 2, ((right_sect3_range[1] - right_sect3_range[0]) / 3) / 2)
        right_sect3_button_endvector = pg.Vector2(right_sect3_button.get_width(), right_sect3_button.get_height())
        right_sect3_surface.blit(right_sect3_button, right_sect3_button_vector)
        right_sect3_surface_vector = pg.Vector2(right_domain[0], right_sect3_range[0])
        self.SCREEN.blit(right_sect3_surface, right_sect3_surface_vector)

        # section 4: about
        right_sect4_range = (3 * (self.SCREEN.get_height() / 4), self.SCREEN.get_height())
        right_sect4_surface = pg.Surface((right_domain[1]-right_domain[0], right_sect4_range[1]-right_sect4_range[0]))
        right_sect4_surface.fill(BG_COLOUR)
        ### content
        right_sect4_button = pg.Surface((2 * ((right_domain[1] - right_domain[0] )/ 3), 2 * ((right_sect1_range[1] - right_sect1_range[0]) / 3)))
        right_sect4_button.fill(AC_COLOUR)
        right_sect4_button_font = pg.font.SysFont(name=pg.font.get_default_font(), size=int(2 * ((right_sect4_button.get_height()) / 3)))
        right_sect4_button_text = right_sect4_button_font.render('About', True, TXT_COLOUR)
        right_sect4_button.blit(right_sect4_button_text, ((right_sect4_button.get_width() - right_sect4_button_text.get_width()) / 2, (right_sect4_button.get_height() - right_sect4_button_text.get_height()) / 2))
        right_sect4_button_vector = pg.Vector2(((right_domain[1] - right_domain[0]) / 3) / 2, ((right_sect4_range[1] - right_sect4_range[0]) / 3) / 2)
        right_sect4_button_endvector = pg.Vector2(right_sect4_button.get_width(), right_sect4_button.get_height())
        right_sect4_surface.blit(right_sect4_button, right_sect4_button_vector)
        right_sect4_surface_vector = pg.Vector2(right_domain[0], right_sect4_range[0])
        self.SCREEN.blit(right_sect4_surface, right_sect4_surface_vector)

        return (right_sect1_button_vector + right_sect1_surface_vector, right_sect1_button_vector + right_sect1_surface_vector + right_sect1_button_endvector), (right_sect2_button_vector + right_sect2_surface_vector, right_sect2_button_vector + right_sect2_surface_vector + right_sect2_button_endvector), (right_sect3_button_vector + right_sect3_surface_vector, right_sect3_button_vector + right_sect3_surface_vector + right_sect3_button_endvector), (right_sect4_button_vector + right_sect4_surface_vector, right_sect4_button_vector + right_sect4_surface_vector + right_sect4_button_endvector)
    async def STATE_intro(self):
        alpha = 255
        while True:
            ## hidden background
            self.SCREEN.fill((0,0,0))
            self.main_menu_draw()

            ## cover surface
            s = pg.Surface((self.SCREEN.get_width(), self.SCREEN.get_height()))
            s.fill((0,0,0))
            s.set_alpha(alpha)
            self.SCREEN.blit(s, (0,0))
            if alpha <= 0:
                break
            alpha -= 5
            await self.BASIC_EVENT_HANDLE()
            await self.tick()
        await self.tick()
        self.SCREEN.fill((0,0,0))
        self.NEXT.put(self.STATE_mainmenu)

    async def STATE_mainmenu(self):
       while True:
            BUTTON_start, BUTTON_options, BUTTON_account, BUTTON_about = self.main_menu_draw()

            # event handling
            for event in pg.event.get():
                match event.type:
                    case pg.QUIT:
                        await self.STATE_QUIT()
                    case pg.VIDEORESIZE:
                        await self.window_resize(event.size)
                    case pg.MOUSEBUTTONDOWN:
                        rpos = pg.Vector2(event.pos)
                        pos = rpos - self.PADDING_VECTOR
                        if (BUTTON_start[0].x < event.pos[0] < BUTTON_start[1].x) and (BUTTON_start[0].y < pos[1] < BUTTON_start[1].y):
                            self.GAME.progress_story()
                            self.NEXT.put(self.STATE_ingame)
                            return
                        elif (BUTTON_options[0].x < pos[0] < BUTTON_options[1].x) and (BUTTON_options[0].y < pos[1] < BUTTON_options[1].y):
                            self.NEXT.put(self.STATE_options_menu)
                            return
                        elif (BUTTON_account[0].x < pos[0] < BUTTON_account[1].x) and (BUTTON_account[0].y < pos[1] < BUTTON_account[1].y):
                            self.NEXT.put(self.STATE_account_menu)
                            return
                        elif (BUTTON_about[0].x < pos[0] < BUTTON_about[1].x) and (BUTTON_about[0].y < pos[1] < BUTTON_about[1].y):
                            self.NEXT.put(self.STATE_about_menu)
                            return

            await self.tick()

    async def STATE_ingame(self):
        tilemap = Tilemap(pl.Path("maps/main.csv"), pg.image.load(self.ASSETS.get("tilemap_main").open("r")))
        while True:
            self.SCREEN.fill((0, 0, 0))
            tilemap.draw(self.SCREEN)

            await self.BASIC_EVENT_HANDLE()
            await self.tick()

        self.NEXT.put(self.STATE_blank)

    async def STATE_options_menu(self):
        self.NEXT.put(self.STATE_blank)
    
    async def STATE_account_menu(self):
        self.NEXT.put(self.STATE_blank)

    async def STATE_about_menu(self):
        self.NEXT.put(self.STATE_blank)

    async def STATE_QUIT(self):
        pg.quit()
        sys.exit()


if __name__ == "__main__":
    app = App()
    asyncio.run(app.main())
    pg.quit()