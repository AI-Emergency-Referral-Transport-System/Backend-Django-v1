from django.contrib import admin

from accounts.models import AIMessage, AIConversationSession


admin.site.register(AIMessage)
admin.site.register(AIConversationSession)
