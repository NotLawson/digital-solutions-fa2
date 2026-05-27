## Digital Soltions FA2
import os, sys, asyncio
import pygame as pg
import pathlib as pl
import json
import queue
import csv
import pytiled_parser as tiled
import math
from storage import Storage, AssetManager
#from auth import Auth

class Game:
    MAP = None
    PLAYER = None 
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
    def __init__(self, tileset: tiled.Tileset, tilesheet: pg.Surface, id: int):
        self.surface = pg.Surface((32, 32))
        if id != 0:
            self.surface.blit(tileset, -1 * pg.Vector2(32 * int(id), 0))

class Player:
    pos = (None, None)
    frame_count: int = 0
    animation_count: int = 0
    speed: int = 8
    current_movement_vector: pg.Vector2 = pg.Vector2(0,0)


    # animations: 6 frames per second
    # frames:
    # 0-11 (12 frames, 2 seconds) idle
    # 12-23 (12 frames, 2 seconds) moving

    def __init__(self, animation_sheet: pg.Surface):
        self.sheet = animation_sheet
        self.cache = {}
    def reset(self):
        self.frame_count = self.animation_count = 0

    def tick(self):
        self.frame_count += 1
        if self.frame_count % 10 == 0:
            self.animation_count += 1
        elif self.frame_count > 60:
            self.frame_count = 0
            self.animation_count = 0

    def render(self, screen_width):
        if self.current_movement_vector != pg.Vector2(0, 0): frame_id = self.animation_count + 12
        else: frame_id = self.animation_count

        # attempt to get frame from cache
        if self.cache.get(frame_id, False):
            return self.cache.get(frame_id)
        
        s = pg.Surface((32, 32))
        s.blit(self.sheet, -1 * pg.Vector2(32 * int(frame_id), 0))
        self.tick()
        s = pg.transform.scale_by(s, (screen_width * 0.05) / 32)
        self.cache.update({frame_id: s})
        return s
        
def TileSurfaceFromTileSet(tileset: tiled.Tileset, id: int):
    tilesheet = pg.image.load(tileset.image).convert()
    tile = pg.Surface((tileset.tile_width, tileset.tile_width))
    if id != -1:
        tile.blit(tilesheet, -1 * pg.Vector2(tileset.tile_width * (int(id) - 1), 0))
    return tile


def render_tilemap(tilemap):
    c = pg.Vector2((32, 0))
    r = pg.Vector2((0, 32))
    current_r = pg.Vector2((0, 0))
    map_surface = pg.Surface(32 * pg.Vector2(tilemap.map_size))

    for row in tilemap.layers[0].data:
        current_c = pg.Vector2((0, 0))
        for col in row:
            tile = TileSurfaceFromTileSet(tilemap.tilesets[1], col)
            map_surface.blit(tile, current_r + current_c)
            current_c += c
        current_r += r


    return map_surface

class App:
    FPS: int = 60
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
        tilemap = tiled.parse_map(self.ASSETS.get("main_tilemap_tmj"))
        player = Player(pg.image.load(self.ASSETS.get("player_spritesheet_image").open("r")).convert())
        map_surface = pg.transform.scale_by(render_tilemap(tilemap), (self.SCREEN.get_width() * 0.05) / 32)
        while True:
            self.SCREEN.fill((0, 0, 0))
            player_surface = player.render(self.SCREEN.get_width())

            if player.pos == (None, None):
                #place player at spawn
                for object in tilemap.layers[1].tiled_objects:
                    if object.class_ == "spawn":
                        # spawn point
                        player.pos = pg.Vector2(object.coordinates)
                        break

            #t.blit(player_surface, player.pos - pg.Vector2(32/2, 32/2))
            self.SCREEN.blit(map_surface, pg.Vector2(self.SCREEN.get_width() / 2, self.SCREEN.get_height() / 2) - player.pos * ((self.SCREEN.get_width() * 0.05) / 32))
            self.SCREEN.blit(player_surface, pg.Vector2(self.SCREEN.get_width() / 2, self.SCREEN.get_height() / 2) - pg.Vector2(player_surface.get_width() / 2, player_surface.get_height() / 2))


            # events
            for event in pg.event.get():
                match event.type:
                    case pg.QUIT:
                        await self.STATE_QUIT()
                    case pg.VIDEORESIZE:
                        await self.window_resize(event.size)
                        # rescale the map
                        map_surface = pg.transform.scale_by(render_tilemap(tilemap), (self.SCREEN.get_width() * 0.05) / 32)
                        player.cache = {}
                    case pg.KEYDOWN:
                        # keydown
                        match event.key:
                            case pg.K_w | pg.K_UP:
                                player.current_movement_vector += pg.Vector2(0, -player.speed)
                            case pg.K_s | pg.K_DOWN:
                                player.current_movement_vector += pg.Vector2(0, player.speed)
                            case pg.K_a | pg.K_LEFT:
                                player.current_movement_vector += pg.Vector2(-player.speed, 0)
                            case pg.K_d | pg.K_RIGHT:
                                player.current_movement_vector += pg.Vector2(player.speed, 0)
                    case pg.KEYUP:
                        # keyup
                        match event.key:
                            case pg.K_w | pg.K_UP:
                                player.current_movement_vector -= pg.Vector2(0, -player.speed)
                            case pg.K_s | pg.K_DOWN:
                                player.current_movement_vector -= pg.Vector2(0, player.speed)
                            case pg.K_a | pg.K_LEFT:
                                player.current_movement_vector -= pg.Vector2(-player.speed, 0)
                            case pg.K_d | pg.K_RIGHT:
                                player.current_movement_vector -= pg.Vector2(player.speed, 0)
            player.pos += player.current_movement_vector
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