# bigpic.py

import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
import requests
import json
import time
import os
import threading
from PIL import Image, ImageTk
import base64
# ΔΙΟΡΘΩΘΗΚΕ: Αφαιρέθηκε το αχρησιμοποίητο import BytesIO
# from io import BytesIO

# Εισαγωγή των κλειδιών API από το αρχείο secrets.py
from secrets import BIGJPG_API_KEY, IMGBB_API_KEY


class BigJPGUpscaler:
    def __init__(self, root):
        self.root = root
        self.root.title("BigJPG Image Upscaler")
        self.root.geometry("800x600")

        # Ρυθμίσεις εμφάνισης CustomTkinter
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("green")

        # Ρυθμίσεις API (τα κλειδιά φορτώνονται από το secrets.py)
        self.bigjpg_api_key_value = BIGJPG_API_KEY
        self.imgbb_api_key_value = IMGBB_API_KEY

        self.base_url = "https://bigjpg.com/api/task/"

        # Μεταβλητές της κλάσης (ΔΙΟΡΘΩΘΗΚΕ: Δηλώνονται όλα στην __init__)
        self.selected_file = None
        self.task_id = None
        self.preview_photo = None
        self.checking_status = False
        self.result_url = None
        self.current_pil_image = None

        # ΔΙΟΡΘΩΘΗΚΕ: Αρχικοποίηση όλων των UI widget μεταβλητών εδώ
        self.file_label = None
        # self.select_image_button = None # ΔΙΟΡΘΩΘΗΚΕ: Νέα δήλωση για το select_image_button
        self.preview_label = None
        self.scale_var = None
        self.style_var = None
        self.noise_var = None
        self.upload_btn = None
        self.check_btn = None
        self.download_btn = None
        self.progress_var = None
        self.progress_bar = None
        self.status_label = None

        self.select_image_button = None  # ΕΔΩ ΕΙΝΑΙ Η ΤΕΛΕΥΤΑΙΑ ΔΙΟΡΘΩΣΗ

        self.create_widgets()
        self.load_config()

    def create_widgets(self):
        # Κύριο πλαίσιο (main_frame)
        main_frame = ctk.CTkFrame(self.root, corner_radius=10)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Ρύθμιση του grid του main_frame για τη νέα διάταξη
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=0)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=0)

        # Τμήμα επιλογής αρχείου - στην κορυφή, καλύπτει 2 στήλες
        file_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        file_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10), padx=10)
        ctk.CTkLabel(file_frame, text="Επιλογή Εικόνας", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0,
                                                                                                        columnspan=2,
                                                                                                        sticky="w",
                                                                                                        padx=10, pady=5)

        self.file_label = ctk.CTkLabel(file_frame, text="Δεν έχει επιλεγεί αρχείο")
        self.file_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)

        self.select_image_button = ctk.CTkButton(file_frame, text="Επιλογή Εικόνας", command=self.select_file,
                                                 fg_color="#6A0DAD", hover_color="#8A2BE2")
        self.select_image_button.grid(row=1, column=1, padx=(10, 10), pady=(0, 10))

        # Τμήμα Προεπισκόπησης - row 1, column 0 (καταλαμβάνει περισσότερο χώρο)
        preview_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        preview_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10), padx=10)
        ctk.CTkLabel(preview_frame, text="Προεπισκόπηση", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0,
                                                                                                         column=0,
                                                                                                         sticky="w",
                                                                                                         padx=10,
                                                                                                         pady=5)

        self.preview_label = tk.Label(preview_frame, text="Δεν έχει επιλεγεί εικόνα",  bg="#343638",
                                      fg="#BBBBBB")
        self.preview_label.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        preview_frame.rowconfigure(1, weight=1)
        preview_frame.columnconfigure(0, weight=1)

        self.preview_label.bind("<Configure>", self.on_preview_resize)

        # Τμήμα Ρυθμίσεων & Κουμπιών - row 1, column 1 (δεξιά της προεπισκόπησης)
        settings_and_controls_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        settings_and_controls_frame.grid(row=1, column=1, sticky="nsew", pady=(0, 10), padx=10)

        # Ρυθμίσεις (μέσα στο settings_and_controls_frame)
        ctk.CTkLabel(settings_and_controls_frame, text="Ρυθμίσεις Αναβάθμισης",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=10,
                                                                    pady=5)

        ctk.CTkLabel(settings_and_controls_frame, text="Συντελεστής Κλίμακας:").grid(row=1, column=0, sticky="w",
                                                                                     padx=10, pady=(10, 0))
        self.scale_var = ctk.StringVar(value="2x")
        scale_combo = ctk.CTkComboBox(settings_and_controls_frame, variable=self.scale_var,
                                      values=["2x", "4x", "8x", "16x"], state="readonly")
        scale_combo.grid(row=1, column=1, padx=(10, 10), sticky="ew", pady=(10, 0))
        settings_and_controls_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(settings_and_controls_frame, text="Στυλ:").grid(row=2, column=0, sticky="w", padx=10, pady=(10, 0))
        self.style_var = ctk.StringVar(value="art")
        style_combo = ctk.CTkComboBox(settings_and_controls_frame, variable=self.style_var,
                                      values=["art", "photo"], state="readonly")
        style_combo.grid(row=2, column=1, padx=(10, 10), sticky="ew", pady=(10, 0))

        ctk.CTkLabel(settings_and_controls_frame, text="Μείωση Θορύβου:").grid(row=3, column=0, sticky="w", padx=10,
                                                                               pady=(10, 0))
        self.noise_var = ctk.StringVar(value="1")
        noise_combo = ctk.CTkComboBox(settings_and_controls_frame, variable=self.noise_var,
                                      values=["0", "1", "2", "3"], state="readonly")
        noise_combo.grid(row=3, column=1, padx=(10, 10), sticky="ew", pady=(10, 0))

        # Κουμπιά ελέγχου (μέσα στο settings_and_controls_frame, κάτω από τις ρυθμίσεις)
        settings_and_controls_frame.rowconfigure(4, weight=1)

        self.upload_btn = ctk.CTkButton(settings_and_controls_frame, text="Έναρξη Αναβάθμισης",
                                        command=self.start_upscaling, state="disabled",
                                        fg_color="#6A0DAD", hover_color="#8A2BE2")
        self.upload_btn.grid(row=5, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="ew")

        self.check_btn = ctk.CTkButton(settings_and_controls_frame, text="Έλεγχος Κατάστασης",
                                       command=self.check_status_manual, state="disabled",
                                       fg_color="#6A0DAD", hover_color="#8A2BE2")
        self.check_btn.grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        self.download_btn = ctk.CTkButton(settings_and_controls_frame, text="Λήψη Αποτελέσματος",
                                          command=self.download_result, state="disabled",
                                          fg_color="#6A0DAD", hover_color="#8A2BE2")
        self.download_btn.grid(row=7, column=0, columnspan=2, padx=10, pady=(5, 10), sticky="ew")

        # Τμήμα Προόδου - row 2, καλύπτει 2 στήλες
        progress_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        progress_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0), padx=10)
        ctk.CTkLabel(progress_frame, text="Πρόοδος", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0,
                                                                                                    sticky="w", padx=10,
                                                                                                    pady=5)

        self.progress_var = ctk.DoubleVar()
        self.progress_bar = ctk.CTkProgressBar(progress_frame, variable=self.progress_var,
                                               orientation="horizontal", height=20,
                                               fg_color="#555555", progress_color="#6A0DAD")
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        self.progress_var.set(0.0001)
        self.progress_bar.set(0.0001)

        progress_frame.columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(progress_frame, text="Έτοιμο")
        self.status_label.grid(row=2, column=0, sticky="w", padx=10, pady=(5, 10))

        # Ρυθμίσεις του root grid για να επεκτείνεται το main_frame
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # self.current_pil_image = None

    def on_preview_resize(self, _event):
        """Καθοδηγεί την επαναφόρτωση της προεπισκόπησης όταν αλλάζει το μέγεθος του πλαισίου."""
        if self.selected_file and self.current_pil_image:
            self.load_preview(resize_only=True)

    @staticmethod
    def load_config():
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")

    @staticmethod
    def save_config():
        try:
            config = {}
            with open('config.json', 'w') as f:
                json.dump(config, f)
            messagebox.showinfo("Επιτυχία", "Η ρύθμιση αποθηκεύτηκε επιτυχώς!")
        except Exception as e:
            messagebox.showerror("Σφάλμα", f"Αποτυχία αποθήκευσης ρύθμισης: {e}")

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Επιλογή Εικόνας",
            filetypes=[
                ("Αρχεία εικόνων", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("Όλα τα αρχεία", "*.*")
            ]
        )

        if file_path:
            self.selected_file = file_path
            self.file_label.configure(text=os.path.basename(file_path))
            self.upload_btn.configure(state="normal")
            self.load_preview()
            self.reset_for_new_upload()

    def load_preview(self, resize_only=False):
        """Φορτώνει και εμφανίζει την προεπισκόπηση της εικόνας, κάνοντας 'contain' στο πλαίσιο της."""
        try:
            if not resize_only:
                self.current_pil_image = Image.open(self.selected_file)

            if self.current_pil_image is None:
                return

            self.root.update_idletasks()

            label_width = self.preview_label.winfo_width()
            label_height = self.preview_label.winfo_height()

            if label_width < 50 or label_height < 50:
                frame_width = self.preview_label.master.winfo_width() - 20
                frame_height = self.preview_label.master.winfo_height() - 20
                label_width = max(10, frame_width)
                label_height = max(10, frame_height)

            img_width, img_height = self.current_pil_image.size

            scale_factor = min(label_width / img_width, label_height / img_height)

            new_width = int(img_width * scale_factor)
            new_height = int(img_height * scale_factor)

            new_width = max(1, new_width)
            new_height = max(1, new_height)

            if new_width != img_width or new_height != img_height:
                resized_image = self.current_pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                resized_image = self.current_pil_image

            self.preview_photo = ImageTk.PhotoImage(resized_image)  # type: ignore
            self.preview_label.config(image=self.preview_photo, text="")

        except Exception as e:
            messagebox.showerror("Σφάλμα", f"Αποτυχία φόρτωσης προεπισκόπησης: {e}")

    def upload_to_imgbb(self):
        imgbb_api_key = self.imgbb_api_key_value

        if not imgbb_api_key:
            messagebox.showerror("Σφάλμα", "Το κλειδί ImgBB API δεν έχει οριστεί στο secrets.py.")
            return None

        try:
            with open(self.selected_file, 'rb') as f:
                img_data = base64.b64encode(f.read()).decode('utf-8')

            payload = {
                'key': imgbb_api_key,
                'image': img_data
            }

            self.update_status("Μεταφόρτωση εικόνας στο ImgBB...", progress=5)

            imgbb_response = requests.post("https://api.imgbb.com/1/upload", data=payload, timeout=60)
            imgbb_response.raise_for_status()

            imgbb_result = imgbb_response.json()
            if imgbb_result and imgbb_result.get('data') and imgbb_result['data'].get('url'):
                self.update_status("Η εικόνα μεταφορτώθηκε επιτυχώς στο ImgBB!", progress=15)
                return imgbb_result['data']['url']
            else:
                error_msg = imgbb_result.get('error', 'Άγνωστο σφάλμα μεταφόρτωσης ImgBB')
                messagebox.showerror("Σφάλμα Μεταφόρτωσης ImgBB", f"Αποτυχία μεταφόρτωσης στο ImgBB: {error_msg}")
                self.update_status(f"Αποτυχία μεταφόρτωσης στο ImgBB: {error_msg}", progress=0)
                return None

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Σφάλμα Δικτύου", f"Αποτυχία μεταφόρτωσης στο ImgBB: {e}")
            self.update_status(f"Σφάλμα δικτύου στο ImgBB: {e}", progress=0)
            return None
        except FileNotFoundError:
            messagebox.showerror("Σφάλμα Αρχείου", "Το επιλεγμένο αρχείο δεν βρέθηκε.")
            self.update_status("Σφάλμα αρχείου: Δεν βρέθηκε.", progress=0)
            return None
        except Exception as e:
            messagebox.showerror("Σφάλμα", f"Προέκυψε μη αναμενόμενο σφάλμα κατά τη μεταφόρτωση στο ImgBB: {e}")
            self.update_status(f"Άγνωστο σφάλμα στο ImgBB: {e}", progress=0)
            return None

    def start_upscaling(self):
        if not self.bigjpg_api_key_value:
            messagebox.showerror("Σφάλμα", "Το κλειδί BigJPG API δεν έχει οριστεί στο secrets.py.")
            return

        if not self.selected_file:
            messagebox.showerror("Σφάλμα", "Παρακαλώ επιλέξτε ένα αρχείο εικόνας")
            return

        self.upload_btn.configure(state="disabled")

        thread = threading.Thread(target=self.upload_image)
        thread.daemon = True
        thread.start()

    def upload_image(self):
        try:
            self.update_status("Προετοιμασία μεταφόρτωσης εικόνας...", progress=0)

            file_size = os.path.getsize(self.selected_file)
            if file_size > 10 * 1024 * 1024:  # 10MB
                self.update_status("Σφάλμα: Το αρχείο είναι πολύ μεγάλο (μέγ. 10MB)", progress=0)
                self.upload_btn.configure(state="normal")
                return

            image_url = self.upload_to_imgbb()
            if not image_url:
                self.upload_btn.configure(state="normal")
                return

            self.update_status("Αποστολή αιτήματος στο BigJPG API...", progress=25)

            url = "https://bigjpg.com/api/task/"
            headers = {
                'X-API-KEY': self.bigjpg_api_key_value,
                'Content-Type': 'application/json'
            }

            scale_map = {"2x": "1", "4x": "2", "8x": "3", "16x": "4"}
            noise_map = {"0": "-1", "1": "0", "2": "1", "3": "2"}

            x2_value = scale_map.get(self.scale_var.get(), "1")
            noise_value = noise_map.get(self.noise_var.get(), "0")

            data = {
                'style': self.style_var.get(),
                'noise': noise_value,
                'x2': x2_value,
                'input': image_url
            }

            print(f"Αποστολή αιτήματος στο BigJPG API...")
            print(f"Κλίμακα: {self.scale_var.get()} -> {x2_value}")
            print(f"Θόρυβος: {self.noise_var.get()} -> {noise_value}")
            print(f"Στυλ: {self.style_var.get()}")
            print(f"URL εικόνας: {image_url}")

            response = requests.post(url, headers=headers, json=data, timeout=60)

            print(f"Κατάσταση απάντησης: {response.status_code}")
            print(f"Απάντηση: {response.text}")

            if response.status_code == 200:
                try:
                    result = response.json()

                    if 'tid' in result:
                        self.update_status(f"Επιτυχής μεταφόρτωση! Αναγνωριστικό εργασίας: {result['tid']}",
                                           progress=30)
                        self.task_id = result['tid']
                        self.check_btn.configure(state="normal")

                        self.start_status_checking()

                        remaining_calls = result.get('remaining_api_calls', 'N/A')
                        print(f"Υπολειπόμενες κλήσεις BigJPG API: {remaining_calls}")

                    elif 'status' in result:
                        self.update_status(f"Αποτυχία μεταφόρτωσης: {result['status']}", progress=0)
                        self.upload_btn.configure(state="normal")
                    elif 'msg' in result:
                        error_msg = result['msg']
                        self.update_status(f"Αποτυχία μεταφόρτωσης: {error_msg}", progress=0)
                        self.upload_btn.configure(state="normal")
                    else:
                        self.update_status("Αποτυχία μεταφόρτωσης: Άγνωστη μορφή απάντησης", progress=0)
                        self.upload_btn.configure(state="normal")

                except json.JSONDecodeError:
                    self.update_status("Αποτυχία μεταφόρτωσης: Μη έγκυρη απάντηση JSON", progress=0)
                    self.upload_btn.configure(state="normal")

            elif response.status_code == 401:
                self.update_status("Σφάλμα: Μη έγκυρο κλειδί BigJPG API", progress=0)
                self.upload_btn.configure(state="normal")
            elif response.status_code == 403:
                self.update_status("Σφάλμα: Απαγορευμένη πρόσβαση στο BigJPG API - ελέγξτε τη συνδρομής σας", progress=0)
                self.upload_btn.configure(state="normal")
            else:
                self.update_status(f"Αποτυχία μεταφόρτωσης: HTTP {response.status_code}", progress=0)
                self.upload_btn.configure(state="normal")

        except requests.exceptions.Timeout:
            self.update_status("Σφάλμα μεταφόρτωσης: Λήξη χρονικού ορίου αιτήματος", progress=0)
            self.upload_btn.configure(state="normal")
        except requests.exceptions.ConnectionError:
            self.update_status("Σφάλμα μεταφόρτωσης: Αποτυχία σύνδεσης", progress=0)
            self.upload_btn.configure(state="normal")
        except Exception as e:
            messagebox.showerror("Σφάλμα", f"Προέκυψε μη αναμενόμενο σφάλμα κατά τη μεταφόρτωση: {e}")
            self.update_status(f"Σφάλμα μεταφόρτωσης: {str(e)}", progress=0)
            self.upload_btn.configure(state="normal")

    def start_status_checking(self):
        self.checking_status = True
        thread = threading.Thread(target=self.auto_check_status)
        thread.daemon = True
        thread.start()

    def auto_check_status(self):
        while self.checking_status and self.task_id:
            time.sleep(15)
            if self.checking_status and self.task_id:
                self.check_status()

    def check_status_manual(self):
        if not self.task_id:
            messagebox.showerror("Σφάλμα", "Δεν υπάρχει ενεργή εργασία")
            return

        thread = threading.Thread(target=self.check_status)
        thread.daemon = True
        thread.start()

    def check_status(self):
        if not self.task_id:
            return

        try:
            url = f"https://bigjpg.com/api/task/{self.task_id}"
            headers = {
                'X-API-KEY': self.bigjpg_api_key_value,
                'Content-Type': 'application/json'
            }

            print(f"Έλεγχος κατάστασης για εργασία: {self.task_id}")
            print(f"URL: {url}")

            response = requests.get(url, headers=headers, timeout=30)

            print(f"Κατάσταση απάντησης: {response.status_code}")
            print(f"Απάντηση κατάστασης: {response.text}")

            if response.status_code == 200:
                try:
                    result_data = response.json()

                    task_info = result_data.get(self.task_id, {})
                    status = task_info.get('status', 'unknown')

                    print(f"Κατάσταση εργασίας: {status}")

                    if status == 'success':
                        self.update_status("Επεξεργασία ολοκληρώθηκε!", progress=100)
                        self.download_btn.configure(state="normal")
                        self.checking_status = False

                        if 'url' in task_info:
                            self.result_url = task_info['url']
                            print(f"URL αποτελέσματος: {self.result_url}")

                    elif status == 'processing':
                        progress = task_info.get('progress', 0)
                        try:
                            progress_num = int(progress)
                            mapped_progress = 30 + (progress_num * 0.6)
                            print(f"BigJPG Progress: {progress_num}%, Mapped Progress: {mapped_progress}%")
                            self.update_status(f"Επεξεργασία... {progress_num}%", progress=mapped_progress)
                        except ValueError:
                            print(f"BigJPG Progress is not an integer: {progress}. Setting to default 60%.")
                            self.update_status("Επεξεργασία...", progress=60)

                    elif status == 'error':
                        error_msg = task_info.get('msg', 'Άγνωστο σφάλμα')
                        self.update_status(f"Αποτυχία επεξεργασίας: {error_msg}", progress=0)
                        self.checking_status = False
                        self.upload_btn.configure(state="normal")

                    elif status == 'waiting':
                        self.update_status("Η εργασία βρίσκεται σε αναμονή στην ουρά...", progress=25)
                    else:
                        self.update_status(f"Κατάσταση: {status}", progress=self.progress_var.get())

                except json.JSONDecodeError:
                    self.update_status("Αποτυχία ελέγχου κατάστασης: Μη έγκυρη απάντηση JSON", progress=0)

            elif response.status_code == 404:
                self.update_status("Η εργασία δεν βρέθηκε - μπορεί να έχει λήξει", progress=0)
                self.checking_status = False
                self.upload_btn.configure(state="normal")
            else:
                self.update_status(f"Αποτυχία ελέγχου κατάστασης: HTTP {response.status_code}", progress=0)

        except requests.exceptions.Timeout:
            self.update_status("Λήξη χρονικού ορίου ελέγχου κατάστασης", progress=0)
        except requests.exceptions.ConnectionError:
            self.update_status("Σφάλμα σύνδεσης ελέγχου κατάστασης", progress=0)
        except Exception as e:
            messagebox.showerror("Σφάλμα", f"Προέκυψε μη αναμενόμενο σφάλμα κατά τον έλεγχο κατάστασης: {e}")
            self.update_status(f"Σφάλμα ελέγχου κατάστασης: {str(e)}", progress=0)

    def download_result(self):
        if not self.result_url:
            messagebox.showerror("Σφάλμα", "Δεν υπάρχει ολοκληρωμένη εργασία ή διαθέσιμο URL λήψης.")
            return

        try:
            self.update_status("Λήψη αποτελέσματος...")

            img_response = requests.get(self.result_url, timeout=120)

            if img_response.status_code == 200:
                original_name = os.path.splitext(os.path.basename(self.selected_file))[0]
                scale_suffix = self.scale_var.get()
                default_filename = f"{original_name}_upscaled_{scale_suffix}.jpg"

                save_path = filedialog.asksaveasfilename(
                    initialfile=default_filename,
                    defaultextension=".jpg",
                    filetypes=[("Αρχεία JPEG", "*.jpg"), ("Αρχεία PNG", "*.png"), ("Όλα τα αρχεία", "*.*")]
                )

                if save_path:
                    with open(save_path, 'wb') as f:
                        f.write(img_response.content)

                    self.update_status(f"Η εικόνα αποθηκεύτηκε επιτυχώς!", progress=100)
                    messagebox.showinfo("Επιτυχία", f"Η εικόνα αποθηκεύτηκε στη διαδρομή:\n{save_path}")
                    self.reset_app()
                else:
                    self.update_status("Η λήψη ακυρώθηκε", progress=0)
            else:
                self.update_status(f"Αποτυχία λήψης εικόνας: HTTP {img_response.status_code}", progress=0)
        except requests.exceptions.Timeout:
            self.update_status("Σφάλμα λήψης: Λήξη χρονικού ορίου λήψης", progress=0)
        except requests.exceptions.ConnectionError:
            self.update_status("Σφάλμα λήψης: Σφάλμα σύνδεσης λήψης", progress=0)
        except Exception as e:
            messagebox.showerror("Σφάλμα", f"Προέκυψε μη αναμενόμενο σφάλμα κατά τη λήψη: {e}")
            self.update_status(f"Σφάλμα λήψης: {str(e)}", progress=0)

    def reset_for_new_upload(self):
        self.task_id = None
        self.checking_status = False
        self.result_url = None
        self.progress_var.set(0)
        self.upload_btn.configure(state="normal")
        self.check_btn.configure(state="disabled")
        self.download_btn.configure(state="disabled")
        self.update_status("Έτοιμο για αναβάθμιση νέας εικόνας.")

    def reset_app(self):
        self.selected_file = None
        self.file_label.configure(text="Δεν έχει επιλεγεί αρχείο")

        self.preview_label.config(image="", text="Δεν έχει επιλεγεί εικόνα")
        self.preview_photo = None
        self.current_pil_image = None
        self.reset_for_new_upload()

    def update_status(self, message, progress=None):
        def update_ui():
            self.status_label.configure(text=message)
            print(f"Κατάσταση: {message}")
            if progress is not None:
                self.progress_bar.set(progress / 100.0)
                print(f"Ενημέρωση προόδου σε: {progress}% (mapped to {progress / 100.0})")

        self.root.after(0, update_ui)


def main():
    root = ctk.CTk()
    app = BigJPGUpscaler(root)  # ΔΙΟΡΘΩΘΗΚΕ: Local variable 'app' value is not used
    root.mainloop()


if __name__ == "__main__":
    main()