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
    
    def reset(self):
        for goal in self.goals:
            goal["complete"] = False

    def add_goal(self, slug: str, friendly: str, stages: str, events: list | None = None, rewards: list | None = None):
        self.goals.append({
            "slug": slug,
            "friendly": friendly,
            "stages": stages,
            "events": events or [],
            "rewards": rewards or [],
            "complete": False
        })
    
    def add_goal_events(self, goalslug: str, type: str, **kwargs):
        for goal in self.goals:
            if goal["slug"] == goalslug:
                goal["events"].append({"type": type, **kwargs})
                break

    def add_goal_rewards(self, goalslug: str, type: str, **kwargs):
        for goal in self.goals:
            if goal["slug"] == goalslug:
                goal["rewards"].append({"type": type, **kwargs})
                break

    def complete_goal(self, goalslug: str):
        for goal in self.goals:
            if goal["slug"] == goalslug:
                goal["complete"] = True
                break

    def _event_matches_goal_event(self, goal_event: dict, event_type: str, payload: dict):
        if goal_event.get("type") != event_type:
            return False

        for key, value in goal_event.items():
            if key == "type":
                continue
            if payload.get(key) != value:
                return False

        return True

    def handle_event(self, event_type: str, **payload):
        completed_goals = []

        for goal in self.goals:
            if goal.get("complete"):
                continue

            for goal_event in goal.get("events", []):
                if self._event_matches_goal_event(goal_event, event_type, payload):
                    goal["complete"] = True
                    completed_goals.append(goal["slug"])
                    break

        return completed_goals

    def is_complete(self):
        return all(goal.get("complete", False) for goal in self.goals)


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
        self._progress = {}
    
    def add_entity_interaction(self, entityid: str, name: str, icon_key: str, interactionResponseCycle: list, repeatCycle: bool, exhaustedInteractionResponse: str):
        self._data[entityid] = {"name": name, "icon": icon_key, "interactionResponseCycle": interactionResponseCycle, "repeatCycle": repeatCycle, "exhaustedInteractionResponse": exhaustedInteractionResponse}
        self._progress.setdefault(entityid, 0)
    
    def get_entity_interaction(self, entityid: str):
        if entityid is None:
            return None

        interaction = self._data.get(entityid)
        if interaction is None:
            return None

        response_cycle = interaction.get("interactionResponseCycle", [])
        response_index = self._progress.get(entityid, 0)

        if response_cycle:
            if response_index < len(response_cycle):
                response_text = response_cycle[response_index]
                if interaction.get("repeatCycle", False):
                    self._progress[entityid] = (response_index + 1) % len(response_cycle)
                else:
                    self._progress[entityid] = min(response_index + 1, len(response_cycle))
            else:
                response_text = interaction.get("exhaustedInteractionResponse", "")
        else:
            response_text = interaction.get("exhaustedInteractionResponse", "")

        return {**interaction, "response": response_text}
    


MAPS = {
    "level_1": "level1_tilemap_tmj",
    "level_2": "level2_tilemap_tmj",
    "level_3": "level3_tilemap_tmj",
    "level_4": "level4_tilemap_tmj",
    "level_5": "level5_tilemap_tmj",
}


def _build_stage(stage: int, slug: str, title: str, description: str, tilemap_key: str, entity_name: str, objective_slug: str):
    interaction_map = InteractionMap()
    interaction_map.add_entity_interaction(
        "example",
        entity_name,
        "example_entity_icon",
        [
            f"{entity_name}: keep going.",
            f"{entity_name}: you are doing fine.",
            f"{entity_name}: almost there.",
        ],
        False,
        f"{entity_name}: come back after you finish this stage."
    )

    objective = Objective(title, description)
    objective.add_goal(objective_slug, title, "1/1")
    objective.add_goal_events(objective_slug, "interaction", entityId="example")
    objective.add_goal_rewards(objective_slug, "storyProgression")

    return {
        "stage": stage,
        "slug": slug,
        "interactionMap": interaction_map,
        "tilemap": MAPS[tilemap_key],
        "spawn": None,
        "objective": objective,
    }


STORY = [
    _build_stage(
        0,
        "school-reception",
        "Meet Sgt Better Pritton",
        "Learn the controls and speak to five entities to clear the reception.",
        "level_1",
        "Sgt Better Pritton",
        "learn_controls",
    ),
    _build_stage(
        1,
        "maths-classroom",
        "Meet Fyumi Pernando",
        "Answer five multiple-choice maths questions by choosing the correct response.",
        "level_2",
        "Fyumi Pernando",
        "maths_quiz",
    ),
    _build_stage(
        2,
        "cluttered-classroom",
        "Meet Trikkie Nimboli",
        "Interact with the room in the required pattern to clear the cluttered classroom.",
        "level_3",
        "Trikkie Nimboli",
        "classroom_cleanup",
    ),
    _build_stage(
        3,
        "teachers-office",
        "Meet Ram Seid",
        "Complete the school rules quiz and earn a passing decision.",
        "level_4",
        "Ram Seid",
        "school_rules_quiz",
    ),
    _build_stage(
        4,
        "principals-office",
        "Meet Principal Fincoln Lorbes",
        "Present your result to the principal and finish the final review.",
        "level_5",
        "Principal Fincoln Lorbes",
        "final_review",
    ),
]