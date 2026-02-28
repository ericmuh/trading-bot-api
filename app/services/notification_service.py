from __future__ import annotations

from app.db import store


class NotificationService:
    def publish(
        self,
        *,
        user_id: str,
        event_type: str,
        title: str,
        message: str,
        email_enabled: bool = False,
    ) -> None:
        store.create_notification(
            user_id=user_id,
            event_type=event_type,
            title=title,
            message=message,
            channel="in_app",
        )
        if email_enabled:
            store.create_notification(
                user_id=user_id,
                event_type=event_type,
                title=title,
                message=message,
                channel="email",
            )
