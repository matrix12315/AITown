import pytest
import datetime
from unittest.mock import MagicMock
from agent.cognitive.chat import (
    generate_round, generate_reply, generate_summary,
    store_chat_memory, clear_chat_state, can_chat,
    _format_history, _parse_message
)


class FakeScratch:
    def __init__(self, name="Test Agent"):
        self.name = name
        self.curr_time = datetime.datetime(2023, 2, 14, 8, 0, 0)
        self.act_description = "serving coffee"
        self.act_address = "the Ville:Hobbs Cafe:cafe"
        self.chatting_with = None
        self.chat_type = None
        self.chat_rounds_left = 0
        self.chat_total_rounds = 0
        self.chat_history = []
        self.chat_cooldown_until = None
        self.last_chat_with = {}
        self.vision_r = 8

    def get_str_iss(self):
        return f"Name: {self.name}\nAge: 25\nInnate traits: friendly"


class FakePersona:
    def __init__(self, name="Test Agent"):
        self.name = name
        self.scratch = FakeScratch(name)
        self.a_mem = MagicMock()
        self.s_mem = MagicMock()


class TestFormatHistory:
    def test_empty_history(self):
        assert _format_history([]) == ""

    def test_with_messages(self):
        history = [
            {"from": "Alice", "msg": "Hi!"},
            {"from": "Bob", "msg": "Hello!"}
        ]
        result = _format_history(history)
        assert "Alice: Hi!" in result
        assert "Bob: Hello!" in result


class TestParseMessage:
    def test_with_prefix(self):
        assert _parse_message("message: Hello there!") == "Hello there!"

    def test_without_prefix(self):
        assert _parse_message("Just a plain message") == "Just a plain message"

    def test_multiline(self):
        response = "message: First line\nSecond line"
        assert _parse_message(response) == "First line"


class TestCanChat:
    def test_can_chat_fresh(self):
        p = FakePersona()
        assert can_chat(p, "Bob") is True

    def test_cooldown_same_agent(self):
        p = FakePersona()
        p.scratch.chat_cooldown_until = datetime.datetime(2023, 2, 14, 9, 0, 0)
        assert can_chat(p, "Bob") is False

    def test_cooldown_same_pair(self):
        p = FakePersona()
        p.scratch.last_chat_with["Bob"] = datetime.datetime(2023, 2, 14, 7, 30, 0)
        # Only 30 min ago, need 1 hour
        assert can_chat(p, "Bob") is False

    def test_cooldown_expired(self):
        p = FakePersona()
        p.scratch.last_chat_with["Bob"] = datetime.datetime(2023, 2, 14, 6, 0, 0)
        # 2 hours ago, cooldown expired
        assert can_chat(p, "Bob") is True


class TestClearChatState:
    def test_clears_state(self):
        p = FakePersona()
        p.scratch.chatting_with = "Bob"
        p.scratch.chat_type = "small_talk"
        p.scratch.chat_rounds_left = 3
        p.scratch.chat_history = [{"from": "p", "msg": "hi"}]

        clear_chat_state(p)

        assert p.scratch.chatting_with is None
        assert p.scratch.chat_type is None
        assert p.scratch.chat_rounds_left == 0
        assert p.scratch.chat_history == []

    def test_sets_cooldown(self):
        p = FakePersona()
        p.scratch.chatting_with = "Bob"
        clear_chat_state(p)
        assert p.scratch.chat_cooldown_until is not None
        assert "Bob" in p.scratch.last_chat_with


class TestGenerateRound:
    def test_generates_message(self):
        p1 = FakePersona("Alice")
        p2 = FakePersona("Bob")
        p1.scratch.chat_type = "small_talk"
        p1.scratch.chat_total_rounds = 3
        p1.scratch.chat_rounds_left = 3

        llm = MagicMock()
        llm.generate.return_value = "message: Hey Bob, how's it going?"

        msg = generate_round(p1, p2, llm)
        assert msg is not None
        assert msg["from"] == "Alice"
        assert "Bob" in msg["msg"] or "going" in msg["msg"]
        assert len(p1.scratch.chat_history) == 1


class TestGenerateSummary:
    def test_generates_summary(self):
        p1 = FakePersona("Alice")
        p2 = FakePersona("Bob")
        p1.scratch.chat_history = [
            {"from": "Alice", "msg": "Hi!"},
            {"from": "Bob", "msg": "Hello!"}
        ]

        llm = MagicMock()
        llm.generate.return_value = "Alice and Bob exchanged greetings."

        summary = generate_summary(p1, p2, llm)
        assert summary == "Alice and Bob exchanged greetings."


class TestStoreChatMemory:
    def test_stores_in_memory(self):
        p = FakePersona("Alice")
        llm = MagicMock()
        llm.get_embedding.return_value = [0.1] * 1024

        store_chat_memory(p, "Bob", "We talked about coffee.", llm)

        p.a_mem.add_chat.assert_called_once()
        p.a_mem.add_event.assert_called_once()
