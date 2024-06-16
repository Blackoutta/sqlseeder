from langchain_community.chat_message_histories import ChatMessageHistory


class HistoryManager:
    def __init__(self):
        self.history = ChatMessageHistory()

    def add_messages(self, messages):
        self.history.add_messages(messages)
        return messages
