## Digital Soltions FA2
# Main entry and game loop
import sys, asyncio
import pygame as pg
import pathlib as pl
import json
import queue
import pytiled_parser as tiled
# Storage and story imports
from storage import Storage, AssetManager
from story import STORY
#from auth import Auth

class Player:
    # Player character handling
    pos = (None, None)
    frame_count: int = 0
    animation_count: int = 0
    speed: int = 4
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

class Entity:
    # Generic entity handling
    animation_count: int = 0
    frame_count: int = 0
    def __init__(self, id: str, animation_sheet: pg.Surface):
        self.id = id
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
        # attempt to get frame from cache
        if self.cache.get(self.animation_count, False):
            return self.cache.get(self.animation_count)
        
        s = pg.Surface((32, 32))
        s.blit(self.sheet, -1 * pg.Vector2(32 * int(self.animation_count), 0))
        self.tick()
        s = pg.transform.scale_by(s, (screen_width * 0.05) / 32)
        self.cache.update({self.animation_count: s})
        return s

class Game:
    # Game state and story management
    MAP: tiled.TiledMap | None = None
    PLAYER: Player | None = None
    MAP_SOLID_RECTS: list[pg.Rect] = []
    MAP_ENTITIES: list = []
    ENTITY_REGISTRY: dict[str, Entity] = {}
    INTERACTED_ENTITY_ID: str | None = None
    INTERACTED_ENTITY_NAME: str | None = None
    INTERACTED_ENTITY_ICON: str | None = None
    INTERACTED_ENTITY_RESPONSE: str | None = None
    OBJECTIVE_COMPLETE: bool = False
    ASSETS: AssetManager = AssetManager(json.load(pl.Path("assets/inventory.json").open("r")))
    OBJECTIVE = {}
    STORY: list = STORY
    STAGE: int = 0
    DECISIONS = []
    PENDING_REWARDS: list[dict] = []
    ACTIVE_REWARD: dict | None = None
    PENDING_STORY_ADVANCE: bool = False
    STORY_COMPLETE: bool = False

    # Story Element: objectives, cutscenes, etc.
    # Stages: tilemaps, minigames

    def __init__(self):
        pass

    def reset_story(self):
        self.MAP = None
        self.MAP_SOLID_RECTS = []
        self.MAP_ENTITIES = []
        self.ENTITY_REGISTRY = {}
        self.INTERACTED_ENTITY_ID = None
        self.INTERACTED_ENTITY_NAME = None
        self.INTERACTED_ENTITY_ICON = None
        self.INTERACTED_ENTITY_RESPONSE = None
        self.OBJECTIVE_COMPLETE = False
        self.PENDING_REWARDS = []
        self.ACTIVE_REWARD = None
        self.PENDING_STORY_ADVANCE = False
        self.STORY_COMPLETE = False
        self.STAGE = 0

    def can_progress_story(self):
        return self.STAGE + 1 < len(self.STORY)

    def _stage_requests_story_progression(self, stage: dict):
        objective = stage.get("objective")
        if objective is None:
            return False

        for goal in objective.goals:
            for reward in goal.get("rewards", []):
                if reward.get("type") == "storyProgression":
                    return True

        return False

    def progress_story(self):
        # Advance story stage
        if not self.can_progress_story():
            self.PENDING_STORY_ADVANCE = False
            self.STORY_COMPLETE = True
            return False
        
        self.STAGE += 1
        current_stage = self.get_current_story_stage()
        objective = current_stage.get("objective")
        if objective is not None:
            objective.reset()
        print(current_stage)
        self.load_map(current_stage["tilemap"])
        self.PENDING_REWARDS = []
        self.ACTIVE_REWARD = None
        self.PENDING_STORY_ADVANCE = False
        self.STORY_COMPLETE = False
        return True
    
    def get_current_story_stage(self):
        return self.STORY[self.STAGE]

    def get_current_objective(self):
        if self.STAGE < 0 or self.STAGE >= len(self.STORY):
            return None
        return self.get_current_story_stage().get("objective")

    def queue_rewards(self, rewards: list[dict]):
        self.PENDING_REWARDS.extend(rewards)

    def has_pending_rewards(self):
        return self.ACTIVE_REWARD is not None or len(self.PENDING_REWARDS) > 0

    def start_next_reward(self):
        while self.PENDING_REWARDS:
            reward = self.PENDING_REWARDS.pop(0)
            reward_type = reward.get("type")

            if reward_type == "scene":
                self.ACTIVE_REWARD = reward
                self.INTERACTED_ENTITY_ID = "scene_reward"
                self.INTERACTED_ENTITY_NAME = reward.get("name")
                self.INTERACTED_ENTITY_ICON = reward.get("icon")
                self.INTERACTED_ENTITY_RESPONSE = reward.get("content")
                return reward

            if reward_type == "storyProgression":
                self.ACTIVE_REWARD = None
                return reward

        self.ACTIVE_REWARD = None
        return None

    def finish_active_reward(self):
        self.ACTIVE_REWARD = None

    def load_map(self, map: str):
        # Load tilemap and instantiate entities
        self.MAP = tiled.parse_map(self.ASSETS.get(map))
        self.MAP_SOLID_RECTS = []
        self.MAP_ENTITIES = []
        self.ENTITY_REGISTRY = {}
        self.INTERACTED_ENTITY_ID = None
        self.INTERACTED_ENTITY_NAME = None
        self.INTERACTED_ENTITY_ICON = None
        self.INTERACTED_ENTITY_RESPONSE = None
        self.OBJECTIVE_COMPLETE = False
        self.PENDING_REWARDS = []
        self.ACTIVE_REWARD = None
        self.PENDING_STORY_ADVANCE = False
        self.STORY_COMPLETE = False

        solid_gids = set()
        for firstgid, tileset in self.MAP.tilesets.items():
            for tile_id, tile in tileset.tiles.items():
                if tile.properties and tile.properties.get("collision"):
                    solid_gids.add(firstgid + tile_id)

        tile_size = self.MAP.tile_size.width
        for row_index, row in enumerate(self.MAP.layers[0].data):
            for col_index, tile_id in enumerate(row):
                if tile_id in solid_gids:
                    self.MAP_SOLID_RECTS.append(pg.Rect(col_index * tile_size, row_index * tile_size, tile_size, tile_size))

        # build the entity registry from object-layer definitions
        for object in self.MAP.layers[1].tiled_objects:
            if object.class_ != "entity":
                continue

            entity_id = object.properties.get("entityid") if object.properties else None
            spritesheet_path = object.properties.get("spritesheet") if object.properties else None
            if entity_id is None or spritesheet_path is None or entity_id in self.ENTITY_REGISTRY:
                continue

            spritesheet_file = pl.Path(__file__).resolve().parent / spritesheet_path
            self.ENTITY_REGISTRY[entity_id] = Entity(entity_id, pg.image.load(str(spritesheet_file)).convert())

        # place player at spawn and spawn entities from the registry
        for object in self.MAP.layers[1].tiled_objects:
            if object.class_ == "spawn":
                # spawn point
                self.PLAYER.pos = pg.Vector2(object.coordinates)
                continue
            if object.class_ == "entity":
                entity_id = object.properties.get("entityid") if object.properties else None
                if entity_id is None:
                    continue

                entity_template = self.ENTITY_REGISTRY.get(entity_id)
                if entity_template is None:
                    continue

                spawned_entity = Entity(entity_template.id, entity_template.sheet)
                spawned_entity.pos = pg.Vector2(object.coordinates)
                spawned_entity.collision_rect = pg.Rect(spawned_entity.pos.x, spawned_entity.pos.y, tile_size, tile_size)
                self.MAP_ENTITIES.append(spawned_entity)
                self.MAP_SOLID_RECTS.append(spawned_entity.collision_rect)

    def register_interaction(self, entity_id: str, interaction: dict | None = None):
        if interaction is None:
            interaction = self.get_current_story_stage()["interactionMap"].get_entity_interaction(entity_id)
        if interaction is None:
            return []

        current_objective = self.get_current_objective()
        current_goal = current_objective.get_current_goal() if current_objective is not None else None

        response = interaction.get("response")
        self.INTERACTED_ENTITY_ID = entity_id
        self.INTERACTED_ENTITY_NAME = interaction.get("name")
        self.INTERACTED_ENTITY_ICON = interaction.get("icon")
        self.INTERACTED_ENTITY_RESPONSE = response

        objective = current_objective
        completed_goals = []
        if objective is not None:
            completed_goals = objective.handle_event("interaction", entityId=entity_id, response=response)
            if current_goal is not None and current_goal.get("slug") in completed_goals:
                self.queue_rewards(current_goal.get("rewards", []))
            self.OBJECTIVE_COMPLETE = objective.is_complete()
            self.PENDING_STORY_ADVANCE = self.has_pending_rewards()

        return completed_goals

    def get_colliding_entity_id(self, player_position: pg.Vector2, player_size: int = 32):
        player_rect = pg.Rect(0, 0, player_size, player_size)
        player_rect.center = player_position

        for entity in self.MAP_ENTITIES:
            if not hasattr(entity, "collision_rect"):
                continue

            # Collision keeps the player outside the entity rect, so check a small
            # interaction envelope instead of requiring exact overlap.
            interaction_rect = player_rect.inflate(8, 8)
            if interaction_rect.colliderect(entity.collision_rect):
                return entity.id

        return None

    def wrap_text(self, text: str, font: pg.font.Font, max_width: int):
        words = text.split()
        if not words:
            return [""]

        lines = []
        current_line = words[0]

        for word in words[1:]:
            candidate_line = f"{current_line} {word}"
            if font.size(candidate_line)[0] <= max_width:
                current_line = candidate_line
            else:
                lines.append(current_line)
                current_line = word

        lines.append(current_line)
        return lines
        
def TileSurfaceFromTileSet(tileset: tiled.Tileset, id: int):
    # Convert a tileset entry into a surface
    tilesheet = pg.image.load(tileset.image).convert()
    tile = pg.Surface((tileset.tile_width, tileset.tile_width))
    if id != -1:
        tile.blit(tilesheet, -1 * pg.Vector2(tileset.tile_width * (int(id) - 1), 0))
    return tile


def render_tilemap(tilemap):
    # Render the full tilemap to a surface
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
    # Application and main event loop
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
        self.INTERACTION_EVENT = pg.event.custom_type()
        self.GAME.PLAYER = Player(pg.image.load(self.ASSETS.get("player_spritesheet_image").open("r")).convert())
        self.NEXT.put(self.STATE_intro)

    # Utils
    async def tick(self):
        # Frame tick: draw and wait for next frame
        self.DISPLAY.fill((0, 0, 0))
        self.DISPLAY.blit(self.SCREEN, self.PADDING_VECTOR)
        pg.display.update()
        await asyncio.sleep(1 / self.FPS)

    async def window_resize(self, size: tuple):
        # Handle window resizing and maintain aspect ratio
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

    def refresh_map_surface(self):
        # Refresh cached scaled map surface
        map_scale = (self.SCREEN.get_width() * 0.05) / 32
        self.map_surface = pg.transform.scale_by(render_tilemap(self.GAME.MAP), map_scale)
        return map_scale

    def draw_objective_box(self):
        # Draw the objective UI panel
        objective = self.GAME.get_current_objective()
        if objective is None:
            return

        box_width = int(self.SCREEN.get_width() * 0.30)
        box_x = self.SCREEN.get_width() - box_width - 24
        box_y = 24

        title_font = pg.font.SysFont(name=pg.font.get_default_font(), size=max(18, int(self.SCREEN.get_height() * 0.028)))
        body_font = pg.font.SysFont(name=pg.font.get_default_font(), size=max(14, int(self.SCREEN.get_height() * 0.022)))

        body_width = box_width - 32
        body_lines = self.GAME.wrap_text(objective.description, body_font, body_width)
        goal_lines = [
            f"{'[x]' if goal.get('complete') else '[ ]'} {goal.get('friendly', goal.get('slug', 'Goal'))}"
            for goal in objective.goals
        ]
        progress = objective.get_progress()

        box_height = 24 + title_font.get_height() + 10
        box_height += len(body_lines) * (body_font.get_height() + 4)
        box_height += 18 + body_font.get_height() + 14
        if goal_lines:
            box_height += 10 + body_font.get_height()
            box_height += len(goal_lines) * (body_font.get_height() + 4)
        box_height += 18
        box_height = max(box_height, int(self.SCREEN.get_height() * 0.16))

        box_surface = pg.Surface((box_width, box_height), pg.SRCALPHA)
        box_surface.fill((18, 24, 34, 220))
        pg.draw.rect(box_surface, (255, 255, 255), box_surface.get_rect(), 2, border_radius=10)

        title_surface = title_font.render(objective.title, True, (255, 255, 255))
        box_surface.blit(title_surface, (16, 14))

        body_top = 14 + title_surface.get_height() + 8
        for index, line in enumerate(body_lines[:3]):
            line_surface = body_font.render(line, True, (220, 220, 220))
            box_surface.blit(line_surface, (16, body_top + index * (line_surface.get_height() + 4)))

        bar_top = body_top + len(body_lines[:3]) * (body_font.get_height() + 4) + (8 if body_lines else 0)
        bar_label_surface = body_font.render(f"Progress: {int(progress * 100)}%", True, (255, 255, 255))
        box_surface.blit(bar_label_surface, (16, bar_top))

        bar_top += bar_label_surface.get_height() + 6
        bar_outer_rect = pg.Rect(16, bar_top, box_width - 32, 14)
        pg.draw.rect(box_surface, (70, 76, 88), bar_outer_rect, border_radius=7)
        bar_inner_width = max(0, int((box_width - 32 - 4) * progress))
        if bar_inner_width > 0:
            bar_inner_rect = pg.Rect(18, bar_top + 2, bar_inner_width, 10)
            pg.draw.rect(box_surface, (243, 178, 67), bar_inner_rect, border_radius=5)

        goal_header_top = bar_top + 24
        if goal_lines:
            goal_header_surface = body_font.render("Goals", True, (255, 255, 255))
            box_surface.blit(goal_header_surface, (16, goal_header_top))

            goal_top = goal_header_top + goal_header_surface.get_height() + 4
            for index, line in enumerate(goal_lines):
                line_surface = body_font.render(line, True, (220, 220, 220))
                box_surface.blit(line_surface, (16, goal_top + index * (line_surface.get_height() + 4)))

        self.SCREEN.blit(box_surface, (box_x, box_y))

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
                            # loading
                            self.SCREEN.fill((0,0,0))
                            await self.tick()
                            if self.GAME.progress_story():
                                self.NEXT.put(self.STATE_ingame)
                                self.refresh_map_surface()
                            else:
                                self.NEXT.put(self.STATE_story_complete)
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
        while True:
            map_scale = (self.SCREEN.get_width() * 0.05) / 32
            self.SCREEN.fill((0, 0, 0))
            player_surface = self.GAME.PLAYER.render(self.SCREEN.get_width())
            self.SCREEN.blit(self.map_surface, pg.Vector2(self.SCREEN.get_width() / 2, self.SCREEN.get_height() / 2) - self.GAME.PLAYER.pos * map_scale)

            for entity in self.GAME.MAP_ENTITIES:
                entity_surface = entity.render(self.SCREEN.get_width())
                entity_screen_pos = pg.Vector2(self.SCREEN.get_width() / 2, self.SCREEN.get_height() / 2) - self.GAME.PLAYER.pos * map_scale + entity.pos * map_scale
                self.SCREEN.blit(entity_surface, entity_screen_pos)

            self.SCREEN.blit(player_surface, pg.Vector2(self.SCREEN.get_width() / 2, self.SCREEN.get_height() / 2) - pg.Vector2(player_surface.get_width() / 2, player_surface.get_height() / 2))
            self.draw_objective_box()

            # events
            for event in pg.event.get():
                match event.type:
                    case pg.QUIT:
                        await self.STATE_QUIT()
                    case pg.VIDEORESIZE:
                        await self.window_resize(event.size)
                        # rescale the map
                        self.refresh_map_surface()
                        self.GAME.PLAYER.cache = {}
                        for entity in self.GAME.MAP_ENTITIES:
                            entity.cache = {}
                    case pg.KEYDOWN:
                        # keydown
                        match event.key:
                            case pg.K_w | pg.K_UP:
                                self.GAME.PLAYER.current_movement_vector += pg.Vector2(0, -self.GAME.PLAYER.speed)
                            case pg.K_s | pg.K_DOWN:
                                self.GAME.PLAYER.current_movement_vector += pg.Vector2(0, self.GAME.PLAYER.speed)
                            case pg.K_a | pg.K_LEFT:
                                self.GAME.PLAYER.current_movement_vector += pg.Vector2(-self.GAME.PLAYER.speed, 0)
                            case pg.K_d | pg.K_RIGHT:
                                self.GAME.PLAYER.current_movement_vector += pg.Vector2(self.GAME.PLAYER.speed, 0)
                            case pg.K_RETURN:
                                entity_id = self.GAME.get_colliding_entity_id(self.GAME.PLAYER.pos)
                                if entity_id is not None:
                                    interaction = self.GAME.get_current_story_stage()["interactionMap"].get_entity_interaction(entity_id)
                                    if interaction is not None:
                                        self.GAME.register_interaction(entity_id, interaction)
                                        pg.event.post(pg.event.Event(self.INTERACTION_EVENT, {"entity_id": entity_id, "response": interaction.get("response")}))
                                    self.NEXT.put(self.STATE_scene)
                                    self.GAME.PLAYER.current_movement_vector = pg.Vector2(0, 0)
                                    return
                            case pg.K_ESCAPE:
                                self.NEXT.put(self.STATE_scene)
                                return
                    case pg.KEYUP:
                        # keyup
                        match event.key:
                            case pg.K_w | pg.K_UP:
                                self.GAME.PLAYER.current_movement_vector -= pg.Vector2(0, -self.GAME.PLAYER.speed)
                            case pg.K_s | pg.K_DOWN:
                                self.GAME.PLAYER.current_movement_vector -= pg.Vector2(0, self.GAME.PLAYER.speed)
                            case pg.K_a | pg.K_LEFT:
                                self.GAME.PLAYER.current_movement_vector -= pg.Vector2(-self.GAME.PLAYER.speed, 0)
                            case pg.K_d | pg.K_RIGHT:
                                self.GAME.PLAYER.current_movement_vector -= pg.Vector2(self.GAME.PLAYER.speed, 0)


            # move the player
            if self.GAME.PLAYER.current_movement_vector != pg.Vector2(0, 0):
                player_rect = pg.Rect(0, 0, 32, 32)
                player_rect.center = self.GAME.PLAYER.pos

                # resolve X first so the player can slide along walls
                player_rect.x += round(self.GAME.PLAYER.current_movement_vector.x)
                for solid in self.GAME.MAP_SOLID_RECTS:
                    if player_rect.colliderect(solid):
                        if self.GAME.PLAYER.current_movement_vector.x > 0:
                            player_rect.right = solid.left
                        elif self.GAME.PLAYER.current_movement_vector.x < 0:
                            player_rect.left = solid.right

                # then resolve Y against the updated X position
                player_rect.y += round(self.GAME.PLAYER.current_movement_vector.y)
                for solid in self.GAME.MAP_SOLID_RECTS:
                    if player_rect.colliderect(solid):
                        if self.GAME.PLAYER.current_movement_vector.y > 0:
                            player_rect.bottom = solid.top
                        elif self.GAME.PLAYER.current_movement_vector.y < 0:
                            player_rect.top = solid.bottom

                self.GAME.PLAYER.pos = pg.Vector2(player_rect.center)


            self.GAME.PLAYER.tick()
            await self.tick()
    
    async def STATE_scene(self):
        dialogue_width = int((self.SCREEN.get_width() - (self.SCREEN.get_height() * 0.02)) - (0 + (self.SCREEN.get_height() * 0.02)))
        dialogue_height = int((self.SCREEN.get_height() - (self.SCREEN.get_height() * 0.02)) - (2 * (self.SCREEN.get_height() / 3) + (self.SCREEN.get_height() * 0.02)))
        dialogue_area = pg.Surface((dialogue_width, dialogue_height))
        dialogue_rect = dialogue_area.get_rect(topleft=pg.Vector2(0 + (self.SCREEN.get_height() * 0.02), (2 * (self.SCREEN.get_height() / 3) + (self.SCREEN.get_height() * 0.02))))

        title_font = pg.font.SysFont(name=pg.font.get_default_font(), size=max(12, int(dialogue_height * 0.16)))
        body_font = pg.font.SysFont(name=pg.font.get_default_font(), size=max(10, int(dialogue_height * 0.1)))
        current_icon_key = None
        icon_surface = None

        def sync_dialogue_from_reward(reward: dict):
            self.GAME.INTERACTED_ENTITY_ID = "scene_reward"
            self.GAME.INTERACTED_ENTITY_NAME = reward.get("name")
            self.GAME.INTERACTED_ENTITY_ICON = reward.get("icon")
            self.GAME.INTERACTED_ENTITY_RESPONSE = reward.get("content")

        while True:
            if self.GAME.INTERACTED_ENTITY_ICON != current_icon_key:
                current_icon_key = self.GAME.INTERACTED_ENTITY_ICON
                icon_surface = None
                if current_icon_key is not None:
                    icon_surface = pg.image.load(self.ASSETS.get(current_icon_key)).convert()

            dialogue_area.fill((24, 24, 28))
            pg.draw.rect(dialogue_area, (255, 255, 255), dialogue_area.get_rect(), 3)

            if self.GAME.INTERACTED_ENTITY_ID is not None:
                padding = max(8, int(dialogue_height * 0.08))
                icon_size = max(32, min(int(dialogue_height * 0.7), dialogue_height - (2 * padding)))
                icon_box = pg.Rect(padding, padding, icon_size, icon_size)
                if icon_surface is not None:
                    scaled_icon = pg.transform.smoothscale(icon_surface, (icon_box.width, icon_box.height))
                    dialogue_area.blit(scaled_icon, icon_box.topleft)
                else:
                    pg.draw.rect(dialogue_area, (80, 80, 90), icon_box)

                title_text = self.GAME.INTERACTED_ENTITY_NAME or ""
                body_text = self.GAME.INTERACTED_ENTITY_RESPONSE or ""

                text_x = icon_box.right + padding
                text_width = max(1, dialogue_width - text_x - padding)
                title_surface = title_font.render(title_text, True, (255, 255, 255))
                dialogue_area.blit(title_surface, (text_x, padding))

                body_lines = self.GAME.wrap_text(body_text, body_font, text_width)
                body_y = padding + title_surface.get_height() + int(padding * 0.5)
                for line in body_lines:
                    line_surface = body_font.render(line, True, (220, 220, 220))
                    dialogue_area.blit(line_surface, (text_x, body_y))
                    body_y += line_surface.get_height() + 4

            self.SCREEN.blit(dialogue_area, dialogue_rect.topleft)
            for event in pg.event.get():
                match event.type:
                    case pg.QUIT:
                        await self.STATE_QUIT()
                    case pg.VIDEORESIZE:
                        await self.window_resize(event.size)
                    case pg.KEYDOWN:
                        match event.key:
                            case pg.K_RETURN:
                                if self.GAME.ACTIVE_REWARD is not None:
                                    self.GAME.finish_active_reward()

                                next_reward = self.GAME.start_next_reward()
                                if next_reward is not None:
                                    if next_reward.get("type") == "scene":
                                        sync_dialogue_from_reward(next_reward)
                                        continue

                                    if next_reward.get("type") == "storyProgression":
                                        if self.GAME.progress_story():
                                            self.refresh_map_surface()
                                            self.NEXT.put(self.STATE_ingame)
                                        else:
                                            self.NEXT.put(self.STATE_story_complete)
                                        return

                                self.NEXT.put(self.STATE_ingame)
                                return
            await self.tick()

    async def STATE_story_complete(self):
        title_font = pg.font.SysFont(name=pg.font.get_default_font(), size=max(24, int(self.SCREEN.get_height() * 0.08)))
        body_font = pg.font.SysFont(name=pg.font.get_default_font(), size=max(16, int(self.SCREEN.get_height() * 0.04)))

        while True:
            self.SCREEN.fill((10, 12, 18))

            title_text = title_font.render("Story complete", True, (255, 255, 255))
            body_text = body_font.render("Press Enter to return to the main menu.", True, (220, 220, 220))

            self.SCREEN.blit(title_text, ((self.SCREEN.get_width() - title_text.get_width()) / 2, self.SCREEN.get_height() / 3))
            self.SCREEN.blit(body_text, ((self.SCREEN.get_width() - body_text.get_width()) / 2, (self.SCREEN.get_height() / 3) + title_text.get_height() + 24))

            for event in pg.event.get():
                match event.type:
                    case pg.QUIT:
                        await self.STATE_QUIT()
                    case pg.VIDEORESIZE:
                        await self.window_resize(event.size)
                    case pg.KEYDOWN:
                        match event.key:
                            case pg.K_RETURN:
                                self.GAME.reset_story()
                                self.NEXT.put(self.STATE_mainmenu)
                                return

            await self.tick()


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