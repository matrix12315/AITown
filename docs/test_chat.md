# Test Documentation: Chat Module (`tests/test_chat.py`)

## TestFormatHistory

### test_empty_history
- **Assert**: `_format_history([])` returns empty string
- **Why**: No messages = no text

### test_with_messages
- **Assert**: Output contains "Alice: Hi!" and "Bob: Hello!"
- **Why**: Each entry is formatted as "name: message"

## TestParseMessage

### test_with_prefix
- **Assert**: `_parse_message("message: Hello there!")` returns "Hello there!"
- **Why**: Strips the "message: " prefix

### test_without_prefix
- **Assert**: Returns the full text when no "message:" prefix
- **Why**: Fallback uses entire response

### test_multiline
- **Assert**: Returns only the first line after "message:"
- **Why**: Only the first line is the actual message

## TestCanChat

### test_can_chat_fresh
- **Assert**: New agent can chat with anyone
- **Why**: No cooldowns set

### test_cooldown_same_agent
- **Assert**: Returns False when general cooldown is in the future
- **Why**: Agent must wait 30 min between any conversations

### test_cooldown_same_pair
- **Assert**: Returns False when last chat with same agent was 30 min ago
- **Why**: Same pair must wait 1 hour between conversations

### test_cooldown_expired
- **Assert**: Returns True when last chat was 2 hours ago
- **Why**: 1 hour cooldown has expired

## TestClearChatState

### test_clears_state
- **Assert**: chatting_with, chat_type, chat_rounds_left, chat_history all reset
- **Why**: Conversation is over, state should be clean

### test_sets_cooldown
- **Assert**: chat_cooldown_until is set, last_chat_with contains the other agent
- **Why**: Prevents immediate re-initiation of conversation

## TestGenerateRound

### test_generates_message
- **Assert**: Returns dict with "from" and "msg" keys, chat_history grows by 1
- **Why**: LLM generates a message, stored in history

## TestGenerateSummary

### test_generates_summary
- **Assert**: Returns the LLM's summary text
- **Why**: Summary is generated from chat history

## TestStoreChatMemory

### test_stores_in_memory
- **Assert**: add_chat and add_event are both called once
- **Why**: Conversation summary stored as both chat node and event node
