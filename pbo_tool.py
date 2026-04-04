import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
import shutil
import re
import threading

# ── Paths ────────────────────────────────────────────────────────────────────
ADDON_BUILDER   = r"C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\AddonBuilder.exe"
DSSIGNFILE      = r"C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\DsUtils\DSSignFile.exe"
MODS_SOURCE     = r"P:\\"
LOCAL_SERVER    = r"C:\Program Files (x86)\Steam\steamapps\common\DayZServer"
START_BAT       = os.path.join(LOCAL_SERVER, "start.bat")
STAGING_BASE    = r"C:\Users\b_mal\Desktop\Core Stuff"
MODPACK_BASE    = r"D:\MODS"

BIKEYS = {
    "TheFactory":     r"D:\MODS\@TheFactoryCore\Keys\TheFactory.biprivatekey",
    "TheFactoryTest": r"D:\MODS\@TheFactoryCoreTest\Keys\TheFactoryTest.biprivatekey",
}

MODPACKS = {
    "Core":     ("TheFactoryCore",     "TheFactoryCoreTest",     "core"),
    "Gear":     ("TheFactoryGear",     "TheFactoryGearTest",     "gear"),
    "Weapons":  ("TheFactoryWeapons",  "TheFactoryWeaponsTest",  "weapons"),
    "Vehicles": ("TheFactoryVehicles", "TheFactoryVehiclesTest", "vehicles"),
}


# ── Main App ─────────────────────────────────────────────────────────────────
class PBOTool(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("brnz PBO Project")
        self.resizable(False, False)
        self.configure(bg="#1e1e1e")

        style = ttk.Style(self)
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

        self._build_ui()
        self._populate_mods()

    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}

        # Header
        ttk.Label(self, text="brnz PBO Project", style="Header.TLabel").grid(row=0, column=0, columnspan=2, pady=(14, 4), padx=12, sticky="w")
        ttk.Separator(self, orient="horizontal").grid(row=1, column=0, columnspan=2, sticky="ew", padx=12)

        # Mod selector with search
        ttk.Label(self, text="Mod (P:\\)").grid(row=2, column=0, sticky="nw", **pad)
        mod_frame = ttk.Frame(self)
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
        ttk.Label(self, text="Destination").grid(row=3, column=0, sticky="nw", **pad)
        dest_frame = ttk.Frame(self)
        dest_frame.grid(row=3, column=1, sticky="w", **pad)

        self.dest_var = tk.StringVar(value="local")
        for text, val in [("Local server (test)", "local"), ("Staging only", "staging_only"), ("Staging + Modpack", "staging"), ("Modpack only", "modpack")]:
            ttk.Radiobutton(dest_frame, text=text, variable=self.dest_var, value=val, command=self._on_dest_change).pack(anchor="w")

        # Pack selector (staging/modpack)
        self.pack_frame = ttk.Frame(self)
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
        self.sign_frame = ttk.Frame(self)
        self.sign_frame.grid(row=5, column=0, columnspan=2, sticky="w", padx=12, pady=2)
        self.sign_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.sign_frame, text="Sign PBO after packing", variable=self.sign_var).pack(anchor="w")
        self.sign_frame.grid_remove()

        ttk.Separator(self, orient="horizontal").grid(row=6, column=0, columnspan=2, sticky="ew", padx=12, pady=6)

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=4)
        self.build_btn = ttk.Button(btn_frame, text="Build", command=self._run)
        self.build_btn.pack(side="left", padx=6)
        ttk.Button(btn_frame, text="New Mod", command=self._new_mod_dialog).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Open Publisher", command=self._open_publisher).pack(side="left", padx=6)

        # Log
        self.log = scrolledtext.ScrolledText(self, width=62, height=14, bg="#111111", fg="#d4d4d4",
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
        addons_dir = os.path.join(LOCAL_SERVER, mod_folder, "addons")
        os.makedirs(addons_dir, exist_ok=True)
        self._log(f"Packing {mod} → local server...", "inf")

        ok = self._addon_builder(src, addons_dir)
        if not ok:
            return

        self._log("Patching start.bat...", "inf")
        self._patch_startbat(mod_folder)
        self._log("Done. Restart your local server to load the mod.", "ok")

    def _patch_startbat(self, mod_folder):
        with open(START_BAT, "r", encoding="utf-8") as f:
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

        with open(START_BAT, "w", encoding="utf-8") as f:
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
            for line in result.stdout.splitlines():
                if any(k in line for k in ["INFO", "ERROR", "WARN"]):
                    tag = "err" if "ERROR" in line else ("ok" if "Successful" in line else "")
                    self._log(line.strip(), tag)
            if "Build Successful" in result.stdout:
                self._log("Pack successful.", "ok")
                return True
            else:
                self._log("Pack FAILED — check log above.", "err")
                return False
        except subprocess.TimeoutExpired:
            self._log("AddonBuilder timed out.", "err")
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


    # ── Publisher ─────────────────────────────────────────────────────────────
    def _open_publisher(self):
        try:
            subprocess.Popen([r"C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\Publisher\Publisher.exe"])
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


if __name__ == "__main__":
    app = PBOTool()
    app.mainloop()
