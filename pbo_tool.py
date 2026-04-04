import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
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

TF_SHOP         = r"P:\TF_Shop"
IMAGE_TO_PAA    = r"C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\ImageToPAA\ImageToPAA.exe"


# ── Main App ─────────────────────────────────────────────────────────────────
class PBOTool(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("brnz Server Tools")
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

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_pbo    = ttk.Frame(notebook)
        self.tab_shop   = ttk.Frame(notebook)
        self.tab_server = ttk.Frame(notebook)
        notebook.add(self.tab_pbo,    text="  PBO Builder  ")
        notebook.add(self.tab_shop,   text="  Flag / Mural  ")
        notebook.add(self.tab_server, text="  Local Server  ")

        self._build_pbo_tab()
        self._build_shop_tab()
        self._build_server_tab()
        self._populate_mods()
        self._ensure_start_bat()

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
        for text, val in [("Local server (test)", "local"), ("Staging only", "staging_only"), ("Staging + Modpack", "staging"), ("Modpack only", "modpack")]:
            ttk.Radiobutton(dest_frame, text=text, variable=self.dest_var, value=val, command=self._on_dest_change).pack(anchor="w")

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
        ttk.Label(f, text="Name (no spaces)").grid(row=3, column=0, sticky="w", **pad)
        self.shop_name_var = tk.StringVar()
        tk.Entry(f, textvariable=self.shop_name_var, width=30,
                 bg="#3a3a3a", fg="#d4d4d4", insertbackground="#d4d4d4",
                 relief="flat", font=("Segoe UI", 10)).grid(row=3, column=1, sticky="w", **pad)

        # Display name
        ttk.Label(f, text="Display name").grid(row=4, column=0, sticky="w", **pad)
        self.shop_display_var = tk.StringVar()
        tk.Entry(f, textvariable=self.shop_display_var, width=30,
                 bg="#3a3a3a", fg="#d4d4d4", insertbackground="#d4d4d4",
                 relief="flat", font=("Segoe UI", 10)).grid(row=4, column=1, sticky="w", **pad)

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

    # ── Local Server Tab ──────────────────────────────────────────────────────
    def _build_server_tab(self):
        import json
        f = self.tab_server
        pad = {"padx": 12, "pady": 4}

        self._server_proc = None
        self._log_after   = None
        self._selections_file = os.path.join(os.path.dirname(__file__), "server_mod_selections.json")

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
                                  values=["RPT", "Script", "LBmaster", "ADM"], width=12, state="readonly")
        log_combo.pack(side="left")
        log_combo.bind("<<ComboboxSelected>>", lambda e: self._load_log())
        ttk.Button(log_pick_frame, text="Refresh", command=self._load_log).pack(side="left", padx=8)

        self.srv_log = scrolledtext.ScrolledText(log_frame, width=52, height=22, bg="#111111", fg="#d4d4d4",
                                                  font=("Consolas", 8), state="disabled", relief="flat")
        self.srv_log.pack(fill="both", expand=True, pady=(4, 0))

        f.columnconfigure(1, weight=1)

    def _load_server_mods(self):
        import json
        all_mods = sorted([
            d for d in os.listdir(LOCAL_SERVER)
            if d.startswith("@") and os.path.isdir(os.path.join(LOCAL_SERVER, d))
        ], key=lambda x: x.lstrip("@").lower())

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
            with open(START_BAT, "r", encoding="utf-8") as f:
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
            with open(START_BAT, "r", encoding="utf-8") as f:
                content = f.read()
            new_content = re.sub(r'"-mod=[^"]*"', f'"-mod={mod_str}"', content)
            with open(START_BAT, "w", encoding="utf-8") as f:
                f.write(new_content)
        except Exception as e:
            messagebox.showerror("Error", f"Could not patch start.bat: {e}")
            return

        self._server_proc = subprocess.Popen(
            [os.path.join(LOCAL_SERVER, "DayZServer_x64.exe"),
             "-config=serverDZ.cfg", "-port=2302", "-cpuCount=2",
             "-dologs", "-adminlog", "-netlog", "-freezecheck",
             "-profiles=Profiles", f"-mod={mod_str}"],
            cwd=LOCAL_SERVER,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        self.srv_start_btn.configure(state="disabled")
        self.srv_stop_btn.configure(state="normal")
        self.srv_status_lbl.configure(text="● Running", foreground="#4ec94e")

        self.srv_log.configure(state="normal")
        self.srv_log.delete("1.0", "end")
        self.srv_log.configure(state="disabled")

        threading.Thread(target=self._stream_server_output, daemon=True).start()
        self._poll_server()

    def _stream_server_output(self):
        try:
            for line in iter(self._server_proc.stdout.readline, b""):
                decoded = line.decode("utf-8", errors="replace").rstrip()
                if decoded:
                    self.srv_log.configure(state="normal")
                    self.srv_log.insert("end", decoded + "\n")
                    self.srv_log.see("end")
                    self.srv_log.configure(state="disabled")
        except Exception:
            pass

    def _poll_server(self):
        if self._server_proc and self._server_proc.poll() is not None:
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
        if not os.path.exists(START_BAT):
            self._generate_start_bat()

    def _generate_start_bat(self, name="brnz local", port="2302", config="serverDZ.cfg", cpu="2"):
        content = f"""@echo off
:start
::Server name (This is just for the bat file)
set serverName={name}
::Server files location
set serverLocation="C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZServer"
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
        with open(START_BAT, "w", encoding="utf-8") as f:
            f.write(content)

    def _edit_params_dialog(self):
        # Read current values from start.bat
        params = {"serverName": "", "serverPort": "", "serverConfig": "", "serverCPU": ""}
        try:
            with open(START_BAT, "r", encoding="utf-8") as f:
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
                with open(START_BAT, "r", encoding="utf-8") as f:
                    content = f.read()
                for key, var in vars_.items():
                    content = re.sub(rf"(set {key}=).+", rf"\g<1>{var.get().strip()}", content)
                with open(START_BAT, "w", encoding="utf-8") as f:
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
        cfg_path = os.path.join(LOCAL_SERVER, "serverDZ.cfg")
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
        profiles = os.path.join(LOCAL_SERVER, "Profiles")
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
