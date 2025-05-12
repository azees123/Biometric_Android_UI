from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from plyer import filechooser, storagepath
from datetime import datetime
import sqlite3
import os
from kivy.app import App

Window.size = (400, 700)

DB_PATH = "users.db"

def init_db():
    db_path = App.get_running_app().user_data_dir + '/users.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT,
                 emp_id TEXT UNIQUE,
                 phone TEXT,
                 fingerprint_path TEXT
             )''')
    conn.commit()
    conn.close()


class RegisterContent(BoxLayout):
    pass


Builder.load_string('''
<RegisterContent>:
    orientation: 'vertical'
    spacing: dp(10)
    size_hint_y: None
    height: self.minimum_height
    padding: dp(20)

    MDTextField:
        id: name_input
        hint_text: "Enter Name"

    MDTextField:
        id: emp_id_input
        hint_text: "Enter Employee ID"

    MDTextField:
        id: phone_input
        hint_text: "Enter Phone Number"

    MDRaisedButton:
        id: select_fp_btn
        text: "Select Fingerprint Image"
        on_release: app.select_fingerprint(self)

    MDRaisedButton:
        id: submit_btn
        text: "Submit"
        on_release: app.register_user(self)
''')

class FingerprintApp(MDApp):
    def build(self):
        self.title = "Fingerprint Verification"
        self.theme_cls.primary_palette = "Blue"
        init_db()

        self.fingerprint_path = None
        self.dialog = None

        
        self.request_permissions()

        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        register_btn = MDRaisedButton(text="Register", size_hint=(1, 0.1))
        register_btn.bind(on_press=self.open_register_popup)
        layout.add_widget(register_btn)

        verify_btn = MDRaisedButton(text="Verify", size_hint=(1, 0.1))
        verify_btn.bind(on_press=self.open_verify_popup)
        layout.add_widget(verify_btn)

        self.result_label = MDLabel(
            text="Verification Status will be shown here.",
            halign="center",
            size_hint=(1, 0.1)
        )
        layout.add_widget(self.result_label)

        return layout

    def request_permissions(self):
        """Request permission for reading/writing storage."""
        from android.permissions import request_permissions, Permission
        request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])

    def open_register_popup(self, instance):
        self.dialog_content = RegisterContent()
        self.name_input = self.dialog_content.ids.name_input
        self.emp_id_input = self.dialog_content.ids.emp_id_input
        self.phone_input = self.dialog_content.ids.phone_input
        self.select_fp_btn = self.dialog_content.ids.select_fp_btn

        self.dialog = MDDialog(
            title="Register User",
            type="custom",
            content_cls=self.dialog_content,
            buttons=[
                MDFlatButton(text="Close", on_release=lambda x: self.dialog.dismiss())
            ],
        )
        self.dialog.open()

    def select_fingerprint(self, instance):
        filechooser.open_file(
            on_selection=self.set_fingerprint_path,
            filters=["*.png", "*.jpg", "*.jpeg", "*.bmp"]
        )

    def set_fingerprint_path(self, selection):
        if selection:
            self.fingerprint_path = selection[0]
            self.select_fp_btn.text = f"Selected: {os.path.basename(self.fingerprint_path)}"

    def register_user(self, instance):
        name = self.name_input.text.strip()
        emp_id = self.emp_id_input.text.strip()
        phone = self.phone_input.text.strip()

        if not all([name, emp_id, phone, self.fingerprint_path]):
            self.show_popup("Error", "Please fill all fields and select a fingerprint.")
            return

        try:
            
            db_path = App.get_running_app().user_data_dir + '/users.db'
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("INSERT INTO users (name, emp_id, phone, fingerprint_path) VALUES (?, ?, ?, ?)",
                      (name, emp_id, phone, self.fingerprint_path))
            conn.commit()
            conn.close()
            self.dialog.dismiss()
            self.show_popup("Success", "User registered successfully.")
        except sqlite3.IntegrityError:
            self.show_popup("Error", "Employee ID already exists.")

    def open_verify_popup(self, instance):
        self.result_label.text = "Verifying fingerprint, please wait..."
        filechooser.open_file(on_selection=self.verify_fingerprint, filters=["*.png", "*.jpg", "*.jpeg", "*.bmp"])

    def verify_fingerprint(self, selection):
        try:
            if not selection:
                self.result_label.text = "No file selected. Please select a fingerprint."
                return

            selected_fp = os.path.basename(selection[0])
    
            db_path = App.get_running_app().user_data_dir + '/users.db'
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT name, emp_id, fingerprint_path FROM users")
            users = c.fetchall()
            conn.close()

            matched_user = None
            for user in users:
                stored_fp = os.path.basename(user[2])
                if stored_fp == selected_fp:
                    matched_user = user
                    break

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if matched_user:
                self.result_label.text = f"Access Granted!\nName: {matched_user[0]}\nEmp ID: {matched_user[1]}\nTime: {timestamp}"
            else:
                self.result_label.text = f"Access Denied.\nUnknown fingerprint.\nTime: {timestamp}"

        except Exception as e:
            self.result_label.text = f"An error occurred: {str(e)}"

    def show_popup(self, title, message):
        dialog = MDDialog(
            title=title,
            text=message,
            buttons=[
                MDFlatButton(text="Close", on_release=lambda x: dialog.dismiss())
            ]
        )
        dialog.open()


if __name__ == '__main__':
    FingerprintApp().run()
