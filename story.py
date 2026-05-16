## Story
import csv
import pathlib

class Scene:
    pass

class Objective:
    title: str = "Objective Title"
    description: str = "Objective Description"
    goals: list = [
        {
            "slug":"slug",
            "friendly": "Friendly Name",
            "stages": "1/1",
            "events": [
                {
                    "type": "interaction",
                    "entityId": "entityId"
                },
                {
                    "type": "tile",
                    "pos": (14, 23)
                }
            ],
            "rewards": [
                {
                    "type": "item",
                    "itemId": "itemId",
                    "quantity": 10
                },
                {
                    "type": "decision",
                    "value": 0
                },
                {
                    "type": "storyProgression"
                }
            ]
        }
    ]
    
    def __init__(self, title: str, description: str):
        self.title, self.description, self.goals = title, description, []
    
    def add_goal(self, slug: str, friendly: str, stages: str):
        self.goals.append({
            "slug": slug,
            "friendly": friendly,
            "stages": stages,
            "events": [],
            "rewards": []
        })
    
    def add_goal_events(self, goalslug: str, type: str, **kwargs):
        for goal in self.goals:
            if goal["slug"] == goalslug:
                goal["events"].update({"type":type})


class InteractionMap:
    _data: dict = {
        "interactionEntityId":{
            "name": "Example Interaction Entity",
            "icon": "example-interaction-entity-icon",
            "interactionResponseCycle":["Interaction Response 1", "Interaction Response 2", "Interaction Response 3"],
            "repeatCycle": False,
            "exhaustedInteractionResponse": "Exhausted Interaction Response"
        }
    }

    def __init__(self):
        self._data = {}
    
    def add_entity_interaction(self, entityid: str, name: str, icon_key: str, interactionResponseCycle: list, repeatCycle: bool, exhaustedInteractionResponse: str):
        self._data[entityid] = {"name": name, "icon": icon_key, "interactionReponseCycle": interactionResponseCycle, "repeatCycle": repeatCycle, "exhaustedInteractionResponse": exhaustedInteractionResponse}

class Element:
    slug: SystemError
    scene: Scene
    objective: Objective
    interactionMap: InteractionMap

    def __init__(self, slug: str, scene: Scene, objective: Objective, interactionmap):
        self.slug = slug
        self.scene = scene
        self.objective = objective
        self.interactionMap = interactionmap

class Tilemap:
    properties = {
        0: {
            "slug": "null",
            "desc": "Unused tile. Isn't generated, leaving the background invisible"
        },
        1: {
            "slug": "walkable",
            "desc": "Standard tile. Player is able to move to it."
        },
        2: {
            "slug": "solid",
            "desc": "Solid tile. Player is unable to move to it."
        },
        3: {
            "slug": "door",
            "desc": "Toggleable tile. Is either solid or walkable, dependant on it's 'open' argument"
        },
        4: {
            "slug": "entity",
            "desc": "Entity Spawn Location. Uses argument 'entityId'."
        },
        5: {
            "slug": "trigger",
            "desc": "Triggers an event when moved to. Uses argument 'event'"
        }
    }

    def __init__(self, map):
        self.map = map

class School(Tilemap):
    tiles = {
        0: {
            "location": (0, 0),
            "properties": [(1)]
        },
        1: {
            "location": (0, 1),
            "properties": [(1)]
        },
        2: {
            "location": (0, 2),
            "properties": [(2)]
        }
    }

    def __init__(self):
        with pathlib.Path("./maps/main.csv").open("r") as f:
            super().__init__(csv.reader(f.readlines()))
            
STORY = []
# 0: Initalisation