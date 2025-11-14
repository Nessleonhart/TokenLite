import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont
from tkinter import colorchooser
import traceback
import datetime
import re
import os
import sys

VERSION = 15
ERROR_LOG_FILENAME = f"v{VERSION}_error_log.txt"


def log_error(exc: BaseException) -> None:
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(base_dir, ERROR_LOG_FILENAME)
    except Exception:
        log_path = ERROR_LOG_FILENAME
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("=" * 50 + "\n")
            f.write(f"Timestamp: {datetime.datetime.now().isoformat()}\n")
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=f)
    except Exception:
        pass


def safe_call(func):
    def wrapper(*a, **k):
        try:
            return func(*a, **k)
        except SystemExit:
            raise
        except BaseException as e:
            log_error(e)
            try:
                messagebox.showerror("Error", f"Unexpected error logged to {ERROR_LOG_FILENAME}.")
            except Exception:
                pass
    return wrapper


PALETTES = {
    "bright": [
        "#6f86d6",
        "#f27d9b",
        "#76d6a0",
        "#e4c27a",
        "#b58be0",
        "#7fd4d9",
        "#f29ac2",
        "#d4e67f",
    ],
    "soft": [
        "#3a5a7f",
        "#7f3a3a",
        "#3a7f4a",
        "#7f6a3a",
        "#5a3a7f",
        "#3a7f78",
        "#7f3a6a",
        "#7f7f3a",
    ],
}

mono_color = "#15A9B5"

root = None
text_box = None
token_var = None
word_var = None
theme_var = None

drag_data = {"x": 0, "y": 0}


@safe_call
def update(event=None):
    text = text_box.get("1.0", "end-1c")

    words = [w for w in text.split() if w.strip()]
    word_var.set(str(len(words)))

    tokens = list(re.finditer(r"\w+|[^\w\s]", text))
    token_var.set(str(len(tokens)))

    apply_highlight(tokens)


def get_active_colors():
    mode = theme_var.get()
    if mode == 0:
        return None
    if mode == 1:
        return PALETTES["bright"]
    if mode == 2:
        return PALETTES["soft"]
    return [mono_color]


def apply_highlight(tokens):
    for tag in text_box.tag_names():
        if tag.startswith("token_"):
            text_box.tag_remove(tag, "1.0", "end")

    colors = get_active_colors()
    if not colors:
        return

    n = len(colors)
    for idx, match in enumerate(tokens):
        start, end = match.start(), match.end()
        color = colors[idx % n]
        tag = f"token_{idx}"
        text_box.tag_configure(tag, foreground=color)
        text_box.tag_add(tag, f"1.0+{start}c", f"1.0+{end}c")


@safe_call
def on_theme_change():
    update()


@safe_call
def pick_mono_color():
    global mono_color
    chosen = colorchooser.askcolor(color=mono_color)
    if chosen and chosen[1]:
        mono_color = chosen[1]
        if theme_var.get() == 3:
            update()


def start_drag(event):
    drag_data["x"] = event.x
    drag_data["y"] = event.y


def do_drag(event):
    try:
        x = event.x_root - drag_data["x"]
        y = event.y_root - drag_data["y"]
        root.geometry(f"+{x}+{y}")
    except Exception as e:
        log_error(e)


@safe_call
def main():
    global root, text_box, token_var, word_var, theme_var

    root = tk.Tk()
    root.title("TokenLite (v15)")
    root.geometry("900x460")
    root.minsize(700, 340)

    # Custom dark title bar
    root.overrideredirect(True)

    bg_main = "#0b0c10"
    bg_title = "#05060a"
    bg_header = "#0b0c10"
    fg_primary = "#ffffff"
    fg_muted = "#9ba4b5"

    root.configure(bg=bg_main)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=0)  # title bar
    root.rowconfigure(1, weight=0)  # stats + theme
    root.rowconfigure(2, weight=1)  # text area

    # Title bar
    title_bar = tk.Frame(root, bg=bg_title, padx=12, pady=4)
    title_bar.grid(row=0, column=0, sticky="ew")
    title_bar.columnconfigure(0, weight=1)
    title_bar.columnconfigure(1, weight=0)

    title_font = tkfont.Font(family="Segoe UI Semibold", size=10)
    title_label = tk.Label(
        title_bar,
        text="TokenLite",
        bg=bg_title,
        fg=fg_muted,
        font=title_font,
        anchor="w",
    )
    title_label.grid(row=0, column=0, sticky="w")

    controls = tk.Frame(title_bar, bg=bg_title)
    controls.grid(row=0, column=1, sticky="e")

    def close_app():
        root.destroy()

    def minimize_app():
        root.update_idletasks()
        root.overrideredirect(False)
        root.iconify()
        root.bind("<Map>", restore_after_minimize, add="+")

    def restore_after_minimize(event=None):
        root.overrideredirect(True)
        root.unbind("<Map>")

    btn_font = tkfont.Font(family="Segoe UI", size=9)

    min_btn = tk.Button(
        controls,
        text="–",
        command=minimize_app,
        bg=bg_title,
        fg=fg_muted,
        activebackground=bg_title,
        activeforeground=fg_primary,
        bd=0,
        padx=8,
        pady=0,
        font=btn_font,
        highlightthickness=0,
    )
    min_btn.pack(side="left")

    close_btn = tk.Button(
        controls,
        text="✕",
        command=close_app,
        bg=bg_title,
        fg=fg_muted,
        activebackground="#b3261e",
        activeforeground="#ffffff",
        bd=0,
        padx=8,
        pady=0,
        font=btn_font,
        highlightthickness=0,
    )
    close_btn.pack(side="left", padx=(2, 0))

    for widget in (title_bar, title_label):
        widget.bind("<Button-1>", start_drag)
        widget.bind("<B1-Motion>", do_drag)

    # Header with counts + theme selector
    header = tk.Frame(root, bg=bg_header, padx=20, pady=12)
    header.grid(row=1, column=0, sticky="ew")
    header.grid_columnconfigure(0, weight=1)
    header.grid_columnconfigure(1, weight=0)

    bigfont = tkfont.Font(family="Segoe UI Semibold", size=22)
    smallfont = tkfont.Font(family="Segoe UI", size=11)

    stats_container = tk.Frame(header, bg=bg_header)
    stats_container.grid(row=0, column=0, sticky="w")

    tk.Label(
        stats_container, text="Tokens", bg=bg_header, fg=fg_muted, font=smallfont
    ).grid(row=0, column=0, padx=(0, 32))
    tk.Label(
        stats_container, text="Words", bg=bg_header, fg=fg_muted, font=smallfont
    ).grid(row=0, column=1, padx=(0, 32))

    token_var = tk.StringVar(value="0")
    word_var = tk.StringVar(value="0")

    tk.Label(
        stats_container, textvariable=token_var, bg=bg_header, fg=fg_primary, font=bigfont
    ).grid(row=1, column=0, padx=(0, 32))
    tk.Label(
        stats_container, textvariable=word_var, bg=bg_header, fg=fg_primary, font=bigfont
    ).grid(row=1, column=1, padx=(0, 32))

    theme_container = tk.Frame(header, bg=bg_header)
    theme_container.grid(row=0, column=1, sticky="e")

    tk.Label(
        theme_container, text="Theme", bg=bg_header, fg=fg_muted, font=smallfont
    ).grid(row=0, column=0, columnspan=5)

    theme_var = tk.IntVar(value=1)  # default: Bright

    themes = [("No color", 0), ("Bright", 1), ("Soft", 2), ("Mono", 3)]
    for idx, (label, val) in enumerate(themes):
        rb = tk.Radiobutton(
            theme_container,
            text=label,
            variable=theme_var,
            value=val,
            command=on_theme_change,
            bg=bg_header,
            fg=fg_muted,
            selectcolor=bg_header,
            activebackground=bg_header,
            activeforeground=fg_primary,
            font=("Segoe UI", 9),
            indicatoron=False,
            padx=6,
            pady=2,
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        rb.grid(row=1, column=idx, padx=2)

    mono_button = tk.Button(
        theme_container,
        text="Pick mono color",
        command=pick_mono_color,
        bg="#20232a",
        fg=fg_muted,
        activebackground="#262a33",
        activeforeground=fg_primary,
        font=("Segoe UI", 9),
        padx=8,
        pady=2,
        relief="flat",
        bd=0,
        highlightthickness=0,
    )
    mono_button.grid(row=1, column=len(themes), padx=(8, 0))

    # Main text area
    main_frame = tk.Frame(root, bg=bg_main, padx=16, pady=12)
    main_frame.grid(row=2, column=0, sticky="nsew")
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_rowconfigure(0, weight=1)

    text_box = tk.Text(
        main_frame,
        wrap="word",
        undo=True,
        bg="#15171e",
        fg=fg_primary,
        insertbackground=fg_primary,
        relief="flat",
        padx=10,
        pady=10,
        spacing1=4,
        spacing2=2,
        font=("Segoe UI", 11),
    )
    text_box.grid(row=0, column=0, sticky="nsew")

    scroll = ttk.Scrollbar(main_frame, orient="vertical", command=text_box.yview)
    scroll.grid(row=0, column=1, sticky="ns")
    text_box.configure(yscrollcommand=scroll.set)

    text_box.bind("<KeyRelease>", update)
    text_box.bind("<<Paste>>", update)
    text_box.bind("<<Cut>>", update)

    update()

    try:
        root.mainloop()
    except BaseException as e:
        log_error(e)
        raise


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_error(e)
        sys.exit(1)
