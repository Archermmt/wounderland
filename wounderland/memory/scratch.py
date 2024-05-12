class Scratch:
    def __init__(self, config):
        # REFLECTION VARIABLES
        self.concept_forget = 100
        self.daily_reflection_time = 60 * 3
        self.daily_reflection_size = 5
        self.overlap_reflect_th = 2
        self.kw_strg_event_reflect_th = 4
        self.kw_strg_thought_reflect_th = 4

        # New reflection variables
        self.recency_w = 1
        self.relevance_w = 1
        self.importance_w = 1
        self.recency_decay = 0.99
        self.importance_trigger_max = 150
        self.importance_trigger_curr = self.importance_trigger_max
        self.importance_ele_n = 0
        self.thought_count = 5

        self.describe = config["describe"]
        """
        # PERSONA PLANNING
        # <daily_req> is a list of various goals the persona is aiming to achieve
        # today.
        # e.g., ['Work on her paintings for her upcoming show',
        #        'Take a break to watch some TV',
        #        'Make lunch for herself',
        #        'Work on her paintings some more',
        #        'Go to bed early']
        # They have to be renewed at the end of the day, which is why we are
        # keeping track of when they were first generated.
        self.daily_req = []
        # <f_daily_schedule> denotes a form of long term planning. This lays out
        # the persona's daily plan.
        # Note that we take the long term planning and short term decomposition
        # appoach, which is to say that we first layout hourly schedules and
        # gradually decompose as we go.
        # Three things to note in the example below:
        # 1) See how "sleeping" was not decomposed -- some of the common events
        #    really, just mainly sleeping, are hard coded to be not decomposable.
        # 2) Some of the elements are starting to be decomposed... More of the
        #    things will be decomposed as the day goes on (when they are
        #    decomposed, they leave behind the original hourly action description
        #    in tact).
        # 3) The latter elements are not decomposed. When an event occurs, the
        #    non-decomposed elements go out the window.
        # e.g., [['sleeping', 360],
        #         ['wakes up and ... (wakes up and stretches ...)', 5],
        #         ['wakes up and starts her morning routine (out of bed )', 10],
        #         ...
        #         ['having lunch', 60],
        #         ['working on her painting', 180], ...]
        self.f_daily_schedule = []
        # <f_daily_schedule_hourly_org> is a replica of f_daily_schedule
        # initially, but retains the original non-decomposed version of the hourly
        # schedule.
        # e.g., [['sleeping', 360],
        #        ['wakes up and starts her morning routine', 120],
        #        ['working on her painting', 240], ... ['going to bed', 60]]
        self.f_daily_schedule_hourly_org = []

        # CURR ACTION
        # <address> is literally the string address of where the action is taking
        # place.  It comes in the form of
        # "{world}:{sector}:{arena}:{game_objects}". It is important that you
        # access this without doing negative indexing (e.g., [-1]) because the
        # latter address elements may not be present in some cases.
        # e.g., "dolores double studio:double studio:bedroom 1:bed"
        self.act_address = None
        # <start_time> is a python datetime instance that indicates when the
        # action has started.
        self.act_start_time = None
        # <duration> is the integer value that indicates the number of minutes an
        # action is meant to last.
        self.act_duration = None
        # <description> is a string description of the action.
        self.act_description = None
        # <pronunciatio> is the descriptive expression of the self.description.
        # Currently, it is implemented as emojis.
        self.act_pronunciatio = None
        # <event_form> represents the event triple that the persona is currently
        # engaged in.
        self.act_event = (self.name, None, None)

        # <obj_description> is a string description of the object action.
        self.act_obj_description = None
        # <obj_pronunciatio> is the descriptive expression of the object action.
        # Currently, it is implemented as emojis.
        self.act_obj_pronunciatio = None
        # <obj_event_form> represents the event triple that the action object is
        # currently engaged in.
        self.act_obj_event = (self.name, None, None)

        # <chatting_with> is the string name of the persona that the current
        # persona is chatting with. None if it does not exist.
        self.chatting_with = None
        # <chat> is a list of list that saves a conversation between two personas.
        # It comes in the form of: [["Dolores Murphy", "Hi"],
        #                           ["Maeve Jenson", "Hi"] ...]
        self.chat = None
        # <chatting_with_buffer>
        # e.g., ["Dolores Murphy"] = self.vision_r
        self.chatting_with_buffer = dict()
        self.chatting_end_time = None

        # <path_set> is True if we've already calculated the path the persona will
        # take to execute this action. That path is stored in the persona's
        # scratch.planned_path.
        self.act_path_set = False
        # <planned_path> is a list of x y coordinate tuples (tiles) that describe
        # the path the persona is to take to execute the <curr_action>.
        # The list does not include the persona's current tile, and includes the
        # destination tile.
        # e.g., [(50, 10), (49, 10), (48, 10), ...]
        self.planned_path = []
        """
