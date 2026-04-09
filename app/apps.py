from django.apps import AppConfig
import threading
import asyncio
from .main import main as bot_main  # main.py dagi main funksiyasini import qilamiz

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
        # Botni asyncio loopda ishga tushiramiz
        asyncio.run(bot_main())
