import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import subprocess
import os
import shutil
import re
import threading

# ── Paths ────────────────────────────────────────────────────────────────────
# Defaults below assume a standard Steam install. Every folder can be changed
# from inside the app via the "⚙ Paths" button; choices are saved to
# tool_settings.json next to this script.
import json

_HERE         = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(_HERE, "tool_settings.json")
_STEAM_COMMON = r"C:\Program Files (x86)\Steam\steamapps\common"

DEFAULT_PATHS = {
    "dayz_tools":    os.path.join(_STEAM_COMMON, "DayZ Tools"),
    "server_stable": os.path.join(_STEAM_COMMON, "DayZServer"),
    "server_exp":    os.path.join(_STEAM_COMMON, "DayZ Server Exp"),
    "mods_source":   "P:\\",
    "staging":       os.path.join(os.path.expanduser("~"), "Desktop", "Core Stuff"),
    "modpacks":      r"D:\MODS",
}
PATH_LABELS = {
    "dayz_tools":    ("DayZ Tools folder",            "Steam → DayZ Tools → Manage → Browse local files"),
    "server_stable": ("DayZ Server folder (Stable)",  "Folder containing DayZServer_x64.exe"),
    "server_exp":    ("DayZ Server folder (Exp)",     "Experimental server, optional"),
    "mods_source":   ("Mod source drive",             "Usually P:\\ (mounted by DayZ Tools)"),
    "staging":       ("Staging folder",               "Where packed PBOs are staged"),
    "modpacks":      ("Modpacks folder",              "Contains @TheFactoryCore etc."),
}

SERVERS = {
    "stable": {
        "label":      "Stable",
        "dir":        DEFAULT_PATHS["server_stable"],
        "title":      "brnz Server Tools",
        "accent":     "#569cd6",
        "bat_name":   "brnz local",
        "selections": "server_mod_selections.json",
    },
    "exp": {
        "label":      "Experimental",
        "dir":        DEFAULT_PATHS["server_exp"],
        "title":      "brnz Server Tools - Experimental",
        "accent":     "#e5a52a",
        "bat_name":   "brnz local exp",
        "selections": "server_mod_selections_exp.json",
    },
}

MODPACKS = {
    "Core":     ("TheFactoryCore",     "TheFactoryCoreTest",     "core"),
    "Gear":     ("TheFactoryGear",     "TheFactoryGearTest",     "gear"),
    "Weapons":  ("TheFactoryWeapons",  "TheFactoryWeaponsTest",  "weapons"),
    "Vehicles": ("TheFactoryVehicles", "TheFactoryVehiclesTest", "vehicles"),
}

# These are derived from the folders above by apply_paths()
ADDON_BUILDER = DSSIGNFILE = IMAGE_TO_PAA = PUBLISHER = None
MODS_SOURCE = STAGING_BASE = MODPACK_BASE = TF_SHOP = TF_LICENSEPLATES = None
BIKEYS = {}


def read_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def write_settings(data):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def load_paths():
    """Defaults overlaid with whatever the user saved in tool_settings.json."""
    paths = dict(DEFAULT_PATHS)
    saved = read_settings().get("paths", {})
    for key in DEFAULT_PATHS:
        val = saved.get(key)
        if isinstance(val, str) and val.strip():
            paths[key] = val.strip()
    return paths


def apply_paths(paths):
    """Rebuild every derived path from the six configurable folders."""
    global ADDON_BUILDER, DSSIGNFILE, IMAGE_TO_PAA, PUBLISHER
    global MODS_SOURCE, STAGING_BASE, MODPACK_BASE, TF_SHOP, TF_LICENSEPLATES, BIKEYS
    tools = paths["dayz_tools"]
    ADDON_BUILDER = os.path.join(tools, "Bin", "AddonBuilder", "AddonBuilder.exe")
    DSSIGNFILE    = os.path.join(tools, "Bin", "DsUtils", "DSSignFile.exe")
    IMAGE_TO_PAA  = os.path.join(tools, "Bin", "ImageToPAA", "ImageToPAA.exe")
    PUBLISHER     = os.path.join(tools, "Bin", "Publisher", "Publisher.exe")

    SERVERS["stable"]["dir"] = paths["server_stable"]
    SERVERS["exp"]["dir"]    = paths["server_exp"]

    # Make sure the drive root keeps its backslash: "P:" alone would mean "cwd on P:"
    ms = paths["mods_source"]
    if re.fullmatch(r"[A-Za-z]:", ms):
        ms += "\\"
    MODS_SOURCE      = os.path.join(ms, "")
    TF_SHOP          = os.path.join(MODS_SOURCE, "TF_Shop")
    TF_LICENSEPLATES = os.path.join(MODS_SOURCE, "TF_LicensePlates")

    STAGING_BASE = paths["staging"]
    MODPACK_BASE = paths["modpacks"]
    BIKEYS = {
        "TheFactory":     os.path.join(MODPACK_BASE, "@TheFactoryCore",     "Keys", "TheFactory.biprivatekey"),
        "TheFactoryTest": os.path.join(MODPACK_BASE, "@TheFactoryCoreTest", "Keys", "TheFactoryTest.biprivatekey"),
    }


CURRENT_PATHS = load_paths()
apply_paths(CURRENT_PATHS)


# ── Main App ─────────────────────────────────────────────────────────────────
class PBOTool(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("brnz Server Tools")
        self.resizable(False, False)
        self.configure(bg="#1e1e1e")

        self.style = style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame",       background="#1e1e1e")
        style.configure("TLabel",       background="#1e1e1e", foreground="#d4d4d4", font=("Segoe UI", 10))
        style.configure("TButton",      background="#3a3a3a", foreground="#d4d4d4", font=("Segoe UI", 10), padding=6)
        style.map("TButton",            background=[("active", "#505050")])
        style.configure("TRadiobutton", background="#1e1e1e", foreground="#d4d4d4", font=("Segoe UI", 10))
        style.configure("TCheckbutton", background="#1e1e1e", foreground="#d4d4d4", font=("Segoe UI", 10))
        style.configure("TCombobox",    fieldbackground="#3a3a3a", background="#3a3a3a", foreground="#d4d4d4")
        style.configure("Header.TLabel", background="#1e1e1e", foreground="#569cd6", font=("Segoe UI", 12, "bold"))
        style.configure("Success.TLabel", background="#1e1e1e", foreground="#4ec94e", font=("Segoe UI", 10))
        style.configure("Error.TLabel",   background="#1e1e1e", foreground="#f44747", font=("Segoe UI", 10))

        # ── Mode (Stable / Experimental) ──────────────────────────────────
        self.mode = self._load_settings().get("mode", "stable")
        if self.mode not in SERVERS:
            self.mode = "stable"
        self._set_mode_paths(self.mode)

        mode_bar = ttk.Frame(self)
        mode_bar.pack(fill="x", padx=16, pady=(12, 0))
        ttk.Label(mode_bar, text="Server:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 10))
        self.mode_var = tk.StringVar(value=self.mode)
        for key in SERVERS:
            ttk.Radiobutton(mode_bar, text=SERVERS[key]["label"], variable=self.mode_var,
                            value=key, command=self._on_mode_change).pack(side="left", padx=(0, 12))
        ttk.Button(mode_bar, text="⚙ Paths", command=self._paths_dialog).pack(side="right")
        self.mode_banner = tk.Label(mode_bar, text="", bg="#1e1e1e", fg="#d4d4d4",
                                    font=("Segoe UI", 9), anchor="e")
        self.mode_banner.pack(side="right", padx=(0, 12))

        self.notebook = notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_pbo    = ttk.Frame(notebook)
        self.tab_shop   = ttk.Frame(notebook)
        self.tab_plate  = ttk.Frame(notebook)
        self.tab_server = ttk.Frame(notebook)
        notebook.add(self.tab_pbo,    text="  PBO Builder  ")
        notebook.add(self.tab_shop,   text="  Flag / Mural  ")
        notebook.add(self.tab_plate,  text="  License Plate  ")
        notebook.add(self.tab_server, text="  Local Server  ")

        self._build_pbo_tab()
        self._build_shop_tab()
        self._build_plate_tab()
        self._build_server_tab()
        self._populate_mods()
        self._apply_mode(self.mode)

        # First run on a new PC: point the user at the Paths dialog if the
        # essentials are missing and nothing has been configured yet.
        if "paths" not in read_settings() and (
                not os.path.isfile(ADDON_BUILDER) or not os.path.isdir(self.server_dir)):
            self.after(300, self._first_run_prompt)

    def _first_run_prompt(self):
        if messagebox.askyesno(
                "Set up paths",
                "DayZ Tools or the DayZ Server folder was not found at the default Steam location.\n\n"
                "Open the Paths settings now to tell the tool where they are?"):
            self._paths_dialog()

    # ── Paths dialog ───────────────────────────────────────────────────────────
    def _paths_dialog(self):
        proc = getattr(self, "_server_proc", None)
        if proc is not None and proc.poll() is None:
            messagebox.showwarning("Server running",
                                   "Stop the local server before changing paths.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Paths")
        dialog.configure(bg="#1e1e1e")
        dialog.resizable(False, False)
        dialog.grab_set()

        ttk.Label(dialog, text="Where things live on this PC", style="Header.TLabel")\
            .grid(row=0, column=0, columnspan=3, padx=12, pady=(12, 4), sticky="w")
        ttk.Label(dialog, text="Changes are saved to tool_settings.json and take effect immediately.",
                  foreground="#9a9a9a").grid(row=1, column=0, columnspan=3, padx=12, pady=(0, 8), sticky="w")

        vars_ = {}
        row = 2
        for key, (label, hint) in PATH_LABELS.items():
            ttk.Label(dialog, text=label).grid(row=row, column=0, padx=12, pady=(6, 0), sticky="w")
            var = tk.StringVar(value=CURRENT_PATHS.get(key, DEFAULT_PATHS[key]))
            vars_[key] = var
            tk.Entry(dialog, textvariable=var, width=60,
                     bg="#3a3a3a", fg="#d4d4d4", insertbackground="#d4d4d4",
                     relief="flat", font=("Segoe UI", 10)).grid(row=row, column=1, padx=(0, 6), pady=(6, 0))

            def browse(v=var):
                initial = v.get() if os.path.isdir(v.get()) else os.path.expanduser("~")
                chosen = filedialog.askdirectory(parent=dialog, initialdir=initial)
                if chosen:
                    v.set(os.path.normpath(chosen))

            ttk.Button(dialog, text="Browse…", command=browse).grid(row=row, column=2, padx=(0, 12), pady=(6, 0))
            ttk.Label(dialog, text=hint, foreground="#9a9a9a", font=("Segoe UI", 8))\
                .grid(row=row + 1, column=1, padx=(0, 6), sticky="w")
            row += 2

        def save():
            paths = {k: v.get().strip() for k, v in vars_.items()}
            empty = [PATH_LABELS[k][0] for k, v in paths.items() if not v]
            if empty:
                messagebox.showerror("Missing", "Please fill in: " + ", ".join(empty), parent=dialog)
                return
            warnings = []
            if not os.path.isfile(os.path.join(paths["dayz_tools"], "Bin", "AddonBuilder", "AddonBuilder.exe")):
                warnings.append("AddonBuilder.exe was not found under the DayZ Tools folder.")
            if not os.path.isfile(os.path.join(paths["server_stable"], "DayZServer_x64.exe")):
                warnings.append("DayZServer_x64.exe was not found in the Stable server folder.")
            if warnings and not messagebox.askyesno(
                    "Check paths", "\n".join(warnings) + "\n\nSave anyway?", parent=dialog):
                return
            self._apply_new_paths(paths)
            dialog.destroy()

        def reset():
            for k, v in vars_.items():
                v.set(DEFAULT_PATHS[k])

        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=(8, 12))
        ttk.Button(btn_frame, text="Save", command=save).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Reset to defaults", command=reset).pack(side="left", padx=6)

    def _apply_new_paths(self, paths):
        global CURRENT_PATHS
        CURRENT_PATHS = dict(paths)
        apply_paths(CURRENT_PATHS)
        data = read_settings()
        data["paths"] = CURRENT_PATHS
        write_settings(data)
        # Refresh everything that depends on the folders
        self._populate_mods()
        self._apply_mode(self.mode)
        self._log("Paths updated.", "inf")

    # ── Mode handling ─────────────────────────────────────────────────────────
    def _load_settings(self):
        return read_settings()

    def _save_settings(self):
        data = read_settings()
        data["mode"] = self.mode
        write_settings(data)

    def _set_mode_paths(self, mode):
        cfg = SERVERS[mode]
        self.mode             = mode
        self.server_dir       = cfg["dir"]
        self.start_bat        = os.path.join(cfg["dir"], "start.bat")
        self._selections_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), cfg["selections"])

    def _on_mode_change(self):
        new_mode = self.mode_var.get()
        if new_mode == self.mode:
            return
        if self._server_proc and self._server_proc.poll() is None:
            messagebox.showwarning("Server running",
                                   f"The {SERVERS[self.mode]['label']} server is still running.\n"
                                   "Stop it before switching modes.")
            self.mode_var.set(self.mode)
            return
        self._apply_mode(new_mode)

    def _apply_mode(self, mode):
        cfg = SERVERS[mode]
        self._set_mode_paths(mode)
        self.mode_var.set(mode)
        is_exp = (mode == "exp")

        # Title, accent colour, banner
        self.title(cfg["title"])
        self.style.configure("Header.TLabel", foreground=cfg["accent"])
        self.mode_banner.configure(text=cfg["dir"], fg=cfg["accent"])

        # Tabs: experimental only gets PBO Builder + Local Server
        if is_exp:
            self.notebook.hide(self.tab_shop)
            self.notebook.hide(self.tab_plate)
        else:
            self.notebook.add(self.tab_shop)
            self.notebook.add(self.tab_plate)

        # Destinations: experimental only packs to the local server
        for val, rb in self.dest_radios.items():
            if val == "local":
                continue
            if is_exp:
                rb.pack_forget()
            else:
                rb.pack(anchor="w")
        if is_exp:
            self.dest_var.set("local")
        self._on_dest_change()

        # Server tab follows the new server folder
        if not os.path.isdir(self.server_dir):
            self._log(f"Server folder not found: {self.server_dir}", "err")
        else:
            self._ensure_start_bat()
        self._load_server_mods()
        self.srv_log.configure(state="normal")
        self.srv_log.delete("1.0", "end")
        self.srv_log.configure(state="disabled")
        self._load_log()

        self._save_settings()

    def _build_pbo_tab(self):
        pad = {"padx": 12, "pady": 6}
        f = self.tab_pbo

        # Header
        ttk.Label(f, text="PBO Builder", style="Header.TLabel").grid(row=0, column=0, columnspan=2, pady=(14, 4), padx=12, sticky="w")
        ttk.Separator(f, orient="horizontal").grid(row=1, column=0, columnspan=2, sticky="ew", padx=12)

        # Mod selector with search
        ttk.Label(f, text="Mod (P:\\)").grid(row=2, column=0, sticky="nw", **pad)
        mod_frame = ttk.Frame(f)
        mod_frame.grid(row=2, column=1, sticky="w", **pad)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._filter_mods)
        search_entry = tk.Entry(mod_frame, textvariable=self.search_var, width=38,
                                bg="#3a3a3a", fg="#d4d4d4", insertbackground="#d4d4d4",
                                relief="flat", font=("Segoe UI", 10))
        search_entry.pack(anchor="w")

        list_frame = ttk.Frame(mod_frame)
        list_frame.pack(anchor="w", pady=(2, 0))
        self.mod_listbox = tk.Listbox(list_frame, width=37, height=6,
                                      bg="#2a2a2a", fg="#d4d4d4", selectbackground="#264f78",
                                      selectforeground="#ffffff", relief="flat",
                                      font=("Consolas", 9), activestyle="none")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.mod_listbox.yview)
        self.mod_listbox.configure(yscrollcommand=scrollbar.set)
        self.mod_listbox.pack(side="left")
        scrollbar.pack(side="left", fill="y")
        self.mod_listbox.bind("<<ListboxSelect>>", self._on_mod_select)
        self.mod_listbox.bind("<Double-Button-1>", self._open_mod_folder)
        self.mod_var = tk.StringVar()

        # Destination
        ttk.Label(f, text="Destination").grid(row=3, column=0, sticky="nw", **pad)
        dest_frame = ttk.Frame(f)
        dest_frame.grid(row=3, column=1, sticky="w", **pad)

        self.dest_var = tk.StringVar(value="local")
        self.dest_radios = {}
        for text, val in [("Local server (test)", "local"), ("Staging only", "staging_only"), ("Staging + Modpack", "staging"), ("Modpack only", "modpack")]:
            rb = ttk.Radiobutton(dest_frame, text=text, variable=self.dest_var, value=val, command=self._on_dest_change)
            rb.pack(anchor="w")
            self.dest_radios[val] = rb

        # Pack selector (staging/modpack)
        self.pack_frame = ttk.Frame(f)
        self.pack_frame.grid(row=4, column=0, columnspan=2, sticky="w", padx=12, pady=2)
        ttk.Label(self.pack_frame, text="Modpack").pack(side="left", padx=(0, 8))
        self.pack_var = tk.StringVar(value="Core")
        self.pack_combo = ttk.Combobox(self.pack_frame, textvariable=self.pack_var, values=list(MODPACKS.keys()), width=14, state="readonly")
        self.pack_combo.pack(side="left")

        ttk.Label(self.pack_frame, text="  Use Test pack").pack(side="left", padx=(16, 4))
        self.test_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.pack_frame, variable=self.test_var).pack(side="left")
        self.pack_frame.grid_remove()

        # Sign checkbox (staging/modpack only)
        self.sign_frame = ttk.Frame(f)
        self.sign_frame.grid(row=5, column=0, columnspan=2, sticky="w", padx=12, pady=2)
        self.sign_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.sign_frame, text="Sign PBO after packing", variable=self.sign_var).pack(anchor="w")
        self.sign_frame.grid_remove()

        ttk.Separator(f, orient="horizontal").grid(row=6, column=0, columnspan=2, sticky="ew", padx=12, pady=6)

        # Buttons
        btn_frame = ttk.Frame(f)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=4)
        self.build_btn = ttk.Button(btn_frame, text="Build", command=self._run)
        self.build_btn.pack(side="left", padx=6)
        ttk.Button(btn_frame, text="New Mod", command=self._new_mod_dialog).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Open Publisher", command=self._open_publisher).pack(side="left", padx=6)

        # Log
        self.log = scrolledtext.ScrolledText(f, width=62, height=14, bg="#111111", fg="#d4d4d4",
                                             font=("Consolas", 9), state="disabled", relief="flat")
        self.log.grid(row=8, column=0, columnspan=2, padx=12, pady=(4, 12), sticky="ew")
        self.log.tag_config("ok",  foreground="#4ec94e")
        self.log.tag_config("err", foreground="#f44747")
        self.log.tag_config("inf", foreground="#9cdcfe")

    def _populate_mods(self):
        try:
            self._all_mods = sorted([d for d in os.listdir(MODS_SOURCE) if os.path.isdir(os.path.join(MODS_SOURCE, d))])
            self._refresh_listbox(self._all_mods)
            if self._all_mods:
                self.mod_listbox.selection_set(0)
                self.mod_var.set(self._all_mods[0])
        except Exception as e:
            self._log(f"Could not list P:\\ — {e}", "err")

    def _refresh_listbox(self, mods):
        self.mod_listbox.delete(0, "end")
        for m in mods:
            self.mod_listbox.insert("end", m)

    def _filter_mods(self, *args):
        typed = self.search_var.get().lower()
        filtered = [m for m in self._all_mods if typed in m.lower()] if typed else self._all_mods
        self._refresh_listbox(filtered)
        if filtered:
            self.mod_listbox.selection_set(0)
            self.mod_var.set(filtered[0])

    def _on_mod_select(self, event=None):
        sel = self.mod_listbox.curselection()
        if sel:
            self.mod_var.set(self.mod_listbox.get(sel[0]))

    def _open_mod_folder(self, event=None):
        sel = self.mod_listbox.curselection()
        if sel:
            mod = self.mod_listbox.get(sel[0])
            path = os.path.join(MODS_SOURCE, mod)
            os.startfile(path)

    def _on_dest_change(self):
        dest = self.dest_var.get()
        if dest == "local":
            self.pack_frame.grid_remove()
            self.sign_frame.grid_remove()
        elif dest == "staging_only":
            self.pack_frame.grid()
            self.sign_frame.grid_remove()
        else:
            self.pack_frame.grid()
            self.sign_frame.grid()

    def _log(self, msg, tag=""):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _run(self):
        mod = self.mod_var.get().strip()
        if not mod or not os.path.isdir(os.path.join(MODS_SOURCE, mod)):
            messagebox.showwarning("No mod selected", "Please select a valid mod from the list.")
            return
        self.build_btn.configure(state="disabled")
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        threading.Thread(target=self._build, args=(mod,), daemon=True).start()

    def _build(self, mod):
        dest     = self.dest_var.get()
        use_test = self.test_var.get()
        pack_key = self.pack_var.get()
        sign     = self.sign_var.get()

        src = os.path.join(MODS_SOURCE, mod)

        try:
            if dest == "local":
                self._build_local(mod, src)
            elif dest == "staging_only":
                self._build_staging_only(mod, src, pack_key)
            elif dest == "staging":
                self._build_staging_and_modpack(mod, src, pack_key, use_test, sign, staging=True)
            else:
                self._build_staging_and_modpack(mod, src, pack_key, use_test, sign, staging=False)
        except Exception as e:
            self._log(f"\nFATAL: {e}", "err")
        finally:
            self.build_btn.configure(state="normal")

    # ── Local server ──────────────────────────────────────────────────────────
    def _build_local(self, mod, src):
        mod_folder = f"@{mod}"
        addons_dir = os.path.join(self.server_dir, mod_folder, "addons")
        os.makedirs(addons_dir, exist_ok=True)
        self._log(f"Packing {mod} → local {SERVERS[self.mode]['label']} server...", "inf")

        ok = self._addon_builder(src, addons_dir)
        if not ok:
            return

        self._log("Patching start.bat...", "inf")
        self._patch_startbat(mod_folder)
        self._log("Done. Restart your local server to load the mod.", "ok")

    def _patch_startbat(self, mod_folder):
        with open(self.start_bat, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = r'("-mod=)([^"]*)"'
        match = re.search(pattern, content)
        if not match:
            self._log("Could not find -mod= line in start.bat", "err")
            return

        current_mods = match.group(2)
        if mod_folder in current_mods:
            self._log(f"{mod_folder} already in start.bat, skipping.", "inf")
            return

        new_mods = current_mods.rstrip(";") + f";{mod_folder}"
        new_content = content[:match.start()] + f'"-mod={new_mods}"' + content[match.end():]

        with open(self.start_bat, "w", encoding="utf-8") as f:
            f.write(new_content)
        self._log(f"Added {mod_folder} to start.bat.", "ok")

    # ── Staging only ──────────────────────────────────────────────────────────
    def _build_staging_only(self, mod, src, pack_key):
        _, _, staging_subdir = MODPACKS[pack_key]
        out_dir = os.path.join(STAGING_BASE, staging_subdir)
        os.makedirs(out_dir, exist_ok=True)
        self._log(f"Packing {mod} → staging ({staging_subdir})...", "inf")
        ok = self._addon_builder(src, out_dir)
        if ok:
            self._log(f"Done. PBO in staging/{staging_subdir}.", "ok")

    # ── Staging + Modpack ─────────────────────────────────────────────────────
    def _build_staging_and_modpack(self, mod, src, pack_key, use_test, sign, staging):
        prod_pack, test_pack, staging_subdir = MODPACKS[pack_key]
        pack_name = test_pack if use_test else prod_pack
        bikey_name = "TheFactoryTest" if use_test else "TheFactory"
        bikey = BIKEYS[bikey_name]

        pack_addons = os.path.join(MODPACK_BASE, pack_name, "Addons")

        if staging:
            out_dir = os.path.join(STAGING_BASE, staging_subdir)
            os.makedirs(out_dir, exist_ok=True)
            self._log(f"Packing {mod} → staging ({staging_subdir})...", "inf")
            ok = self._addon_builder(src, out_dir)
            if not ok:
                return
            pbo_path = os.path.join(out_dir, f"{mod}.pbo")

            if sign:
                self._log(f"Signing with {bikey_name} key...", "inf")
                self._sign(pbo_path, bikey)

            self._log(f"Copying to modpack {pack_name}...", "inf")
            os.makedirs(pack_addons, exist_ok=True)
            dest_pbo = os.path.join(pack_addons, f"{mod}.pbo")
            self._remove_old_bisign(pack_addons, mod)
            shutil.copy2(pbo_path, dest_pbo)
            if sign:
                bisign = pbo_path + f".{bikey_name}.bisign"
                if os.path.exists(bisign):
                    shutil.copy2(bisign, pack_addons)
            self._log(f"Done. PBO in staging and {pack_name}.", "ok")

        else:
            self._log(f"Packing {mod} → modpack {pack_name}...", "inf")
            os.makedirs(pack_addons, exist_ok=True)
            self._remove_old_bisign(pack_addons, mod)
            ok = self._addon_builder(src, pack_addons)
            if not ok:
                return
            pbo_path = os.path.join(pack_addons, f"{mod}.pbo")
            if sign:
                self._log(f"Signing with {bikey_name} key...", "inf")
                self._sign(pbo_path, bikey)
            self._log(f"Done. PBO in {pack_name}.", "ok")

    def _remove_old_bisign(self, addons_dir, mod):
        for f in os.listdir(addons_dir):
            if f.startswith(f"{mod}.pbo.") and f.endswith(".bisign"):
                os.remove(os.path.join(addons_dir, f))
                self._log(f"Removed old signature: {f}", "inf")

    # ── AddonBuilder ─────────────────────────────────────────────────────────
    def _addon_builder(self, src, out_dir):
        cmd = [ADDON_BUILDER, src, out_dir, "-clear", "-packonly"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            success = "Build Successful" in result.stdout

            for line in result.stdout.splitlines():
                if any(k in line for k in ["INFO", "ERROR", "WARN"]):
                    tag = "err" if "ERROR" in line else ("ok" if "Successful" in line else "")
                    self._log(line.strip(), tag)

            if success:
                self._log("Pack successful.", "ok")
                return True

            # Failure: dump everything we have so the user can actually see why
            self._log(f"AddonBuilder exit code: {result.returncode}", "err")
            if result.stdout.strip():
                self._log("--- stdout ---", "inf")
                for line in result.stdout.splitlines():
                    if line.strip():
                        self._log(line.rstrip())
            if result.stderr.strip():
                self._log("--- stderr ---", "inf")
                for line in result.stderr.splitlines():
                    if line.strip():
                        self._log(line.rstrip(), "err")
            self._log("Pack FAILED — see output above.", "err")
            return False
        except subprocess.TimeoutExpired:
            self._log("AddonBuilder timed out (120s).", "err")
            return False
        except Exception as e:
            self._log(f"AddonBuilder launch failed: {e}", "err")
            return False

    # ── DSSignFile ────────────────────────────────────────────────────────────
    def _sign(self, pbo_path, bikey):
        cmd = [DSSIGNFILE, bikey, pbo_path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self._log("Signed successfully.", "ok")
            else:
                self._log(f"Sign failed: {result.stderr.strip()}", "err")
        except subprocess.TimeoutExpired:
            self._log("DSSignFile timed out.", "err")


    # ── Flag / Mural Tab ─────────────────────────────────────────────────────
    def _build_shop_tab(self):
        f = self.tab_shop
        pad = {"padx": 12, "pady": 6}

        ttk.Label(f, text="Flag / Mural Creator", style="Header.TLabel").grid(row=0, column=0, columnspan=2, pady=(14, 4), padx=12, sticky="w")
        ttk.Separator(f, orient="horizontal").grid(row=1, column=0, columnspan=2, sticky="ew", padx=12)

        # Type toggle
        ttk.Label(f, text="Type").grid(row=2, column=0, sticky="w", **pad)
        type_frame = ttk.Frame(f)
        type_frame.grid(row=2, column=1, sticky="w", **pad)
        self.shop_type_var = tk.StringVar(value="flag")
        ttk.Radiobutton(type_frame, text="Flag",  variable=self.shop_type_var, value="flag").pack(side="left", padx=(0, 12))
        ttk.Radiobutton(type_frame, text="Mural", variable=self.shop_type_var, value="mural").pack(side="left")

        # Internal name (folder/classname)
        ttk.Label(f, text="Name").grid(row=3, column=0, sticky="w", **pad)
        name_frame = ttk.Frame(f)
        name_frame.grid(row=3, column=1, sticky="w", **pad)
        self.shop_name_var = tk.StringVar()
        tk.Entry(name_frame, textvariable=self.shop_name_var, width=20,
                 bg="#3a3a3a", fg="#d4d4d4", insertbackground="#d4d4d4",
                 relief="flat", font=("Segoe UI", 10)).pack(side="left", padx=(0, 6))
        self.shop_name_hint = ttk.Label(name_frame, text="→ TFSHOP_flag_???", foreground="#888888", font=("Segoe UI", 9))
        self.shop_name_hint.pack(side="left")
        self.shop_type_var.trace_add("write", self._update_shop_hints)
        self.shop_name_var.trace_add("write", self._update_shop_hints)

        # Display name
        ttk.Label(f, text="Display name").grid(row=4, column=0, sticky="w", **pad)
        display_frame = ttk.Frame(f)
        display_frame.grid(row=4, column=1, sticky="w", **pad)
        self.shop_display_var = tk.StringVar()
        tk.Entry(display_frame, textvariable=self.shop_display_var, width=20,
                 bg="#3a3a3a", fg="#d4d4d4", insertbackground="#d4d4d4",
                 relief="flat", font=("Segoe UI", 10)).pack(side="left", padx=(0, 6))
        self.shop_display_hint = ttk.Label(display_frame, text='→ "TF Flag - ???"', foreground="#888888", font=("Segoe UI", 9))
        self.shop_display_hint.pack(side="left")
        self.shop_display_var.trace_add("write", self._update_shop_hints)

        # Image picker
        ttk.Label(f, text="Image (PNG)").grid(row=5, column=0, sticky="w", **pad)
        img_frame = ttk.Frame(f)
        img_frame.grid(row=5, column=1, sticky="w", **pad)
        self.shop_img_var = tk.StringVar()
        tk.Entry(img_frame, textvariable=self.shop_img_var, width=26,
                 bg="#3a3a3a", fg="#d4d4d4", insertbackground="#d4d4d4",
                 relief="flat", font=("Segoe UI", 9)).pack(side="left", padx=(0, 6))
        ttk.Button(img_frame, text="Browse", command=self._browse_image).pack(side="left")

        ttk.Separator(f, orient="horizontal").grid(row=6, column=0, columnspan=2, sticky="ew", padx=12, pady=6)

        self.shop_create_btn = ttk.Button(f, text="Create", command=self._run_shop)
        self.shop_create_btn.grid(row=7, column=0, columnspan=2, pady=4)

        self.shop_log = scrolledtext.ScrolledText(f, width=62, height=10, bg="#111111", fg="#d4d4d4",
                                                  font=("Consolas", 9), state="disabled", relief="flat")
        self.shop_log.grid(row=8, column=0, columnspan=2, padx=12, pady=(4, 12), sticky="ew")
        self.shop_log.tag_config("ok",  foreground="#4ec94e")
        self.shop_log.tag_config("err", foreground="#f44747")
        self.shop_log.tag_config("inf", foreground="#9cdcfe")

    def _update_shop_hints(self, *args):
        kind    = self.shop_type_var.get()
        name    = self.shop_name_var.get().strip() or "???"
        display = self.shop_display_var.get().strip() or "???"
        self.shop_name_hint.configure(text=f"→ TFSHOP_{kind}_{name}")
        self.shop_display_hint.configure(text=f'→ "TF {kind.capitalize()} - {display}"')

    def _browse_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if path:
            self.shop_img_var.set(path)

    def _slog(self, msg, tag=""):
        self.shop_log.configure(state="normal")
        self.shop_log.insert("end", msg + "\n", tag)
        self.shop_log.see("end")
        self.shop_log.configure(state="disabled")

    def _run_shop(self):
        name     = self.shop_name_var.get().strip().lower().replace(" ", "_")
        display  = self.shop_display_var.get().strip()
        img_path = self.shop_img_var.get().strip()
        kind     = self.shop_type_var.get()

        if not name:
            messagebox.showwarning("Missing", "Enter a name.", parent=self.tab_shop)
            return
        if not display:
            messagebox.showwarning("Missing", "Enter a display name.", parent=self.tab_shop)
            return
        if not img_path or not os.path.isfile(img_path):
            messagebox.showwarning("Missing", "Select a valid image file.", parent=self.tab_shop)
            return

        self.shop_create_btn.configure(state="disabled")
        self.shop_log.configure(state="normal")
        self.shop_log.delete("1.0", "end")
        self.shop_log.configure(state="disabled")
        threading.Thread(target=self._create_shop_item, args=(name, display, img_path, kind), daemon=True).start()

    def _create_shop_item(self, name, display, img_path, kind):
        try:
            subdir  = os.path.join(TF_SHOP, "data", f"{kind}s", name)
            paa_name = f"{name}.paa"
            paa_path = os.path.join(subdir, paa_name)
            class_name = f"TFSHOP_{kind}_{name}"
            texture_path = f"TF_Shop\\data\\{kind}s\\{name}\\{paa_name}"

            if os.path.exists(subdir):
                self._slog(f"Folder already exists: {subdir}", "err")
                return

            self._slog(f"Creating {subdir}...", "inf")
            os.makedirs(subdir)

            # Copy image
            img_ext = os.path.splitext(img_path)[1]
            shutil.copy2(img_path, os.path.join(subdir, f"{name}{img_ext}"))

            # Convert to PAA
            self._slog("Converting to PAA...", "inf")
            result = subprocess.run([IMAGE_TO_PAA, img_path, paa_path], capture_output=True, text=True, timeout=60)
            if not os.path.exists(paa_path):
                self._slog(f"PAA conversion failed: {result.stderr.strip()}", "err")
                return
            self._slog("PAA created.", "ok")

            # Delete the copied source image
            src_copy = os.path.join(subdir, f"{name}{img_ext}")
            if os.path.exists(src_copy):
                os.remove(src_copy)

            # Write config.cpp
            if kind == "flag":
                config = f"""class CfgPatches
{{
\tclass {class_name}
\t{{
\t\tunits[]={{
            {class_name}
        }};
\t\tweapons[]={{}};
\t\trequiredVersion=0.1;
\t\trequiredAddons[]=
\t\t{{
\t\t\t"DZ_Characters",
            "DZ_Data"
\t\t}};
\t}};
}};
class CfgVehicles
{{
    class Flag_Base;
    class {class_name}: Flag_Base
    {{
    \tscope=2;
\t\tdisplayname = "TF Flag - {display}";
\t\tdescriptionShort = "A Customized Flag made for {display}";
        hiddenSelections[]=
\t    {{
\t    \t"camo"
\t    }};
    \thiddenSelectionsTextures[]=
    \t{{
    \t\t"{texture_path}"
    \t}};
    \t
    }};
}}"""
            else:
                config = f"""class CfgPatches
{{
    class TF_Decor
    {{
        units[]={{
            {class_name}
        }};
        weapons[] = {{}};
        requiredVersion = 0.1;
        requiredAddons[] = {{"RPC_Scripts","DZ_Characters","DZ_Characters_Backpacks","DZ_Characters_Pants","DZ_Characters_Tops","DZ_Gear_Containers","DZ_Characters_Headgear","DZ_Gear_Camping","DZ_Gear_Crafting","DZ_Gear_Tools","DZ_Animals","DZ_Data"
\t\t}};
    }};
}};


class CfgVehicles
{{
    class BBP_WallPaper_Mural;
    class {class_name}: BBP_WallPaper_Mural
\t{{
\t\tscope = 2;
\t\tdisplayName = "TF Mural - {display}";
\t\tdescriptionShort = "A Customized Mural made for {display}";
\t\thiddenSelectionsTextures[] = {{"{texture_path}"}};
\t}};

}};"""

            with open(os.path.join(subdir, "config.cpp"), "w", encoding="utf-8") as f:
                f.write(config)
            self._slog("config.cpp written.", "ok")

            # Update classnames.txt
            classnames_path = os.path.join(TF_SHOP, "classnames.txt")
            with open(classnames_path, "r", encoding="utf-8") as f:
                content = f.read()

            section = "FLAGS" if kind == "flag" else "MURALS"
            insert_after = f"{section}\n-----------------------" if kind == "flag" else f"{section}\n---------------------"
            if insert_after in content:
                content = content.replace(insert_after, f"{insert_after}\n{class_name}", 1)
                with open(classnames_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self._slog(f"Added {class_name} to classnames.txt.", "ok")
            else:
                self._slog("Could not find section in classnames.txt — add manually.", "err")

            self._slog(f"\nDone! {class_name} created.", "ok")
            self._slog(f"Don't forget to rebuild TF_Shop PBO.", "inf")

        except Exception as e:
            self._slog(f"Error: {e}", "err")
        finally:
            self.shop_create_btn.configure(state="normal")

    # ── License Plate Tab ─────────────────────────────────────────────────────
    def _build_plate_tab(self):
        f = self.tab_plate
        pad = {"padx": 12, "pady": 6}

        ttk.Label(f, text="License Plate Creator", style="Header.TLabel").grid(row=0, column=0, columnspan=2, pady=(14, 4), padx=12, sticky="w")
        ttk.Separator(f, orient="horizontal").grid(row=1, column=0, columnspan=2, sticky="ew", padx=12)

        # Internal name (folder/classname)
        ttk.Label(f, text="Name").grid(row=2, column=0, sticky="w", **pad)
        name_frame = ttk.Frame(f)
        name_frame.grid(row=2, column=1, sticky="w", **pad)
        self.plate_name_var = tk.StringVar()
        tk.Entry(name_frame, textvariable=self.plate_name_var, width=20,
                 bg="#3a3a3a", fg="#d4d4d4", insertbackground="#d4d4d4",
                 relief="flat", font=("Segoe UI", 10)).pack(side="left", padx=(0, 6))
        self.plate_name_hint = ttk.Label(name_frame, text="→ TF_LicensePlate_???", foreground="#888888", font=("Segoe UI", 9))
        self.plate_name_hint.pack(side="left")
        self.plate_name_var.trace_add("write", self._update_plate_hints)

        # Display name
        ttk.Label(f, text="Display name").grid(row=3, column=0, sticky="w", **pad)
        display_frame = ttk.Frame(f)
        display_frame.grid(row=3, column=1, sticky="w", **pad)
        self.plate_display_var = tk.StringVar()
        tk.Entry(display_frame, textvariable=self.plate_display_var, width=20,
                 bg="#3a3a3a", fg="#d4d4d4", insertbackground="#d4d4d4",
                 relief="flat", font=("Segoe UI", 10)).pack(side="left", padx=(0, 6))
        self.plate_display_hint = ttk.Label(display_frame, text='→ "TF Plate - ???"', foreground="#888888", font=("Segoe UI", 9))
        self.plate_display_hint.pack(side="left")
        self.plate_display_var.trace_add("write", self._update_plate_hints)

        # Image picker
        ttk.Label(f, text="Image (PNG)").grid(row=4, column=0, sticky="w", **pad)
        img_frame = ttk.Frame(f)
        img_frame.grid(row=4, column=1, sticky="w", **pad)
        self.plate_img_var = tk.StringVar()
        tk.Entry(img_frame, textvariable=self.plate_img_var, width=26,
                 bg="#3a3a3a", fg="#d4d4d4", insertbackground="#d4d4d4",
                 relief="flat", font=("Segoe UI", 9)).pack(side="left", padx=(0, 6))
        ttk.Button(img_frame, text="Browse", command=self._browse_plate_image).pack(side="left")

        # Optional normal map (NOHQ)
        ttk.Label(f, text="Normal map (opt)").grid(row=5, column=0, sticky="w", **pad)
        nohq_frame = ttk.Frame(f)
        nohq_frame.grid(row=5, column=1, sticky="w", **pad)
        self.plate_nohq_var = tk.StringVar()
        tk.Entry(nohq_frame, textvariable=self.plate_nohq_var, width=26,
                 bg="#3a3a3a", fg="#d4d4d4", insertbackground="#d4d4d4",
                 relief="flat", font=("Segoe UI", 9)).pack(side="left", padx=(0, 6))
        ttk.Button(nohq_frame, text="Browse", command=self._browse_plate_nohq).pack(side="left")
        ttk.Button(nohq_frame, text="Clear", command=lambda: self.plate_nohq_var.set("")).pack(side="left", padx=(4, 0))

        ttk.Separator(f, orient="horizontal").grid(row=6, column=0, columnspan=2, sticky="ew", padx=12, pady=6)

        self.plate_create_btn = ttk.Button(f, text="Create", command=self._run_plate)
        self.plate_create_btn.grid(row=7, column=0, columnspan=2, pady=4)

        self.plate_log = scrolledtext.ScrolledText(f, width=62, height=10, bg="#111111", fg="#d4d4d4",
                                                   font=("Consolas", 9), state="disabled", relief="flat")
        self.plate_log.grid(row=8, column=0, columnspan=2, padx=12, pady=(4, 12), sticky="ew")
        self.plate_log.tag_config("ok",  foreground="#4ec94e")
        self.plate_log.tag_config("err", foreground="#f44747")
        self.plate_log.tag_config("inf", foreground="#9cdcfe")

    def _update_plate_hints(self, *args):
        name    = self.plate_name_var.get().strip() or "???"
        display = self.plate_display_var.get().strip() or "???"
        self.plate_name_hint.configure(text=f"→ TF_LicensePlate_{name}")
        self.plate_display_hint.configure(text=f'→ "TF Plate - {display}"')

    def _browse_plate_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if path:
            self.plate_img_var.set(path)

    def _browse_plate_nohq(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg"), ("PAA", "*.paa")])
        if path:
            self.plate_nohq_var.set(path)

    def _plog(self, msg, tag=""):
        self.plate_log.configure(state="normal")
        self.plate_log.insert("end", msg + "\n", tag)
        self.plate_log.see("end")
        self.plate_log.configure(state="disabled")

    def _run_plate(self):
        name      = self.plate_name_var.get().strip().lower().replace(" ", "_")
        display   = self.plate_display_var.get().strip()
        img_path  = self.plate_img_var.get().strip()
        nohq_path = self.plate_nohq_var.get().strip()

        if not name:
            messagebox.showwarning("Missing", "Enter a name.", parent=self.tab_plate)
            return
        if not display:
            messagebox.showwarning("Missing", "Enter a display name.", parent=self.tab_plate)
            return
        if not img_path or not os.path.isfile(img_path):
            messagebox.showwarning("Missing", "Select a valid image file.", parent=self.tab_plate)
            return
        if nohq_path and not os.path.isfile(nohq_path):
            messagebox.showwarning("Missing", "Normal map path is set but not a valid file.\nClear it or pick a real file.", parent=self.tab_plate)
            return

        self.plate_create_btn.configure(state="disabled")
        self.plate_log.configure(state="normal")
        self.plate_log.delete("1.0", "end")
        self.plate_log.configure(state="disabled")
        threading.Thread(target=self._create_plate_item, args=(name, display, img_path, nohq_path), daemon=True).start()

    def _create_plate_item(self, name, display, img_path, nohq_path=""):
        try:
            subdir       = os.path.join(TF_LICENSEPLATES, "data", "plates", name)
            paa_name     = f"{name}.paa"
            paa_path     = os.path.join(subdir, paa_name)
            class_name   = f"TF_LicensePlate_{name}"
            texture_path = f"TF_LicensePlates\\data\\plates\\{name}\\{paa_name}"

            if os.path.exists(subdir):
                self._plog(f"Folder already exists: {subdir}", "err")
                return

            self._plog(f"Creating {subdir}...", "inf")
            os.makedirs(subdir)

            # Convert to PAA
            self._plog("Converting to PAA...", "inf")
            result = subprocess.run([IMAGE_TO_PAA, img_path, paa_path], capture_output=True, text=True, timeout=60)
            if not os.path.exists(paa_path):
                self._plog(f"PAA conversion failed: {result.stderr.strip()}", "err")
                return
            self._plog("PAA created.", "ok")

            # ── Optional normal map (NOHQ) ─────────────────────────────────
            # If supplied, write a per-plate .rvmat that uses this plate's own
            # _co + _nohq, and override hiddenSelectionsMaterials. If left blank
            # the plate inherits Callatic's default material (Stage1 NOHQ).
            material_block = ""
            if nohq_path:
                nohq_paa_name = f"{name}_nohq.paa"
                nohq_paa_path = os.path.join(subdir, nohq_paa_name)
                nohq_tex_rel  = f"TF_LicensePlates\\data\\plates\\{name}\\{nohq_paa_name}"
                rvmat_name    = f"{name}.rvmat"
                rvmat_rel     = f"TF_LicensePlates\\data\\plates\\{name}\\{rvmat_name}"

                if nohq_path.lower().endswith(".paa"):
                    # Already a PAA — copy in as-is
                    shutil.copy2(nohq_path, nohq_paa_path)
                    self._plog("Normal map copied (PAA).", "ok")
                else:
                    # Feed ImageToPAA a *_nohq source so it packs as DXT5 (normal-map format)
                    ext = os.path.splitext(nohq_path)[1] or ".png"
                    tmp_src = os.path.join(subdir, f"{name}_nohq{ext}")
                    shutil.copy2(nohq_path, tmp_src)
                    self._plog("Converting normal map to PAA...", "inf")
                    subprocess.run([IMAGE_TO_PAA, tmp_src, nohq_paa_path], capture_output=True, text=True, timeout=60)
                    if os.path.exists(tmp_src):
                        os.remove(tmp_src)
                    if not os.path.exists(nohq_paa_path):
                        self._plog("Normal map PAA conversion failed.", "err")
                        return
                    self._plog("Normal map PAA created.", "ok")

                # Per-plate material referencing this plate's own _co + _nohq
                rvmat = self._plate_rvmat(texture_path, nohq_tex_rel)
                with open(os.path.join(subdir, rvmat_name), "w", encoding="utf-8") as rf:
                    rf.write(rvmat)
                self._plog("rvmat written.", "ok")

                material_block = (
                    "\n    \thiddenSelectionsMaterials[]=\n"
                    "    \t{\n"
                    f"    \t\t\"{rvmat_rel}\"\n"
                    "    \t};"
                )

            # Write config.cpp — inherits LicensePlate_Base from the loaded Callatic mod
            config = f"""class CfgPatches
{{
\tclass {class_name}
\t{{
\t\tunits[]={{
            {class_name}
        }};
\t\tweapons[]={{}};
\t\trequiredVersion=0.1;
\t\trequiredAddons[]=
\t\t{{
\t\t\t"Callatic_Vehicles_License_Plates"
\t\t}};
\t}};
}};
class CfgVehicles
{{
    class LicensePlate_Base;
    class {class_name}: LicensePlate_Base
    {{
    \tscope=2;
\t\tdisplayName = "TF Plate - {display}";
\t\tdescriptionShort = "A Customized License Plate made for {display}";
        hiddenSelections[]=
\t    {{
\t    \t"camo"
\t    }};
    \thiddenSelectionsTextures[]=
    \t{{
    \t\t"{texture_path}"
    \t}};{material_block}
    \t
    }};
}}"""

            with open(os.path.join(subdir, "config.cpp"), "w", encoding="utf-8") as f:
                f.write(config)
            self._plog("config.cpp written.", "ok")

            # Update classnames.txt
            classnames_path = os.path.join(TF_LICENSEPLATES, "classnames.txt")
            insert_after = "LICENSE PLATES\n-----------------------"
            try:
                with open(classnames_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except FileNotFoundError:
                content = insert_after + "\n"
            if insert_after in content:
                content = content.replace(insert_after, f"{insert_after}\n{class_name}", 1)
            else:
                content = content.rstrip() + f"\n{class_name}\n"
            with open(classnames_path, "w", encoding="utf-8") as f:
                f.write(content)
            self._plog(f"Added {class_name} to classnames.txt.", "ok")

            self._plog(f"\nDone! {class_name} created.", "ok")
            self._plog("Rebuild the TF_LicensePlates PBO, and make sure the Callatic", "inf")
            self._plog("license-plate mod is loaded alongside it.", "inf")

        except Exception as e:
            self._plog(f"Error: {e}", "err")
        finally:
            self.plate_create_btn.configure(state="normal")

    def _plate_rvmat(self, co_path, nohq_path):
        # Same material as Callatic's plate_default.rvmat: Stage0 = _co, Stage1 = NOHQ,
        # remaining stages procedural + vanilla env map. Only Stage0/Stage1 differ per plate.
        rvmat = r"""ambient[] = {1,1,1,1};
diffuse[] = {1,1,1,1};
forcedDiffuse[] = {0,0,0,0};
emmisive[] = {0,0,0,1};
specular[] = {1,1,1,1};
specularPower = 320;

PixelShaderID = "Super";
VertexShaderID = "Super";

class Stage0
{
    texture = "__CO__";
    uvSource = "tex";
    class uvTransform
    {
        aside[] = {1,0,0};
        up[] = {0,1,0};
        dir[] = {0,0,0};
        pos[] = {0,0,0};
    };
};

class Stage1   // NOHQ (normal)
{
    texture = "__NOHQ__";
    uvSource = "tex";
    class uvTransform
    {
        aside[] = {1,0,0};
        up[] = {0,1,0};
        dir[] = {0,0,0};
        pos[] = {0,0,0};
    };
};

class Stage2
{
    texture = "#(argb,8,8,3)color(0.25,0.25,0.25,0.25,DT)";
    uvSource = "tex";
    class uvTransform
    {
        aside[] = {1,0,0};
        up[] = {0,1,0};
        dir[] = {0,0,0};
        pos[] = {0,0,0};
    };
};

class Stage3   // MC (macro) - safe blank
{
    texture = "#(argb,8,8,3)color(0,0,0,0,MC)";
    uvSource = "tex";
    class uvTransform
    {
        aside[] = {1,0,0};
        up[] = {0,1,0};
        dir[] = {0,0,0};
        pos[] = {0,0,0};
    };
};

class Stage4   // AS (ambient shadow) - white so it does NOT darken
{
    texture = "#(argb,8,8,3)color(1,1,1,1,AS)";
    uvSource = "tex";
    class uvTransform
    {
        aside[] = {1,0,0};
        up[] = {0,1,0};
        dir[] = {0,0,0};
        pos[] = {0,0,0};
    };
};

class Stage5   // SMDI (spec/gloss/metal packed)
{
    texture = "#(argb,8,8,3)color(0.5,0.5,1,1,SMDI)";
    uvSource = "tex";
    class uvTransform
    {
        aside[] = {1,0,0};
        up[] = {0,1,0};
        dir[] = {0,0,0};
        pos[] = {0,0,0};
    };
};

class Stage6   // Fresnel
{
    texture = "#(ai,64,64,1)fresnel(1.1,0.3)";
    uvSource = "tex";
    class uvTransform
    {
        aside[] = {1,0,0};
        up[] = {0,1,0};
        dir[] = {0,0,0};
        pos[] = {0,0,0};
    };
};

class Stage7   // Environment map
{
    texture = "dz\data\data\env_land_co.paa";
    uvSource = "tex";
    useWorldEnvMap = "true";
    class uvTransform
    {
        aside[] = {1,0,0};
        up[] = {0,1,0};
        dir[] = {0,0,0};
        pos[] = {0,0,0};
    };
};
"""
        return rvmat.replace("__CO__", co_path).replace("__NOHQ__", nohq_path)

    # ── Publisher ─────────────────────────────────────────────────────────────
    def _open_publisher(self):
        try:
            subprocess.Popen([PUBLISHER])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open Publisher: {e}")

    # ── New Mod ───────────────────────────────────────────────────────────────
    def _new_mod_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("New Mod")
        dialog.configure(bg="#1e1e1e")
        dialog.resizable(False, False)
        dialog.grab_set()

        ttk.Label(dialog, text="Mod name:").grid(row=0, column=0, padx=12, pady=(14, 6), sticky="w")
        name_var = tk.StringVar()
        entry = tk.Entry(dialog, textvariable=name_var, width=30,
                         bg="#3a3a3a", fg="#d4d4d4", insertbackground="#d4d4d4",
                         relief="flat", font=("Segoe UI", 10))
        entry.grid(row=0, column=1, padx=12, pady=(14, 6))
        entry.focus()

        def confirm():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("No name", "Enter a mod name.", parent=dialog)
                return
            mod_path = os.path.join(MODS_SOURCE, name)
            if os.path.exists(mod_path):
                messagebox.showwarning("Already exists", f"{name} already exists in P:\\", parent=dialog)
                return
            dialog.destroy()
            self._create_mod(name)

        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=(4, 12))
        ttk.Button(btn_frame, text="Create", command=confirm).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=6)
        entry.bind("<Return>", lambda e: confirm())

    def _create_mod(self, name):
        mod_path = os.path.join(MODS_SOURCE, name)
        try:
            os.makedirs(os.path.join(mod_path, "data"))
            os.makedirs(os.path.join(mod_path, "scripts", "3_Game"))
            os.makedirs(os.path.join(mod_path, "scripts", "4_World"))
            os.makedirs(os.path.join(mod_path, "scripts", "5_Mission"))

            with open(r"P:\zzzzNewconfig.cpp", "r", encoding="utf-8") as f:
                template = f.read()

            config = template
            # Replace requiredAddons placeholder first (pure * with no TF_ prefix)
            config = re.sub(r'"\*+"', '"DayZGame"', config)
            # Replace all TF_** patterns (class names, dir, files[] paths, etc.)
            config = re.sub(r'TF_\*+', name, config)

            config_path = os.path.join(mod_path, "config.cpp")
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(config)

            self._log(f"Created mod: {name}", "ok")
            self._log(f"  P:\\{name}\\config.cpp", "inf")
            self._log(f"  P:\\{name}\\data\\", "inf")
            self._log(f"  P:\\{name}\\scripts\\3_Game\\", "inf")
            self._log(f"  P:\\{name}\\scripts\\4_World\\", "inf")
            self._log(f"  P:\\{name}\\scripts\\5_Mission\\", "inf")

            # Refresh mod list and select new mod
            self._populate_mods()
            if name in self._all_mods:
                idx = self._all_mods.index(name)
                self.mod_listbox.selection_clear(0, "end")
                self.mod_listbox.selection_set(idx)
                self.mod_listbox.see(idx)
                self.mod_var.set(name)

        except Exception as e:
            self._log(f"Failed to create mod: {e}", "err")

    # ── Local Server Tab ──────────────────────────────────────────────────────
    def _build_server_tab(self):
        import json
        f = self.tab_server
        pad = {"padx": 12, "pady": 4}

        self._server_proc = None
        self._log_after   = None

        ttk.Label(f, text="Local Server Manager", style="Header.TLabel").grid(row=0, column=0, columnspan=3, pady=(14, 4), padx=12, sticky="w")
        ttk.Separator(f, orient="horizontal").grid(row=1, column=0, columnspan=3, sticky="ew", padx=12)

        # Start / Stop buttons
        btn_frame = ttk.Frame(f)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=8)
        self.srv_start_btn = ttk.Button(btn_frame, text="Start Server", command=self._start_server)
        self.srv_start_btn.pack(side="left", padx=6)
        self.srv_stop_btn  = ttk.Button(btn_frame, text="Stop Server",  command=self._stop_server, state="disabled")
        self.srv_stop_btn.pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Start Settings", command=self._edit_params_dialog).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Server Config", command=self._edit_server_cfg_dialog).pack(side="left", padx=6)
        self.srv_status_lbl = ttk.Label(btn_frame, text="● Stopped", foreground="#f44747", background="#1e1e1e", font=("Segoe UI", 10, "bold"))
        self.srv_status_lbl.pack(side="left", padx=12)

        ttk.Separator(f, orient="horizontal").grid(row=3, column=0, columnspan=3, sticky="ew", padx=12, pady=4)

        # Mod list (left) + log viewer (right)
        mod_hdr = ttk.Frame(f)
        mod_hdr.grid(row=4, column=0, sticky="w", padx=12)
        ttk.Label(mod_hdr, text="Mods", style="Header.TLabel").pack(side="left")
        ttk.Button(mod_hdr, text="↻", width=3, command=self._load_server_mods).pack(side="left", padx=(8, 0))
        ttk.Label(f, text="Log Viewer", style="Header.TLabel").grid(row=4, column=1, columnspan=2, sticky="w", padx=12)

        # Mod checkboxes
        mod_outer = ttk.Frame(f)
        mod_outer.grid(row=5, column=0, sticky="nsw", padx=12, pady=4)
        canvas_frame = ttk.Frame(mod_outer)
        canvas_frame.pack(side="top", fill="both")
        self._mod_canvas = tk.Canvas(canvas_frame, width=220, height=300, bg="#1e1e1e", highlightthickness=0)
        mod_canvas = self._mod_canvas
        mod_scroll = ttk.Scrollbar(canvas_frame, orient="vertical", command=mod_canvas.yview)
        mod_canvas.configure(yscrollcommand=mod_scroll.set)
        mod_canvas.pack(side="left", fill="both")
        mod_scroll.pack(side="left", fill="y")
        self.mod_check_frame = ttk.Frame(mod_canvas)
        mod_canvas.create_window((0, 0), window=self.mod_check_frame, anchor="nw")
        self.mod_check_frame.bind("<Configure>", lambda e: mod_canvas.configure(scrollregion=mod_canvas.bbox("all")))
        mod_canvas.bind("<MouseWheel>", lambda e: mod_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        self.mod_check_frame.bind("<MouseWheel>", lambda e: mod_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._mod_check_vars = {}
        self._srv_search_var = tk.StringVar()
        self._srv_search_var.trace_add("write", self._filter_server_mods)
        srv_search = tk.Entry(mod_outer, textvariable=self._srv_search_var, width=28,
                              bg="#3a3a3a", fg="#888888", insertbackground="#d4d4d4",
                              relief="flat", font=("Segoe UI", 9))
        srv_search.insert(0, "Search mods...")
        srv_search.pack(side="top", fill="x", pady=(0, 4))

        def _on_focus_in(e):
            if srv_search.get() == "Search mods...":
                srv_search.delete(0, "end")
                srv_search.configure(fg="#d4d4d4")
        def _on_focus_out(e):
            if not srv_search.get():
                srv_search.insert(0, "Search mods...")
                srv_search.configure(fg="#888888")
        srv_search.bind("<FocusIn>",  _on_focus_in)
        srv_search.bind("<FocusOut>", _on_focus_out)
        self._load_server_mods()

        # Log viewer
        log_frame = ttk.Frame(f)
        log_frame.grid(row=5, column=1, columnspan=2, sticky="nsew", padx=(0, 12), pady=4)

        log_pick_frame = ttk.Frame(log_frame)
        log_pick_frame.pack(fill="x")
        ttk.Label(log_pick_frame, text="Log:").pack(side="left", padx=(0, 6))
        self.log_type_var = tk.StringVar(value="RPT")
        log_combo = ttk.Combobox(log_pick_frame, textvariable=self.log_type_var,
                                  values=["RPT", "Script", "LBmaster", "ADM", "Crash"], width=12, state="readonly")
        log_combo.pack(side="left")
        log_combo.bind("<<ComboboxSelected>>", lambda e: self._load_log())
        ttk.Button(log_pick_frame, text="Refresh", command=self._load_log).pack(side="left", padx=8)

        self.srv_log = scrolledtext.ScrolledText(log_frame, width=52, height=22, bg="#111111", fg="#d4d4d4",
                                                  font=("Consolas", 8), state="disabled", relief="flat")
        self.srv_log.pack(fill="both", expand=True, pady=(4, 0))

        f.columnconfigure(1, weight=1)

    def _load_server_mods(self):
        import json
        try:
            all_mods = sorted([
                d for d in os.listdir(self.server_dir)
                if d.startswith("@") and os.path.isdir(os.path.join(self.server_dir, d))
            ], key=lambda x: x.lstrip("@").lower())
        except FileNotFoundError:
            all_mods = []

        saved = {}
        if os.path.exists(self._selections_file):
            try:
                with open(self._selections_file, "r") as f:
                    saved = json.load(f)
            except Exception:
                pass

        # Get currently active mods from start.bat
        active = set()
        try:
            with open(self.start_bat, "r", encoding="utf-8") as f:
                content = f.read()
            match = re.search(r'"-mod=([^"]*)"', content)
            if match:
                active = set(m.strip() for m in match.group(1).split(";") if m.strip())
        except Exception:
            pass

        self._all_server_mods = all_mods
        for widget in self.mod_check_frame.winfo_children():
            widget.destroy()
        self._mod_check_vars = {}

        for mod in all_mods:
            var = tk.BooleanVar(value=saved.get(mod, mod in active))
            self._mod_check_vars[mod] = var

        self._render_server_mod_checkboxes(all_mods)

    def _render_server_mod_checkboxes(self, mods):
        for widget in self.mod_check_frame.winfo_children():
            widget.destroy()
        for mod in mods:
            var = self._mod_check_vars[mod]
            cb = ttk.Checkbutton(self.mod_check_frame, text=mod, variable=var,
                                 command=self._save_mod_selections)
            cb.pack(anchor="w", padx=4)
            cb.bind("<MouseWheel>", lambda e: self._mod_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def _filter_server_mods(self, *args):
        if not hasattr(self, "_all_server_mods"):
            return
        typed = self._srv_search_var.get().lower()
        if not typed or typed == "search mods...":
            filtered = self._all_server_mods
        else:
            filtered = [m for m in self._all_server_mods if typed in m.lower()]
        self._render_server_mod_checkboxes(filtered)

    def _save_mod_selections(self):
        import json
        data = {mod: var.get() for mod, var in self._mod_check_vars.items()}
        with open(self._selections_file, "w") as f:
            json.dump(data, f, indent=2)

    def _start_server(self):
        if self._server_proc and self._server_proc.poll() is None:
            return

        # Build mod list from checkboxes
        selected = [mod for mod, var in self._mod_check_vars.items() if var.get()]
        mod_str = ";".join(selected)

        # Patch start.bat
        try:
            with open(self.start_bat, "r", encoding="utf-8") as f:
                content = f.read()
            new_content = re.sub(r'"-mod=[^"]*"', f'"-mod={mod_str}"', content)
            with open(self.start_bat, "w", encoding="utf-8") as f:
                f.write(new_content)
        except Exception as e:
            messagebox.showerror("Error", f"Could not patch start.bat: {e}")
            return

        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 6  # SW_MINIMIZE

        self._server_proc = subprocess.Popen(
            [os.path.join(self.server_dir, "DayZServer_x64.exe"),
             "-config=serverDZ.cfg", "-port=2302", "-cpuCount=2",
             "-dologs", "-adminlog", "-netlog", "-freezecheck",
             "-profiles=Profiles", f"-mod={mod_str}"],
            cwd=self.server_dir,
            stdin=subprocess.DEVNULL,
            startupinfo=si
        )
        self.srv_start_btn.configure(state="disabled")
        self.srv_stop_btn.configure(state="normal")
        self.srv_status_lbl.configure(text="● Running", foreground="#4ec94e")

        self.srv_log.configure(state="normal")
        self.srv_log.delete("1.0", "end")
        self.srv_log.configure(state="disabled")

        self._rpt_tail_active = True
        threading.Thread(target=self._tail_rpt_live, daemon=True).start()
        self._poll_server()

    def _tail_rpt_live(self):
        import time, glob
        profiles = os.path.join(self.server_dir, "Profiles")

        # Wait up to 20s for a new RPT to appear
        rpt_path = None
        before = set(glob.glob(os.path.join(profiles, "*.RPT")))
        for _ in range(40):
            time.sleep(0.5)
            after = set(glob.glob(os.path.join(profiles, "*.RPT")))
            new = after - before
            if new:
                rpt_path = sorted(new, key=os.path.getmtime)[-1]
                break

        if not rpt_path:
            # fallback to most recent
            all_rpts = sorted(glob.glob(os.path.join(profiles, "*.RPT")), key=os.path.getmtime)
            if all_rpts:
                rpt_path = all_rpts[-1]

        if not rpt_path:
            return

        with open(rpt_path, "r", encoding="utf-8", errors="replace") as f:
            while self._rpt_tail_active:
                line = f.readline()
                if line:
                    self.srv_log.configure(state="normal")
                    self.srv_log.insert("end", line)
                    self.srv_log.see("end")
                    self.srv_log.configure(state="disabled")
                else:
                    time.sleep(0.2)

    def _poll_server(self):
        if self._server_proc and self._server_proc.poll() is not None:
            self._rpt_tail_active = False
            code = self._server_proc.returncode
            self.srv_start_btn.configure(state="normal")
            self.srv_stop_btn.configure(state="disabled")
            if code == 0:
                self.srv_status_lbl.configure(text="● Stopped", foreground="#f44747")
            else:
                self.srv_status_lbl.configure(text=f"● Crashed (exit {code})", foreground="#f44747")
                self.srv_log.configure(state="normal")
                self.srv_log.insert("end", f"\n[SERVER EXITED WITH CODE {code}]\n")
                self.srv_log.see("end")
                self.srv_log.configure(state="disabled")
        else:
            self.after(3000, self._poll_server)

    def _stop_server(self):
        self._rpt_tail_active = False
        if self._server_proc:
            self._server_proc.terminate()
            try:
                self._server_proc.wait(timeout=10)
            except Exception:
                self._server_proc.kill()
        subprocess.run(["taskkill", "/im", "DayZServer_x64.exe", "/F"], capture_output=True)
        self.srv_start_btn.configure(state="normal")
        self.srv_stop_btn.configure(state="disabled")
        self.srv_status_lbl.configure(text="● Stopped", foreground="#f44747")

    def _ensure_start_bat(self):
        if not os.path.exists(self.start_bat):
            self._generate_start_bat()

    def _generate_start_bat(self, name=None, port="2302", config="serverDZ.cfg", cpu="2"):
        if not name:
            name = SERVERS[self.mode]["bat_name"]
        content = f"""@echo off
:start
::Server name (This is just for the bat file)
set serverName={name}
::Server files location
set serverLocation="{self.server_dir}"
::Server Port
set serverPort={port}
::Server config
set serverConfig={config}
::Logical CPU cores to use (Equal or less than available)
set serverCPU={cpu}
::Sets title for terminal (DONT edit)
title %serverName% batch
::DayZServer location (DONT edit)
cd "%serverLocation%"
echo (%time%) %serverName% started.
::Launch parameters (edit end: -config=|-port=|-profiles=|-doLogs|-adminLog|-netLog|-freezeCheck|-filePatching|-BEpath=|-cpuCount=)
start "DayZ Server" /min "DayZServer_x64.exe" -config=%serverConfig% -port=%serverPort% -cpuCount=%serverCPU% -dologs -adminlog -netlog -freezecheck "-profiles=Profiles" "-mod="
::Time in seconds before kill server process (14400 = 4 hours)
timeout 14390
taskkill /im DayZServer_x64.exe /F
::Time in seconds to wait before..
timeout 10
::Go back to the top and repeat the whole cycle again
goto start
"""
        with open(self.start_bat, "w", encoding="utf-8") as f:
            f.write(content)

    def _edit_params_dialog(self):
        # Read current values from start.bat
        params = {"serverName": "", "serverPort": "", "serverConfig": "", "serverCPU": ""}
        try:
            with open(self.start_bat, "r", encoding="utf-8") as f:
                for line in f:
                    for key in params:
                        m = re.match(rf"set {key}=(.+)", line.strip())
                        if m:
                            params[key] = m.group(1).strip()
        except Exception as e:
            messagebox.showerror("Error", f"Could not read start.bat: {e}")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Server Parameters")
        dialog.configure(bg="#1e1e1e")
        dialog.resizable(False, False)
        dialog.grab_set()

        labels = {"serverName": "Server Name", "serverPort": "Port", "serverConfig": "Config file", "serverCPU": "CPU Cores"}
        vars_ = {}
        for i, (key, label) in enumerate(labels.items()):
            ttk.Label(dialog, text=label).grid(row=i, column=0, padx=12, pady=6, sticky="w")
            var = tk.StringVar(value=params[key])
            vars_[key] = var
            tk.Entry(dialog, textvariable=var, width=28,
                     bg="#3a3a3a", fg="#d4d4d4", insertbackground="#d4d4d4",
                     relief="flat", font=("Segoe UI", 10)).grid(row=i, column=1, padx=12, pady=6)

        def save():
            try:
                with open(self.start_bat, "r", encoding="utf-8") as f:
                    content = f.read()
                for key, var in vars_.items():
                    content = re.sub(rf"(set {key}=).+", rf"\g<1>{var.get().strip()}", content)
                with open(self.start_bat, "w", encoding="utf-8") as f:
                    f.write(content)
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Could not save: {e}", parent=dialog)

        def regenerate():
            if messagebox.askyesno("Regenerate", "This will replace start.bat with a clean default. Current mod selections will be cleared from it. Continue?", parent=dialog):
                self._generate_start_bat(
                    name=vars_["serverName"].get().strip(),
                    port=vars_["serverPort"].get().strip(),
                    config=vars_["serverConfig"].get().strip(),
                    cpu=vars_["serverCPU"].get().strip()
                )
                dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=len(labels), column=0, columnspan=2, pady=(4, 12))
        ttk.Button(btn_frame, text="Save", command=save).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Regenerate start.bat", command=regenerate).pack(side="left", padx=6)

    def _edit_server_cfg_dialog(self):
        cfg_path = os.path.join(self.server_dir, "serverDZ.cfg")
        if not os.path.exists(cfg_path):
            messagebox.showerror("Error", "serverDZ.cfg not found.")
            return

        with open(cfg_path, "r", encoding="utf-8") as f:
            raw = f.read()

        # Parse key = value lines (skip class blocks and comments)
        parsed = []
        for line in raw.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("//") or stripped.startswith("class") or stripped.startswith("{") or stripped.startswith("}"):
                continue
            m = re.match(r'^(\w+)\s*=\s*(.+?)(?:\s*;)?(?:\s*//.*)?$', stripped)
            if m:
                parsed.append([m.group(1), m.group(2).strip()])

        dialog = tk.Toplevel(self)
        dialog.title("serverDZ.cfg Editor")
        dialog.configure(bg="#1e1e1e")
        dialog.resizable(False, True)
        dialog.grab_set()

        # Scrollable rows
        container = ttk.Frame(dialog)
        container.pack(fill="both", expand=True, padx=12, pady=(12, 4))

        canvas = tk.Canvas(container, bg="#1e1e1e", highlightthickness=0, width=500, height=400)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        rows_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=rows_frame, anchor="nw")
        rows_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        row_data = []  # list of (key_var, val_var, frame)

        def add_row(key="", val=""):
            rf = ttk.Frame(rows_frame)
            rf.pack(fill="x", pady=2)
            k = tk.StringVar(value=key)
            v = tk.StringVar(value=val)
            tk.Entry(rf, textvariable=k, width=22, bg="#3a3a3a", fg="#d4d4d4",
                     insertbackground="#d4d4d4", relief="flat", font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
            tk.Entry(rf, textvariable=v, width=22, bg="#3a3a3a", fg="#d4d4d4",
                     insertbackground="#d4d4d4", relief="flat", font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
            entry = (k, v, rf)
            row_data.append(entry)
            def do_remove(r=rf):
                idx = next((i for i, x in enumerate(row_data) if x[2] == r), None)
                if idx is not None:
                    row_data.pop(idx)
                r.destroy()
            ttk.Button(rf, text="✕", width=3, command=do_remove).pack(side="left")

        ttk.Label(rows_frame, text="Key", width=22, anchor="w").pack(side="top") if False else None
        hdr = ttk.Frame(rows_frame)
        hdr.pack(fill="x", pady=(0, 4))
        ttk.Label(hdr, text="Key", width=24, anchor="w").pack(side="left")
        ttk.Label(hdr, text="Value", width=24, anchor="w").pack(side="left")

        for key, val in parsed:
            add_row(key, val)

        # Bottom buttons
        bot = ttk.Frame(dialog)
        bot.pack(fill="x", padx=12, pady=(4, 12))
        ttk.Button(bot, text="+ Add", command=lambda: add_row()).pack(side="left", padx=(0, 6))

        def save():
            # Rebuild file preserving class Missions block
            lines = []
            for k_var, v_var, _ in row_data:
                k = k_var.get().strip()
                v = v_var.get().strip()
                if k:
                    lines.append(f'{k} = {v};')

            # Append the Missions class block from original
            missions_match = re.search(r'(class Missions.*)', raw, re.DOTALL)
            missions_block = "\n" + missions_match.group(1) if missions_match else ""

            with open(cfg_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + missions_block + "\n")
            dialog.destroy()

        ttk.Button(bot, text="Save", command=save).pack(side="left", padx=(0, 6))
        ttk.Button(bot, text="Cancel", command=dialog.destroy).pack(side="left")

    def _load_log(self):
        log_type = self.log_type_var.get()
        profiles = os.path.join(self.server_dir, "Profiles")
        target = None

        try:
            all_files = os.listdir(profiles)
            if log_type == "RPT":
                candidates = sorted([f for f in all_files if f.endswith(".RPT")])
            elif log_type == "Script":
                candidates = sorted([f for f in all_files if f.startswith("script_") and f.endswith(".log")])
            elif log_type == "LBmaster":
                candidates = sorted([f for f in all_files if f.startswith("LBmaster_") and f.endswith(".log")])
            elif log_type == "ADM":
                candidates = sorted([f for f in all_files if f.endswith(".ADM")])
            elif log_type == "Crash":
                candidates = sorted([f for f in all_files if "crash" in f.lower() and f.endswith(".log")])
                if not candidates:
                    self.srv_log.configure(state="normal")
                    self.srv_log.delete("1.0", "end")
                    self.srv_log.insert("end", "No crash log found.")
                    self.srv_log.configure(state="disabled")
                    return
            else:
                candidates = []

            if candidates:
                target = os.path.join(profiles, candidates[-1])
        except Exception as e:
            return

        self.srv_log.configure(state="normal")
        self.srv_log.delete("1.0", "end")
        if target and os.path.exists(target):
            try:
                with open(target, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                self.srv_log.insert("end", content)
                self.srv_log.see("end")
            except Exception as e:
                self.srv_log.insert("end", f"Could not read log: {e}")
        else:
            self.srv_log.insert("end", "No log file found.")
        self.srv_log.configure(state="disabled")


if __name__ == "__main__":
    app = PBOTool()
    app.mainloop()
