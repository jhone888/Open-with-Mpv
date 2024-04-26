import tkinter as tk
from tkinter import ttk
import threading
import time
import pyperclip
import subprocess
from pytube import YouTube
import keyboard  # Importe o módulo keyboard
import signal

signal.signal(signal.SIGINT, signal.SIG_IGN)


class YoutubeVideoManager:
    def __init__(self):
        self.waiting_urls = []
        self.executed_urls = set()
        self.executing_index = -1
        self.mpv_process = None
        self.lock = threading.Lock()
        self.running = True
        self.gui_closed = False

    def open_youtube_video(self, url):
        try:
            print("Abrindo vídeo:", url)
            if self.mpv_process is None or self.mpv_process.poll() is not None:
                self.mpv_process = subprocess.Popen(["C:\\Ai\\Video Upscalers\\mpv.exe", url])
        except FileNotFoundError:
            print("O caminho para o executável do mpv não está correto.")
        except Exception as e:
            print(f"Erro ao abrir o vídeo com o MPV: {e}")

    def monitor_mpv(self):
        try:
            while self.running:
                if self.mpv_process and self.mpv_process.poll() is not None:
                    print("MPV fechado.")
                    self.mpv_process = None
                    self.executing_index = -1
                time.sleep(1)
        except Exception as e:
            print(f"Erro ao monitorar o processo mpv: {e}")

    def process_clipboard(self):
        try:
            last_clipboard_content = ""
            while self.running:
                clipboard_content = pyperclip.paste()

                if clipboard_content != last_clipboard_content:
                    last_clipboard_content = clipboard_content
                    if clipboard_content.startswith("https://www.youtube.com/"):
                        yt = YouTube(clipboard_content)
                        title = yt.title
                        with self.lock:
                            if clipboard_content not in self.executed_urls and clipboard_content not in self.waiting_urls:
                                self.waiting_urls.append((clipboard_content, title))
                                print("Vídeo adicionado à lista de espera:", title)
                                if self.gui_closed:
                                    self.restore_gui()
                                update_waiting_list(self)

                time.sleep(5)
        except Exception as e:
            print(f"Erro inesperado: {e}")

    def stop(self):
        self.running = False

    def delete_url(self, index):
        del self.waiting_urls[index]
        update_waiting_list(self)

    def minimize_gui(self):
        self.gui_closed = True

    def restore_gui(self):
        if self.gui_closed:
            gui_thread = threading.Thread(target=self.gui_thread)
            gui_thread.start()
            self.gui_closed = False

    def gui_thread(self):
        root = tk.Tk()
        root.title("YouTube Video Manager")

        style = ttk.Style()
        style.configure('Dark.TButton', foreground='#222222', background='#333333', font=('Helvetica', 12),
                        highlightcolor='#000000')
        root.configure(bg='#1f1f1f')

        url_label = tk.Label(root, text="URL do vídeo:", font=('Helvetica', 12), foreground='#ffffff',
                             highlightcolor='#000000', bg='#1f1f1f')
        url_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        url_entry = tk.Entry(root, width=50, font=('Helvetica', 12), highlightcolor='#000000', bg='#333333',
                             fg='#000000')
        url_entry.grid(row=0, column=1, padx=5, pady=5)

        add_button = ttk.Button(root, text="Adicionar à lista de espera",
                                 command=lambda: add_to_waiting_list(url_entry, self), style='Dark.TButton')
        add_button.grid(row=0, column=2, padx=5, pady=5)

        waiting_list_label = tk.Label(root, text="Vídeos:", font=('Helvetica', 12), foreground='#ffffff',
                                      highlightcolor='#000000', bg='#1f1f1f')
        waiting_list_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

        self.waiting_list = tk.Listbox(root, width=70, font=('Helvetica', 12), highlightcolor='#000000',
                                          bg='#333333', fg='#ffffff')
        self.waiting_list.grid(row=2, column=0, columnspan=3, padx=5, pady=5)

        start_button = ttk.Button(root, text="Iniciar", command=lambda: start_video(self), style='Dark.TButton')
        start_button.grid(row=3, column=0, padx=5, pady=5)

        next_button = ttk.Button(root, text="Próximo", command=lambda: next_video(self), style='Dark.TButton')
        next_button.grid(row=3, column=1, padx=5, pady=5)

        previous_button = ttk.Button(root, text="Anterior", command=lambda: previous_video(self),
                                     style='Dark.TButton')
        previous_button.grid(row=3, column=2, padx=5, pady=5)

        delete_button = ttk.Button(root, text="Delete Url", command=lambda: delete_url(self), style='Dark.TButton')
        delete_button.grid(row=4, column=0, padx=5, pady=5)

        def on_closing():
            self.minimize_gui()
            root.withdraw()  # Esconder a janela ao invés de fechá-la

        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()


def add_to_waiting_list(url_entry, manager):
    url = url_entry.get()
    if url and url not in manager.executed_urls and url not in [item[0] for item in manager.waiting_urls]:
        yt = YouTube(url)
        title = yt.title
        manager.waiting_urls.append((url, title))
        update_waiting_list(manager)
        url_entry.delete(0, tk.END)
        if manager.gui_closed:  # Verifica se o GUI está minimizado
            manager.restore_gui()  # Restaura o GUI


def start_video(manager):
    if manager.executing_index == -1:
        selected_index = manager.waiting_list.curselection()
        if selected_index:
            manager.executing_index = selected_index[0]
            url, _ = manager.waiting_urls[manager.executing_index]
            print("Iniciando vídeo:", url)
            manager.open_youtube_video(url)


def next_video(manager):
    if manager.mpv_process and manager.mpv_process.poll() is None:
        manager.mpv_process.terminate()
        manager.mpv_process.wait()
    if manager.executing_index < len(manager.waiting_urls) - 1:
        manager.executing_index += 1
        url, _ = manager.waiting_urls[manager.executing_index]
        print("Próximo vídeo:", url)
        manager.open_youtube_video(url)


def previous_video(manager):
    if manager.mpv_process and manager.mpv_process.poll() is None:
        manager.mpv_process.terminate()
        manager.mpv_process.wait()
    if manager.executing_index > 0:
        manager.executing_index -= 1
        url, _ = manager.waiting_urls[manager.executing_index]
        print("Vídeo anterior:", url)
        manager.open_youtube_video(url)


def delete_url(manager):
    selected_index = manager.waiting_list.curselection()
    if selected_index:
        index = int(selected_index[0])
        manager.delete_url(index)
        update_waiting_list(manager)


def update_waiting_list(manager):
    manager.waiting_list.delete(0, tk.END)
    if manager.executing_index >= 0:
        manager.waiting_list.insert(tk.END, "Execução: " + manager.waiting_urls[manager.executing_index][1])
    for i, (url, title) in enumerate(manager.waiting_urls):
        if i != manager.executing_index:
            manager.waiting_list.insert(tk.END, f"Lista de Espera: {title} - {url}")


def main():
    # Criar a interface gráfica
    manager = YoutubeVideoManager()

    # Definir a função para ser executada quando o atalho Ctrl+Shift+C for pressionado
    keyboard.add_hotkey('ctrl+shift+x', manager.restore_gui)

    # Iniciar os threads para monitorar o clipboard e o MPV
    clipboard_thread = threading.Thread(target=manager.process_clipboard, daemon=True)
    clipboard_thread.start()

    monitor_thread = threading.Thread(target=manager.monitor_mpv, daemon=True)
    monitor_thread.start()

    # Iniciar a GUI
    manager.gui_thread()


if __name__ == "__main__":
    main()
