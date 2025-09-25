import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Notification

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Only allow authenticated users
        if self.scope["user"] == AnonymousUser():
            await self.close()
            return
            
        self.user = self.scope["user"]
        self.group_name = f"notifications_{self.user.id}"
        
        # Join notification group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send unread count on connection
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'mark_as_read':
            notification_id = data.get('notification_id')
            await self.mark_notification_as_read(notification_id)
        elif message_type == 'mark_all_as_read':
            await self.mark_all_as_read()

    # Receive message from room group
    async def notification_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_unread_count(self):
        return Notification.objects.filter(recipient=self.user, is_read=False).count()

    @database_sync_to_async
    def mark_notification_as_read(self, notification_id):
        try:
            notification = Notification.objects.get(id=notification_id, recipient=self.user)
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False

    @database_sync_to_async
    def mark_all_as_read(self):
        unread_notifications = Notification.objects.filter(recipient=self.user, is_read=False)
        count = unread_notifications.count()
        for notification in unread_notifications:
            notification.mark_as_read()
        return count
