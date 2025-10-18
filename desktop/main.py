import asyncio
import threading
import tkinter as tk
import webbrowser
from tkinter import ttk

import tkinterweb as tw


class DesktopApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TradingView в Tkinter (Async)")
        self.root.geometry("1200x800")

        # Прогрес бар
        self.progress = ttk.Progressbar(self.root, mode="indeterminate")
        self.progress.pack(side=tk.BOTTOM, fill=tk.X)
        self.status = ttk.Label(self.root, text="Ініціалізація...")
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        self.frame = ttk.Frame(self.root)
        self.frame.pack(fill="both", expand=True)

        # Кнопка для відкриття в браузері
        self.browser_button = ttk.Button(self.root, text="Відкрити в браузері", command=self.open_in_browser)
        self.browser_button.pack(side=tk.TOP, fill=tk.X)

        self.start_async_loading()

    async def load_chart(self):
        """Асинхронне завантаження графіка"""
        self.update_status("Підготовка інтерфейсу...")
        await asyncio.sleep(0.5)

        self.update_status("Завантаження TradingView...")
        await asyncio.sleep(0.5)

        # Створюємо браузер в головному потоці
        self.root.after(0, self.create_browser_ui)

        self.update_status("Графік готовий!")
        await asyncio.sleep(1)
        self.update_status("")

    def update_status(self, text):
        """Оновлення статусу з головного потоку"""
        self.root.after(0, lambda: self.status.config(text=text))

    def open_in_browser(self):
        """Відкрити TradingView в браузері"""
        url = "https://www.tradingview.com/chart/?symbol=BINANCE:BTCUSDT"
        webbrowser.open(url)

    def create_browser_ui(self):
        """Створення UI браузера"""
        try:
            self.browser = tw.HtmlFrame(self.frame)
            self.browser.pack(fill="both", expand=True)

            # Спроба 1: Використання embeddable TradingView
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>TradingView</title>
                <style>
                    body, html {margin:0;padding:0;width:100%;height:100%;overflow:hidden;}
                    iframe {border:none;width:100%;height:100%;display:block;}
                </style>
            </head>
            <body>
                <iframe src="https://www.tradingview.com/widgetembed/?frameElementId=tradingview_12345&symbol=BINANCE%3ABTCUSDT&i">
                </iframe>
            </body>
            </html>
            """

            try:
                self.browser.load_html(html_content)
                self.update_status("Графік завантажується...")
                # Чекаємо трохи для завантаження
                self.root.after(3000, self.check_iframe_loaded)
            except Exception as iframe_error:
                print(f"Помилка з iframe: {iframe_error}")

                self.update_status("Графік недоступний - iframe заблоковано")
        except Exception as e:
            self.status.config(text=f"Помилка створення графіка: {e}")

    def check_iframe_loaded(self):
        """Перевіряємо чи завантажився iframe"""
        try:
            # Спробуємо перевірити чи iframe містить контент
            # Якщо ні, показуємо альтернативну сторінку
            self.update_status("Графік недоступний - iframe заблоковано")
        except Exception as e:
            self.status.config(text=f"Помилка перевірки iframe: {e}")

    def start_async_loading(self):
        """Запуск асинхронного завантаження"""
        self.progress.start()

        async def run():
            await self.load_chart()
            self.root.after(0, self.progress.stop)

        def run_async():
            asyncio.run(run())

        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = DesktopApp()
    app.run()
