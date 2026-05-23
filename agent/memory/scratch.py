import datetime
import json


class Scratch:
    def __init__(self):
        self.vision_r = 4
        self.att_bandwidth = 3
        self.retention = 5
        self.curr_time = None
        self.curr_tile = None
        self.daily_plan_req = None

        self.name = None
        self.first_name = None
        self.last_name = None
        self.age = None
        self.innate = None
        self.learned = None
        self.currently = None
        self.lifestyle = None
        self.living_area = None

        self.concept_forget = 100
        self.daily_reflection_time = 60 * 3
        self.daily_reflection_size = 5
        self.overlap_reflect_th = 2
        self.kw_strg_event_reflect_th = 4
        self.kw_strg_thought_reflect_th = 4

        self.recency_w = 1
        self.relevance_w = 1
        self.importance_w = 1
        self.recency_decay = 0.99
        self.importance_trigger_max = 150
        self.importance_trigger_curr = self.importance_trigger_max
        self.importance_ele_n = 0
        self.thought_count = 5

        self.daily_req = []
        self.f_daily_schedule = []
        self.f_daily_schedule_hourly_org = []

        self.act_address = None
        self.act_start_time = None
        self.act_duration = None
        self.act_description = None
        self.act_pronunciatio = None
        self.act_event = (self.name, None, None)

        self.act_obj_description = None
        self.act_obj_pronunciatio = None
        self.act_obj_event = (self.name, None, None)

        self.chatting_with = None
        self.chat = None
        self.chatting_with_buffer = {}
        self.chatting_end_time = None

        self.act_path_set = False
        self.planned_path = []

    def load_from_dict(self, d):
        for key, val in d.items():
            if hasattr(self, key):
                setattr(self, key, val)

    def load_from_file(self, filepath):
        with open(filepath, 'r') as f:
            d = json.load(f)
        self.load_from_dict(d)

    def add_new_action(self, action_address, action_duration, action_description,
                       action_pronunciatio, action_event,
                       chatting_with, chat, chatting_with_buffer, chatting_end_time,
                       act_obj_description, act_obj_pronunciatio, act_obj_event,
                       act_start_time=None):
        self.act_address = action_address
        self.act_duration = action_duration
        self.act_description = action_description
        self.act_pronunciatio = action_pronunciatio
        self.act_event = action_event
        self.chatting_with = chatting_with
        self.chat = chat
        if chatting_with_buffer:
            self.chatting_with_buffer.update(chatting_with_buffer)
        self.chatting_end_time = chatting_end_time
        self.act_obj_description = act_obj_description
        self.act_obj_pronunciatio = act_obj_pronunciatio
        self.act_obj_event = act_obj_event
        self.act_start_time = self.curr_time
        self.act_path_set = False

    def act_check_finished(self):
        if not self.act_address:
            return True
        if self.chatting_with:
            end_time = self.chatting_end_time
        else:
            x = self.act_start_time
            if x.second != 0:
                x = x.replace(second=0)
                x = x + datetime.timedelta(minutes=1)
            end_time = x + datetime.timedelta(minutes=self.act_duration)
        if end_time.strftime("%H:%M:%S") == self.curr_time.strftime("%H:%M:%S"):
            return True
        return False

    def get_str_iss(self):
        commonset = ""
        commonset += f"Name: {self.name}\n"
        commonset += f"Age: {self.age}\n"
        commonset += f"Innate traits: {self.innate}\n"
        commonset += f"Learned traits: {self.learned}\n"
        commonset += f"Currently: {self.currently}\n"
        commonset += f"Lifestyle: {self.lifestyle}\n"
        commonset += f"Daily plan requirement: {self.daily_plan_req}\n"
        if self.curr_time:
            commonset += f"Current Date: {self.curr_time.strftime('%A %B %d')}\n"
        return commonset

    def get_f_daily_schedule_index(self, advance=0):
        if not self.curr_time:
            return 0
        today_min_elapsed = self.curr_time.hour * 60 + self.curr_time.minute + advance
        curr_index = 0
        elapsed = 0
        for task, duration in self.f_daily_schedule:
            elapsed += duration
            if elapsed > today_min_elapsed:
                return curr_index
            curr_index += 1
        return curr_index

    def save(self, filepath):
        d = {
            "name": self.name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "age": self.age,
            "innate": self.innate,
            "learned": self.learned,
            "currently": self.currently,
            "lifestyle": self.lifestyle,
            "living_area": self.living_area,
            "curr_tile": self.curr_tile,
            "daily_plan_req": self.daily_plan_req,
            "act_address": self.act_address,
            "act_start_time": self.act_start_time.strftime("%B %d, %Y, %H:%M:%S") if self.act_start_time else None,
            "act_duration": self.act_duration,
            "act_description": self.act_description,
            "act_pronunciatio": self.act_pronunciatio,
            "act_event": list(self.act_event) if self.act_event else None,
        }
        with open(filepath, 'w') as f:
            json.dump(d, f, indent=2)
