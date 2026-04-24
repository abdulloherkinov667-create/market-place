from django.apps import AppConfig
import threading
import asyncio

class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        # Django ishga tushganda botni alohida threadda ishga tushiramiz
        if not hasattr(self, '_bot_thread_started'):
            self._bot_thread_started = True
            bot_thread = threading.Thread(target=self.start_bot, daemon=True)
            bot_thread.start()

    def start_bot(self):
        from .main import main as bot_main  # takror import
        # Botni asyncio loopda ishga tushiramiz
        asyncio.run(bot_main())
