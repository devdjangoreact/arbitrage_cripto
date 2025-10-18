import os
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

import pyautogui
import pygetwindow as gw
from PIL import Image, ImageTk


class WindowCapturer:
    """Клас для захоплення вигляду вікон програм та їх відтворення у tkinter"""

    def __init__(self, root):
        self.root = root
        self.root.title("Window Appearance Copier")
        self.root.geometry("1200x800")
        self.root.configure(bg="#2e2e2e")

        # Змінні для захоплення
        self.windows_list = []
        self.selected_window = None
        self.captured_image = None
        self.auto_refresh = False

        self.create_gui()
        self.load_windows_list()

    def create_gui(self):
        """Створення графічного інтерфейсу"""
        # Головний фрейм
        main_frame = tk.Frame(self.root, bg="#2e2e2e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Панель вибору вікна
        selection_frame = tk.LabelFrame(
            main_frame, text="Вибір вікна для копіювання", bg="#2e2e2e", fg="white", font=("Arial", 12, "bold")
        )
        selection_frame.pack(fill=tk.X, pady=(0, 10))

        # Список доступних вікон
        list_frame = tk.Frame(selection_frame, bg="#2e2e2e")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Скроллбар для списку
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.windows_listbox = tk.Listbox(
            list_frame,
            bg="#3e3e3e",
            fg="white",
            selectbackground="#4e4e4e",
            font=("Arial", 10),
            yscrollcommand=scrollbar.set,
        )
        self.windows_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.windows_listbox.yview)

        # Кнопки управління
        btn_frame = tk.Frame(selection_frame, bg="#2e2e2e")
        btn_frame.pack(fill=tk.X, pady=5)

        tk.Button(btn_frame, text="🔄 Оновити список", command=self.load_windows_list, bg="#4e4e4e", fg="white").pack(
            side=tk.LEFT, padx=2
        )

        tk.Button(btn_frame, text="📸 Захопити вигляд", command=self.capture_window, bg="#5e5e5e", fg="white").pack(
            side=tk.LEFT, padx=2
        )

        tk.Button(btn_frame, text="👁️ Показати у tkinter", command=self.show_in_tkinter, bg="#6e6e5e", fg="white").pack(
            side=tk.LEFT, padx=2
        )

        # Чекбокс для автоматичного оновлення
        self.auto_refresh_var = tk.BooleanVar()
        auto_refresh_cb = tk.Checkbutton(
            btn_frame,
            text="Автооновлення кожні 2с",
            variable=self.auto_refresh_var,
            command=self.toggle_auto_refresh,
            bg="#2e2e2e",
            fg="white",
            selectcolor="#4e4e4e",
        )
        auto_refresh_cb.pack(side=tk.RIGHT)

        # Область для відображення захопленого зображення
        display_frame = tk.LabelFrame(
            main_frame, text="Захоплений вигляд вікна", bg="#2e2e2e", fg="white", font=("Arial", 12, "bold")
        )
        display_frame.pack(fill=tk.BOTH, expand=True)

        # Полотно для зображення
        self.canvas = tk.Canvas(display_frame, bg="#1e1e1e", highlightthickness=1, highlightbackground="#4e4e4e")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Статус бар
        self.status_var = tk.StringVar(value="Готовий до роботи")
        status_bar = tk.Label(main_frame, textvariable=self.status_var, bg="#4e4e4e", fg="white", anchor="w")
        status_bar.pack(fill=tk.X, pady=(5, 0))

        # Прив'язуємо подвійний клік до списку
        self.windows_listbox.bind("<Double-Button-1>", lambda e: self.capture_window())

    def load_windows_list(self):
        """Завантаження списку відкритих вікон"""
        try:
            windows = gw.getAllWindows()
            self.windows_list = [w for w in windows if w.title and not w.isMinimized]

            # Очищуємо список
            self.windows_listbox.delete(0, tk.END)

            # Додаємо вікна до списку
            for window in self.windows_list:
                title = window.title[:50] + "..." if len(window.title) > 50 else window.title
                self.windows_listbox.insert(tk.END, f"{title} | {window.size}")

            self.status_var.set(f"Знайдено {len(self.windows_list)} відкритих вікон")

        except Exception as e:
            self.status_var.set(f"Помилка завантаження списку вікон: {str(e)}")
            messagebox.showerror("Помилка", f"Не вдалося завантажити список вікон:\n{str(e)}")

    def capture_window(self):
        """Захоплення вигляду обраного вікна"""
        selection = self.windows_listbox.curselection()
        if not selection:
            messagebox.showwarning("Попередження", "Оберіть вікно зі списку")
            return

        try:
            self.selected_window = self.windows_list[selection[0]]
            self.status_var.set(f"Захоплюю вигляд вікна: {self.selected_window.title}")

            # Захоплюємо скріншот вікна
            screenshot = pyautogui.screenshot(
                region=(
                    self.selected_window.left,
                    self.selected_window.top,
                    self.selected_window.width,
                    self.selected_window.height,
                )
            )

            # Конвертуємо для tkinter
            self.captured_image = ImageTk.PhotoImage(screenshot)

            # Відображаємо на полотні
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.captured_image)

            # Налаштовуємо скроллбари якщо потрібно
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

            self.status_var.set(f"Захоплено: {self.selected_window.title} ({screenshot.size})")

        except Exception as e:
            self.status_var.set(f"Помилка захоплення: {str(e)}")
            messagebox.showerror("Помилка", f"Не вдалося захопити вікно:\n{str(e)}")

    def show_in_tkinter(self):
        """Відображення захопленого вигляду у новому вікні tkinter"""
        if not self.captured_image:
            messagebox.showwarning("Попередження", "Спочатку захопіть вигляд вікна")
            return

        # Створюємо нове вікно
        preview_window = tk.Toplevel(self.root)
        preview_window.title(f"Копія вигляду: {self.selected_window.title}")
        preview_window.geometry(f"{self.selected_window.width}x{self.selected_window.height}")

        # Створюємо полотно для відображення
        canvas = tk.Canvas(preview_window, bg="#1e1e1e")
        canvas.pack(fill=tk.BOTH, expand=True)

        # Відображаємо зображення
        canvas.create_image(0, 0, anchor=tk.NW, image=self.captured_image)

        # Додаємо скроллбари для великих зображень
        h_scrollbar = tk.Scrollbar(preview_window, orient=tk.HORIZONTAL, command=canvas.xview)
        v_scrollbar = tk.Scrollbar(preview_window, orient=tk.VERTICAL, command=canvas.yview)

        canvas.config(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        canvas.config(scrollregion=canvas.bbox(tk.ALL))

        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def toggle_auto_refresh(self):
        """Перемикання автоматичного оновлення"""
        if self.auto_refresh_var.get():
            self.start_auto_refresh()
        else:
            self.stop_auto_refresh()

    def start_auto_refresh(self):
        """Запуск автоматичного оновлення"""
        if not hasattr(self, "_auto_refresh_thread") or not self._auto_refresh_thread.is_alive():
            self.auto_refresh = True
            self._auto_refresh_thread = threading.Thread(target=self._auto_refresh_worker, daemon=True)
            self._auto_refresh_thread.start()
            self.status_var.set("Автооновлення запущено")

    def stop_auto_refresh(self):
        """Зупинка автоматичного оновлення"""
        self.auto_refresh = False
        self.status_var.set("Автооновлення зупинено")

    def _auto_refresh_worker(self):
        """Робочий потік для автоматичного оновлення"""
        while self.auto_refresh:
            try:
                if self.selected_window and not self.selected_window.isMinimized:
                    self.capture_window()
                time.sleep(2)  # Оновлення кожні 2 секунди
            except Exception as e:
                print(f"Помилка автооновлення: {e}")
                time.sleep(1)


def create_window_capturer():
    """Функція створення вікна для захоплення вигляду програм"""
    root = tk.Tk()
    app = WindowCapturer(root)
    return root


if __name__ == "__main__":
    # Запуск додатку
    root = create_window_capturer()
    root.mainloop()
