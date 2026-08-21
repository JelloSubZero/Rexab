from types import SimpleNamespace

from aiogram.exceptions import TelegramBadRequest


class FakeBot:

    def __init__(self):
        self.sent = []
        self.edited = []
        self.deleted = []
        self._next_message_id = 1000
        self._edit_failures = {}

    def fail_edit(
        self,
        chat_id,
        message_id,
        message="Bad Request: message to edit not found",
    ):
        self._edit_failures[(chat_id, message_id)] = message

    async def send_message(
        self,
        chat_id,
        text,
        parse_mode=None,
        reply_markup=None,
        **kwargs,
    ):
        self._next_message_id += 1
        message_id = self._next_message_id

        self.sent.append({
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "keyboard": reply_markup,
        })

        return SimpleNamespace(
            chat=SimpleNamespace(id=chat_id),
            message_id=message_id,
        )

    async def edit_message_text(
        self,
        chat_id,
        message_id,
        text,
        parse_mode=None,
        reply_markup=None,
        **kwargs,
    ):
        key = (chat_id, message_id)

        if key in self._edit_failures:
            error_message = self._edit_failures.pop(key)
            raise TelegramBadRequest(
                method=None,
                message=error_message,
            )

        self.edited.append({
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "keyboard": reply_markup,
        })

        return SimpleNamespace(
            chat=SimpleNamespace(id=chat_id),
            message_id=message_id,
        )

    async def delete_message(self, chat_id, message_id):
        self.deleted.append((chat_id, message_id))
