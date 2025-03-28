from kivymd.app import MDApp
from kivymd.uix.button import MDFloatingActionButtonSpeedDial
from kivy.lang import Builder

KV = '''
Screen:
    MDFloatingActionButtonSpeedDial:
        data: app.data
        rotation_root_button: True
'''

class FirstApp(MDApp):
    data = {
        'youtube': 'YouTube',
        'facebook': 'Facebook',
        'telegram': 'Telegram',
        'google': 'Google',
    }

    def build(self):
        return Builder.load_string(KV)

FirstApp().run()
