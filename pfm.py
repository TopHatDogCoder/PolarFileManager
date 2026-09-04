import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Optional: use send2trash if available to move deletions to the system Trash/Recycle Bin
try:
    from send2trash import send2trash
    _HAVE_SEND2TRASH = True
except Exception:
    _HAVE_SEND2TRASH = False

app = tk.Tk()
app.title("Polar File Manager")
app.geometry("700x500")

try:
    app.iconbitmap(default="")
except Exception:
    pass

style = ttk.Style()
try:
    if sys.platform == "win32":
        style.theme_use("vista")
    else:
        style.theme_use("clam")
except Exception:
    try:
        style.theme_use("winnative")
    except Exception:
        pass

history_back = []
history_forward = []
current_dir = ""


def get_file_details(item_name, is_dir):
    if is_dir:
        return "📁 " + item_name, "Folder"

    ext = os.path.splitext(item_name)[1].lower()

    type_mapping = {
        ".py": ("🐍 " + item_name, "Python Script"),
        ".sh": ("🐚 " + item_name, "Shell Script"),
        ".bat": ("⚙️ " + item_name, "Batch File"),
        ".txt": ("📝 " + item_name, "Text Document"),
        ".md": ("📝 " + item_name, "Markdown Document"),
        ".exe": ("🖥️ " + item_name, "Executable Application"),
        ".msi": ("📦 " + item_name, "Windows Installer"),
        ".zip": ("🗜️ " + item_name, "Compressed Archive"),
        ".rar": ("🗜️ " + item_name, "Compressed Archive"),
        ".png": ("🖼️ " + item_name, "PNG Image"),
        ".jpg": ("🖼️ " + item_name, "JPEG Image"),
        ".jpeg": ("🖼️ " + item_name, "JPEG Image"),
        ".mp3": ("🎵 " + item_name, "Audio File"),
        ".wav": ("🎵 " + item_name, "Audio File"),
        ".mp4": ("🎬 " + item_name, "Video File"),
        ".mkv": ("🎬 " + item_name, "Video File"),
        ".pdf": ("📕 " + item_name, "PDF Document"),
        ".html": ("🌐 " + item_name, "HTML Document"),
        ".json": ("⚙️ " + item_name, "JSON Data")
    }

    return type_mapping.get(ext, ("📄 " + item_name, f"{ext[1:].upper() if ext else 'Unknown'} File"))


def load_files(folder_path):
    """Load the directory listing using os.scandir (more efficient) and sort by name.
    Handles permission and not-found errors gracefully.
    """
    global current_dir
    current_dir = folder_path
    path_var.set(folder_path)

    # clear the tree
    for row in file_tree.get_children():
        file_tree.delete(row)

    try:
        with os.scandir(folder_path) as it:
            entries = sorted(it, key=lambda e: e.name.lower())
            for entry in entries:
                try:
                    item_path = entry.path
                    is_dir = entry.is_dir(follow_symlinks=False)
                    display_name, item_type = get_file_details(entry.name, is_dir)
                    file_tree.insert("", "end", values=(display_name, item_type), tags=(item_path,))
                except PermissionError:
                    # skip entries we don't have permission to inspect
                    continue
    except PermissionError:
        messagebox.showerror("Permission Denied", f"Cannot access: {folder_path}")
    except FileNotFoundError:
        messagebox.showerror("Not Found", f"Folder not found: {folder_path}")
    except Exception as e:
        # fallback to os.listdir in the unlikely event scandir fails
        try:
            for item in sorted(os.listdir(folder_path), key=lambda s: s.lower()):
                item_path = os.path.join(folder_path, item)
                is_dir = os.path.isdir(item_path)
                display_name, item_type = get_file_details(item, is_dir)
                file_tree.insert("", "end", values=(display_name, item_type), tags=(item_path,))
        except Exception:
            messagebox.showerror("Error", f"Error listing {folder_path}: {e}")

    update_buttons()


def browse_folder():
    global history_back, history_forward
    selected_folder = filedialog.askdirectory()
    if selected_folder:
        if current_dir:
            history_back.append(current_dir)
            history_forward.clear()
        load_files(selected_folder)


def go_back():
    global history_back, history_forward
    if history_back:
        history_forward.append(current_dir)
        prev_dir = history_back.pop()
        load_files(prev_dir)


def go_forward():
    global history_back, history_forward
    if history_forward:
        history_back.append(current_dir)
        next_dir = history_forward.pop()
        load_files(next_dir)


def update_buttons():
    back_btn.configure(state="normal" if history_back else "disabled")
    forward_btn.configure(state="normal" if history_forward else "disabled")


def rename_item():
    sel = file_tree.selection()
    if not sel:
        return
    selected_item = sel[0]

    old_path = file_tree.item(selected_item, "tags")[0]
    old_name = os.path.basename(old_path)

    dialog = tk.Toplevel(app)
    dialog.title("Rename")
    dialog.geometry("350x130")
    dialog.resizable(False, False)
    dialog.transient(app)
    dialog.grab_set()

    try:
        dialog.iconbitmap(default="")
    except Exception:
        pass

    frame = ttk.Frame(dialog, padding=15)
    frame.pack(fill="both", expand=True)

    label = ttk.Label(frame, text=f"Enter new name for '{old_name}':")
    label.pack(fill="x", anchor="w", pady=(0, 5))

    entry_var = tk.StringVar(value=old_name)
    entry = ttk.Entry(frame, textvariable=entry_var)
    entry.pack(fill="x", pady=(0, 15))
    entry.select_range(0, tk.END)
    entry.focus()

    btn_frame = ttk.Frame(frame)
    btn_frame.pack(anchor="e")

    def on_confirm():
        new_name = entry_var.get().strip()
        if new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
                load_files(current_dir)
            except Exception as e:
                messagebox.showerror("Error", f"Could not rename item: {e}")
        dialog.destroy()

    def on_cancel():
        dialog.destroy()

    ok_btn = ttk.Button(btn_frame, text="OK", command=on_confirm, width=10)
    ok_btn.pack(side="left", padx=2)

    cancel_btn = ttk.Button(btn_frame, text="Cancel", command=on_cancel, width=10)
    cancel_btn.pack(side="left", padx=2)

    dialog.bind("<Return>", lambda e: on_confirm())
    dialog.bind("<Escape>", lambda e: on_cancel())

    app.wait_window(dialog)


def delete_item():
    sel = file_tree.selection()
    if not sel:
        return
    selected_item = sel[0]

    item_path = file_tree.item(selected_item, "tags")[0]
    item_name = os.path.basename(item_path)

    # Be explicit: warn the user this is permanent unless send2trash is available
    if _HAVE_SEND2TRASH:
        confirm = messagebox.askyesno("Delete", f"Move '{item_name}' to Trash/Recycle Bin?")
    else:
        confirm = messagebox.askyesno("Delete", f"Are you sure you want to permanently delete '{item_name}'? This will NOT go to Trash.")

    if confirm:
        try:
            if _HAVE_SEND2TRASH:
                send2trash(item_path)
            else:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            load_files(current_dir)
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete item: {e}")


def show_context_menu(event):
    item = file_tree.identify_row(event.y)
    if item:
        file_tree.selection_set(item)
        context_menu.post(event.x_root, event.y_root)


def on_double_click(event):
    sel = file_tree.selection()
    if not sel:
        return
    selected_item = sel[0]

    item_path = file_tree.item(selected_item, "tags")[0]

    if os.path.isdir(item_path):
        history_back.append(current_dir)
        history_forward.clear()
        load_files(item_path)
    else:
        try:
            if sys.platform == "win32":
                os.startfile(item_path)
            elif sys.platform == "darwin":
                subprocess.check_call(["open", item_path])
            else:
                subprocess.check_call(["xdg-open", item_path])
        except Exception:
            messagebox.showwarning(
                "No Association Found",
                f"No application is associated with this file type.\n\nFile: {os.path.basename(item_path)}"
            )


# UI layout
top_frame = ttk.Frame(app, padding=10)
top_frame.pack(fill="x")

back_btn = ttk.Button(top_frame, text="Back", command=go_back, state="disabled")
back_btn.pack(side="left", padx=2)

forward_btn = ttk.Button(top_frame, text="Forward", command=go_forward, state="disabled")
forward_btn.pack(side="left", padx=2)

browse_btn = ttk.Button(top_frame, text="Browse Folder", command=browse_folder)
browse_btn.pack(side="left", padx=5)

path_var = tk.StringVar(value="No folder selected")
path_entry = ttk.Entry(top_frame, textvariable=path_var, state="readonly", width=50)
path_entry.pack(side="left", padx=5, fill="x", expand=True)

tree_frame = ttk.Frame(app, padding=10)
tree_frame.pack(fill="both", expand=True)

# Single-selection browse mode to avoid confusion with multi-selection
file_tree = ttk.Treeview(tree_frame, columns=("Name", "Type"), show="headings", selectmode="browse")
file_tree.heading("Name", text="Name")
file_tree.heading("Type", text="Type")
file_tree.column("Name", width=450)
file_tree.column("Type", width=150)
file_tree.pack(side="left", fill="both", expand=True)

context_menu = tk.Menu(app, tearoff=0)
context_menu.add_command(label="Rename", command=rename_item)
context_menu.add_command(label="Delete", command=delete_item)

file_tree.bind("<Double-1>", on_double_click)
file_tree.bind("<Button-3>", show_context_menu)
file_tree.bind("<Button-2>", show_context_menu)

scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=file_tree.yview)
file_tree.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")

app.mainloop()
