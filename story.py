class Scene:
    # Scene placeholder for narrative scenes
    pass

class Objective:
    # Tracks objectives, goals, and progress
    title: str = "Objective Title"
    description: str = "Objective Description"
    goals: list = [
        {
            "slug":"slug",
            "friendly": "Friendly Name",
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
                },
                {
                    "type": "scene",
                    "icon":"icon_key",
                    "name":"scene name",
                    "content":"content"

                }
            ]
        }
    ]
    
    def __init__(self, title: str, description: str):
        self.title, self.description, self.goals = title, description, []
    
    def reset(self):
        # Reset goal completion and event states
        for goal in self.goals:
            goal["complete"] = False
            goal["event_states"] = [False for _ in goal.get("events", [])]

    def add_goal(self, slug: str, friendly: str, events: list | None = None, rewards: list | None = None):
        self.goals.append({
            "slug": slug,
            "friendly": friendly,
            "events": events or [],
            "rewards": rewards or [],
            "complete": False,
            "event_states": [False for _ in (events or [])]
        })


    def complete_goal(self, goalslug: str):
        for goal in self.goals:
            if goal["slug"] == goalslug:
                goal["complete"] = True
                break

    def _event_matches_goal_event(self, goal_event: dict, event_type: str, payload: dict):
        # Check whether an event payload matches a goal event
        if goal_event.get("type") != event_type:
            return False

        for key, value in goal_event.items():
            if key == "type":
                continue
            if payload.get(key) != value:
                return False

        return True

    def handle_event(self, event_type: str, **payload):
        # Handle an incoming event and update goals
        completed_goals = []

        current_goal = None
        for goal in self.goals:
            if not goal.get("complete"):
                current_goal = goal
                break

        if current_goal is None:
            return completed_goals

        event_states = current_goal.setdefault("event_states", [False for _ in current_goal.get("events", [])])
        for index, goal_event in enumerate(current_goal.get("events", [])):
            if event_states[index]:
                continue
            if self._event_matches_goal_event(goal_event, event_type, payload):
                event_states[index] = True
                break

        if current_goal.get("events") and all(event_states):
            current_goal["complete"] = True
            completed_goals.append(current_goal["slug"])

        return completed_goals

    def is_complete(self):
        # Return True if all goals are complete
        return all(goal.get("complete", False) for goal in self.goals)

    def get_progress(self):
        total_events = 0
        completed_events = 0

        for goal in self.goals:
            events = goal.get("events", [])
            event_states = goal.setdefault("event_states", [False for _ in events])
            total_events += len(events)
            completed_events += sum(1 for state in event_states if state)

        if total_events == 0:
            return 0.0

        return completed_events / total_events

    def get_current_goal(self):
        for goal in self.goals:
            if not goal.get("complete"):
                return goal
        return None


class InteractionMap:
    # Stores entity interaction definitions and progress
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
        # Initialize runtime interaction data and progress
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

        # Return a copy of the interaction with the selected response
        return {**interaction, "response": response_text}
    


MAPS = {
    "level_1": "level1_tilemap_tmj",
    "level_2": "level2_tilemap_tmj",
    "level_3": "level3_tilemap_tmj",
    "level_4": "level4_tilemap_tmj",
    "level_5": "level5_tilemap_tmj",
}

def build_example_level():
    # Example level structure (unused helper)
    {
        "stage": 0, # stage id
        "slug": "example", # stage slug
        "interactionMap": InteractionMap(), # interaction map,
        "tilemap": None, # tilemap
        "objective": Objective("objective", "description") # objective
    }

# Level 1: Reception w/ Sgt Pritton
def build_level_1():
    # Build level 1: reception and basic goals
    obj = Objective("Welcome to MWBI!", "Get to know your controls.")
    obj.add_goal("interact",
                 "Interact with Sgt. Pritton by walking over to him and pressing [return].",
                 [{
                    "type": "interaction",
                    "entityId": "pritton"
                 }])
    obj.add_goal("meetstudents",
                 "Get to know 5 other students.",
                 [
                 {
                     "type": "interaction",
                     "entityId": "student1"
                 },
                 {
                     "type": "interaction",
                     "entityId": "student2"
                 },
                 {
                     "type": "interaction",
                     "entityId": "student3"
                 },
                 {
                     "type": "interaction",
                     "entityId": "student4"
                 },
                 {
                     "type": "interaction",
                     "entityId": "student5"
                 },
                 ])
    obj.add_goal("finish", "Go back and talk to Sgt. Pritton",
                 [{
                     "type": "interaction",
                     "entityId": "pritton"
                 }],
                 [{
                    "type": "scene",
                    "icon": "pritton_icon",
                    "name": "Sgt. Pritton",
                    "content": "Well done on talking to the other students. It's time for your next class!"
                 },
                 {"type": "storyProgression"}])
    tm = MAPS["level_1"]
    im = InteractionMap()
    im.add_entity_interaction("pritton", "Sgt. Pritton", "pritton_icon", ["Welcome to MWBI!", "At this school, we very strict standards.", "But for now, you should go and meet some of your peers."], False, "Follow the instructions in the top right corner of the screen to continue.")
    im.add_entity_interaction("student1", "Student", "student_icon", ["Hey, I'm just getting settled in.", "I think the classrooms are over there."], False, "I'm focused on class right now.")
    im.add_entity_interaction("student2", "Student", "student_icon", ["The school feels a lot bigger than I expected.", "Maybe the teacher can point you in the right direction."], False, "I should get back to my desk.")
    im.add_entity_interaction("student3", "Student", "student_icon", ["I'm trying to remember where everything is.", "A lot of people are still finding their way around."], False, "Sorry, I need to keep moving.")
    im.add_entity_interaction("student4", "Student", "student_icon", ["Have you met Sgt. Pritton yet?", "He seems to know everything about this place."], False, "I have to finish getting ready for class.")
    im.add_entity_interaction("student5", "Student", "student_icon", ["I heard the first lesson is all about the basics.", "That should make it easier to settle in."], False, "Maybe talk to the teacher first.")
    return {
        "stage": 1, # stage id
        "slug": "level1", # stage slug
        "interactionMap": im, # interaction map,
        "tilemap": tm, # tilemap
        "objective": obj # objective
    }

# Level 2: Maths Classroom w/ Ms Pernando
def build_level_2():
    # Level 2 not yet implemented
    pass

# Level 3: Cluttered Classroom w/ Ms Nimboli
def build_level_3():
    # Level 3 not yet implemented
    pass

# Level 4: Office w/ Mr Seid
def build_level_4():
    # Level 4 not yet implemented
    pass

# Level 5: Pricipal's Office w/ Pricipal Lorbes
def build_level_5():
    # Level 5 not yet implemented
    pass


STORY = [
    {},
    build_level_1(),
    #build_level_2(),
    #build_level_3(),
    #build_level_4(),
    #build_level_5()
]