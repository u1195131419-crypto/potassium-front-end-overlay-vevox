#!/usr/bin/env python3
"""
Vevox — Professional Executor Interface & HTTP Bridge
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import http.server
import json
import time
import os
import sys
import re
import queue
import datetime
import logging
import webbrowser
import subprocess
import urllib.request
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass, field, asdict

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


# ═══════════════════════════════════════════════════════════════════════════════
#  PYINSTALLER COMPATIBILITY
# ═══════════════════════════════════════════════════════════════════════════════

def resource_path(relative_path: str) -> Path:
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / relative_path
    try:
        return Path(__file__).parent / relative_path
    except NameError:
        return Path(os.getcwd()) / relative_path


try:
    ICON_PATH = str(resource_path("icon.ico"))
    if not Path(ICON_PATH).exists():
        ICON_PATH = None
except Exception:
    ICON_PATH = None


# ═══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

APP_NAME = "Vevox"
APP_VERSION = "5.2.0"
CONFIG_DIR = Path.home() / ".vevox"
CONFIG_FILE = CONFIG_DIR / "settings.json"
SCRIPTS_DIR = CONFIG_DIR / "scripts"
HISTORY_FILE = CONFIG_DIR / "history.json"
LOG_FILE = CONFIG_DIR / "app.log"
TABS_FILE = CONFIG_DIR / "tabs.json"
CUSTOM_HUB_FILE = CONFIG_DIR / "custom_hub.json"
REMOTE_CACHE_FILE = CONFIG_DIR / "remote_links.json"

BRIDGE_HOST = "127.0.0.1"
BRIDGE_PORT = 8000
BRIDGE_URL = f"http://{BRIDGE_HOST}:{BRIDGE_PORT}"

# ─── REPLACE WITH YOUR GIST RAW URL ──────────────────────────────────────────
REMOTE_LINKS_URL = "https://gist.githubusercontent.com/u1195131419-crypto/a7e4dfad1ad7cda06f1d2d39cb5f2aa5/raw/vevox_links.json"
# ──────────────────────────────────────────────────────────────────────────────

REMOTE_LINKS_TTL = 300
REMOTE_LINKS_TIMEOUT = 5

ROBLOX_PROCESSES = [
    "RobloxPlayerBeta.exe", "RobloxPlayerBeta",
    "Windows10Universal.exe", "RobloxPlayer",
]

POTASSIUM_HINTS = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Potassium" / "autoexec",
    Path(os.environ.get("APPDATA", "")) / "Potassium" / "autoexec",
    Path("C:/Potassium/autoexec"),
    Path.home() / "Potassium" / "autoexec",
]

MAX_HISTORY = 500
MAX_CONSOLE = 2000
MAX_TABS = 12

BRIDGE_LISTENER_VERSION = "5.0"
INSTANCE_TIMEOUT = 15

TAB_BAR_HEIGHT = 40
TAB_WIDTH_MIN = 100
TAB_WIDTH_MAX = 180

BRIDGE_LISTENER_SOURCE = '''--[[
    Vevox Bridge Listener v5.0 (auto-written by Vevox app)
    Multi-instance capable
]]

local BRIDGE = "http://127.0.0.1:{port}"
local POLL = 0.5
local PING = 4
local FWD_CONSOLE = true

local INSTANCE_ID = tostring(math.random(100000, 999999)) .. "_" .. tostring(tick()):gsub("%.", "")

local httpReq = (syn and syn.request) or (http and http.request)
    or http_request or request or (fluxus and fluxus.request)
local HS = game:GetService("HttpService")
local SG = game:GetService("StarterGui")
local Plrs = game:GetService("Players")

local function notify(t, x, d)
    pcall(function()
        SG:SetCore("SendNotification", {{
            Title = t or "Vevox",
            Text = x or "",
            Duration = d or 3
        }})
    end)
end

local function post(ep, data)
    if not httpReq then return end
    data.instance_id = INSTANCE_ID
    task.spawn(function()
        pcall(function()
            httpReq({{
                Url = BRIDGE .. ep,
                Method = "POST",
                Headers = {{["Content-Type"] = "application/json"}},
                Body = HS:JSONEncode(data)
            }})
        end)
    end)
end

local function callback(s, m)
    post("/callback", {{
        status = s,
        message = tostring(m):sub(1, 200),
        timestamp = tick()
    }})
end

local function fwd(lvl, m)
    if not FWD_CONSOLE then return end
    post("/console", {{
        level = lvl,
        message = tostring(m):sub(1, 500),
        timestamp = tick()
    }})
end

local function gameInfo()
    pcall(function()
        local p = Plrs.LocalPlayer
        local n = "Unknown"
        pcall(function()
            n = game:GetService("MarketplaceService"):GetProductInfo(game.PlaceId).Name
        end)
        post("/game-info", {{
            placeId = game.PlaceId,
            gameId = game.GameId,
            placeName = n,
            player = p and p.Name or "?",
            displayName = p and p.DisplayName or "?",
        }})
    end)
end

if FWD_CONSOLE then
    local _p, _w = print, warn
    local function cat(...)
        local t = {{}}
        for i = 1, select("#", ...) do t[i] = tostring(select(i, ...)) end
        return table.concat(t, "\\t")
    end
    print = function(...) _p(...) fwd("print", cat(...)) end
    warn = function(...) _w(...) fwd("warn", cat(...)) end
end

notify("Vevox", "Bridge v5.0 connected (ID: " .. INSTANCE_ID:sub(1, 6) .. ")", 3)
task.delay(2, gameInfo)

task.spawn(function()
    while true do
        pcall(function() game:HttpGet(BRIDGE .. "/ping?id=" .. INSTANCE_ID) end)
        task.wait(PING)
    end
end)

task.spawn(function()
    while true do
        local ok, code = pcall(function()
            return game:HttpGet(BRIDGE .. "/?id=" .. INSTANCE_ID)
        end)
        if ok and code and code ~= "" then
            local fn, err = loadstring(code)
            if fn then
                task.spawn(function()
                    local s, e = pcall(fn)
                    if s then
                        notify("Vevox", "Executed!", 2)
                        callback("success", "OK")
                    else
                        local m = tostring(e):sub(1, 150)
                        warn("[Vevox] Runtime:", e)
                        notify("Vevox", m, 5)
                        callback("error", "Runtime: " .. m)
                    end
                end)
            else
                local m = tostring(err):sub(1, 150)
                warn("[Vevox] Compile:", err)
                notify("Vevox", m, 5)
                callback("error", "Compile: " .. m)
            end
        end
        task.wait(POLL)
    end
end)

task.spawn(function()
    while true do task.wait(30) gameInfo() end
end)
'''

for d in [CONFIG_DIR, SCRIPTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8")],
)
logger = logging.getLogger("Vevox")


# ═══════════════════════════════════════════════════════════════════════════════
#  THEMES
# ═══════════════════════════════════════════════════════════════════════════════

THEMES = {
    "Pure Black": {
        "BG0": "#000000", "BG1": "#0a0a0a", "BG2": "#111111",
        "BG3": "#181818", "BG4": "#1f1f1f", "BG5": "#262626",
        "BG6": "#2e2e2e", "BG7": "#353535",
        "BG_EDITOR": "#080808", "BG_TOPBAR": "#0a0a0a",
        "TAB_BAR": "#050505", "TAB_INACTIVE": "#1a1a1a", "TAB_ACTIVE": "#2b2b2b",
        "ACCENT": "#e8e8e8", "ACCENT_HOVER": "#ffffff",
        "ACCENT_DARK": "#3a3a3a", "ACCENT_TEXT": "#000000",
        "RED": "#e05555", "ORANGE": "#e8a04e", "YELLOW": "#e8d060",
        "PURPLE": "#a880d4", "GREEN_BRIGHT": "#00e070",
        "T1": "#f0f0f0", "T2": "#a0a0a0", "T3": "#808080", "T4": "#404040",
        "BORDER": "#222222", "SCROLL": "#333333", "SCROLL_H": "#4a4a4a",
        "SYN_KW": "#d0a0d0", "SYN_BI": "#e8b878", "SYN_GL": "#d88888",
        "SYN_ST": "#a8c8a8", "SYN_CM": "#585858", "SYN_NM": "#d8b878",
        "SYN_OP": "#b8b8b8", "SYN_FN": "#d8c898",
    },
    "Midnight": {
        "BG0": "#0d1117", "BG1": "#131a22", "BG2": "#161b22",
        "BG3": "#1c2128", "BG4": "#22272e", "BG5": "#2d333b",
        "BG6": "#373e47", "BG7": "#444c56",
        "BG_EDITOR": "#0d1117", "BG_TOPBAR": "#0a0e14",
        "TAB_BAR": "#0a0e14", "TAB_INACTIVE": "#1c2128", "TAB_ACTIVE": "#2d333b",
        "ACCENT": "#58a6ff", "ACCENT_HOVER": "#79b8ff",
        "ACCENT_DARK": "#1f3350", "ACCENT_TEXT": "#0d1117",
        "RED": "#f85149", "ORANGE": "#e3b341", "YELLOW": "#f0c34e",
        "PURPLE": "#bc8cff", "GREEN_BRIGHT": "#3fb950",
        "T1": "#e6edf3", "T2": "#8b949e", "T3": "#8b949e", "T4": "#484f58",
        "BORDER": "#30363d", "SCROLL": "#30363d", "SCROLL_H": "#484f58",
        "SYN_KW": "#ff7b72", "SYN_BI": "#d2a8ff", "SYN_GL": "#79c0ff",
        "SYN_ST": "#a5d6ff", "SYN_CM": "#8b949e", "SYN_NM": "#79c0ff",
        "SYN_OP": "#ff7b72", "SYN_FN": "#d2a8ff",
    },
    "Dracula": {
        "BG0": "#1a1c24", "BG1": "#20222c", "BG2": "#282a36",
        "BG3": "#2f3241", "BG4": "#363948", "BG5": "#44475a",
        "BG6": "#4c5069", "BG7": "#565973",
        "BG_EDITOR": "#282a36", "BG_TOPBAR": "#1a1c24",
        "TAB_BAR": "#1a1c24", "TAB_INACTIVE": "#2f3241", "TAB_ACTIVE": "#44475a",
        "ACCENT": "#bd93f9", "ACCENT_HOVER": "#d0aaff",
        "ACCENT_DARK": "#44365a", "ACCENT_TEXT": "#282a36",
        "RED": "#ff5555", "ORANGE": "#ffb86c", "YELLOW": "#f1fa8c",
        "PURPLE": "#bd93f9", "GREEN_BRIGHT": "#50fa7b",
        "T1": "#f8f8f2", "T2": "#a4a7b8", "T3": "#a4a7b8", "T4": "#6272a4",
        "BORDER": "#44475a", "SCROLL": "#44475a", "SCROLL_H": "#6272a4",
        "SYN_KW": "#ff79c6", "SYN_BI": "#8be9fd", "SYN_GL": "#ffb86c",
        "SYN_ST": "#f1fa8c", "SYN_CM": "#6272a4", "SYN_NM": "#bd93f9",
        "SYN_OP": "#ff79c6", "SYN_FN": "#50fa7b",
    },
    "Nord": {
        "BG0": "#2e3440", "BG1": "#333947", "BG2": "#3b4252",
        "BG3": "#434c5e", "BG4": "#4c566a", "BG5": "#5e6779",
        "BG6": "#6a7488", "BG7": "#758197",
        "BG_EDITOR": "#2e3440", "BG_TOPBAR": "#292e3a",
        "TAB_BAR": "#292e3a", "TAB_INACTIVE": "#434c5e", "TAB_ACTIVE": "#5e6779",
        "ACCENT": "#88c0d0", "ACCENT_HOVER": "#a3d4e0",
        "ACCENT_DARK": "#3d5560", "ACCENT_TEXT": "#2e3440",
        "RED": "#bf616a", "ORANGE": "#d08770", "YELLOW": "#ebcb8b",
        "PURPLE": "#b48ead", "GREEN_BRIGHT": "#a3be8c",
        "T1": "#eceff4", "T2": "#d8dee9", "T3": "#d8dee9", "T4": "#7a869e",
        "BORDER": "#434c5e", "SCROLL": "#4c566a", "SCROLL_H": "#5e6779",
        "SYN_KW": "#81a1c1", "SYN_BI": "#88c0d0", "SYN_GL": "#8fbcbb",
        "SYN_ST": "#a3be8c", "SYN_CM": "#616e88", "SYN_NM": "#b48ead",
        "SYN_OP": "#81a1c1", "SYN_FN": "#88c0d0",
    },
    "GitHub Dark": {
        "BG0": "#0d1117", "BG1": "#161b22", "BG2": "#0d1117",
        "BG3": "#161b22", "BG4": "#1c2128", "BG5": "#21262d",
        "BG6": "#30363d", "BG7": "#373e47",
        "BG_EDITOR": "#0d1117", "BG_TOPBAR": "#010409",
        "TAB_BAR": "#010409", "TAB_INACTIVE": "#161b22", "TAB_ACTIVE": "#30363d",
        "ACCENT": "#2f81f7", "ACCENT_HOVER": "#4493f8",
        "ACCENT_DARK": "#0d2a4a", "ACCENT_TEXT": "#ffffff",
        "RED": "#f85149", "ORANGE": "#db6d28", "YELLOW": "#e3b341",
        "PURPLE": "#a371f7", "GREEN_BRIGHT": "#3fb950",
        "T1": "#e6edf3", "T2": "#7d8590", "T3": "#7d8590", "T4": "#484f58",
        "BORDER": "#30363d", "SCROLL": "#30363d", "SCROLL_H": "#484f58",
        "SYN_KW": "#ff7b72", "SYN_BI": "#d2a8ff", "SYN_GL": "#79c0ff",
        "SYN_ST": "#a5d6ff", "SYN_CM": "#8b949e", "SYN_NM": "#79c0ff",
        "SYN_OP": "#ff7b72", "SYN_FN": "#d2a8ff",
    },
    "Solarized Dark": {
        "BG0": "#001e26", "BG1": "#00232c", "BG2": "#002b36",
        "BG3": "#073642", "BG4": "#0d4653", "BG5": "#155566",
        "BG6": "#1d6376", "BG7": "#245566",
        "BG_EDITOR": "#002b36", "BG_TOPBAR": "#001e26",
        "TAB_BAR": "#001e26", "TAB_INACTIVE": "#073642", "TAB_ACTIVE": "#155566",
        "ACCENT": "#268bd2", "ACCENT_HOVER": "#3ea1ec",
        "ACCENT_DARK": "#0d3a5a", "ACCENT_TEXT": "#fdf6e3",
        "RED": "#dc322f", "ORANGE": "#cb4b16", "YELLOW": "#b58900",
        "PURPLE": "#6c71c4", "GREEN_BRIGHT": "#859900",
        "T1": "#fdf6e3", "T2": "#93a1a1", "T3": "#93a1a1", "T4": "#657b83",
        "BORDER": "#073642", "SCROLL": "#073642", "SCROLL_H": "#0d4653",
        "SYN_KW": "#859900", "SYN_BI": "#268bd2", "SYN_GL": "#cb4b16",
        "SYN_ST": "#2aa198", "SYN_CM": "#586e75", "SYN_NM": "#d33682",
        "SYN_OP": "#93a1a1", "SYN_FN": "#b58900",
    },
}


class C:
    """Live color palette — populated from selected theme at runtime."""
    BG0 = "#000000"; BG1 = "#0a0a0a"; BG2 = "#111111"; BG3 = "#181818"
    BG4 = "#1f1f1f"; BG5 = "#262626"; BG6 = "#2e2e2e"; BG7 = "#353535"
    BG_EDITOR = "#080808"; BG_TOPBAR = "#0a0a0a"
    TAB_BAR = "#050505"; TAB_INACTIVE = "#1a1a1a"; TAB_ACTIVE = "#2b2b2b"
    ACCENT = "#e8e8e8"; ACCENT_HOVER = "#ffffff"
    ACCENT_DARK = "#3a3a3a"; ACCENT_TEXT = "#000000"
    RED = "#e05555"; ORANGE = "#e8a04e"; YELLOW = "#e8d060"
    PURPLE = "#a880d4"; GREEN_BRIGHT = "#00e070"
    T1 = "#f0f0f0"; T2 = "#a0a0a0"; T3 = "#808080"; T4 = "#404040"
    BORDER = "#222222"; SCROLL = "#333333"; SCROLL_H = "#4a4a4a"
    SYN_KW = "#d0a0d0"; SYN_BI = "#e8b878"; SYN_GL = "#d88888"
    SYN_ST = "#a8c8a8"; SYN_CM = "#585858"; SYN_NM = "#d8b878"
    SYN_OP = "#b8b8b8"; SYN_FN = "#d8c898"

    @classmethod
    def apply_theme(cls, name: str):
        theme = THEMES.get(name, THEMES["Pure Black"])
        for k, v in theme.items():
            setattr(cls, k, v)


# ═══════════════════════════════════════════════════════════════════════════════
#  PERSISTENT DATA
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Settings:
    font_family: str = "Consolas"
    font_size: int = 13
    win_w: int = 1200
    win_h: int = 750
    win_x: int = -1
    win_y: int = -1
    last_dir: str = ""
    auto_clear: bool = False
    confirm_exec: bool = False
    wrap_text: bool = False
    line_numbers: bool = True
    bridge_port: int = BRIDGE_PORT
    username: str = "User"
    topmost: bool = False
    opacity: float = 1.0
    last_page: str = "editor"
    autoexec_path: str = ""
    recent_files: List[str] = field(default_factory=list)
    theme: str = "Pure Black"

    def save(self):
        try:
            CONFIG_FILE.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Save settings: {e}")

    @classmethod
    def load(cls) -> "Settings":
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except Exception:
                pass
        return cls()


@dataclass
class TabData:
    name: str = "Script 1"
    content: str = ""
    filepath: str = ""
    modified: bool = False


class TabStore:
    @staticmethod
    def save(tabs: List[TabData], idx: int):
        try:
            data = {"active": idx, "tabs": [
                {"name": t.name, "content": t.content, "filepath": t.filepath}
                for t in tabs
            ]}
            TABS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Save tabs: {e}")

    @staticmethod
    def load():
        if TABS_FILE.exists():
            try:
                data = json.loads(TABS_FILE.read_text(encoding="utf-8"))
                tabs = [TabData(name=t.get("name", "Script"), content=t.get("content", ""),
                                filepath=t.get("filepath", "")) for t in data.get("tabs", [])]
                if not tabs:
                    tabs = [TabData()]
                return tabs, min(data.get("active", 0), len(tabs) - 1)
            except Exception:
                pass
        return [TabData(content="-- Vevox Script Editor\n-- Ctrl+Enter to execute\n\nprint(\"Hello from Vevox!\")\n")], 0


class History:
    def __init__(self):
        self.records: List[Dict] = []
        self._load()

    def _load(self):
        if HISTORY_FILE.exists():
            try:
                self.records = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            except Exception:
                self.records = []

    def _save(self):
        try:
            HISTORY_FILE.write_text(json.dumps(self.records[-MAX_HISTORY:], indent=2), encoding="utf-8")
        except Exception:
            pass

    def add(self, code, status, source="editor", target="all"):
        self.records.append({
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "snippet": code[:120].replace("\n", "↵"),
            "status": status, "source": source, "chars": len(code),
            "target": target,
        })
        self._save()

    def clear(self):
        self.records.clear()
        self._save()


class CustomHubStore:
    @staticmethod
    def load() -> List[Dict]:
        if CUSTOM_HUB_FILE.exists():
            try:
                return json.loads(CUSTOM_HUB_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return []

    @staticmethod
    def save(scripts: List[Dict]):
        try:
            CUSTOM_HUB_FILE.write_text(json.dumps(scripts, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Save custom hub: {e}")


class RemoteLinks:
    def __init__(self):
        self.discord = ""
        self.website = ""
        self.last_fetch = 0.0
        self.last_error = ""
        self._load_cache()

    def _load_cache(self):
        if REMOTE_CACHE_FILE.exists():
            try:
                data = json.loads(REMOTE_CACHE_FILE.read_text(encoding="utf-8"))
                self.discord = data.get("discord", "")
                self.website = data.get("website", "")
                self.last_fetch = data.get("_fetched", 0.0)
            except Exception:
                pass

    def _save_cache(self):
        try:
            REMOTE_CACHE_FILE.write_text(json.dumps({
                "discord": self.discord, "website": self.website,
                "_fetched": self.last_fetch,
            }, indent=2), encoding="utf-8")
        except Exception:
            pass

    def fetch(self, force=False):
        if not force and (time.time() - self.last_fetch) < REMOTE_LINKS_TTL:
            return True
        try:
            url = f"{REMOTE_LINKS_URL}?t={int(time.time())}"
            req = urllib.request.Request(url, headers={"User-Agent": f"Vevox/{APP_VERSION}"})
            with urllib.request.urlopen(req, timeout=REMOTE_LINKS_TIMEOUT) as r:
                data = json.loads(r.read().decode("utf-8"))
            self.discord = data.get("discord", "")
            self.website = data.get("website", "")
            self.last_fetch = time.time()
            self.last_error = ""
            self._save_cache()
            return True
        except Exception as e:
            self.last_error = str(e)[:120]
            return False

    def fetch_async(self, cb=None):
        def _r():
            ok = self.fetch()
            if cb:
                cb(ok)
        threading.Thread(target=_r, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
#  INSTANCE MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class Instance:
    def __init__(self, instance_id: str):
        self.id = instance_id
        self.short_id = instance_id[:6]
        self.first_seen = time.time()
        self.last_ping = time.time()
        self.game_info: Dict = {}
        self.queue: queue.Queue = queue.Queue()
        self.display_name = f"Instance {self.short_id}"
        self.number = 0


class InstanceManager:
    def __init__(self):
        self.instances: Dict[str, Instance] = {}
        self.legacy_queue: queue.Queue = queue.Queue()
        self._lock = threading.Lock()
        self._counter = 0

    def get_or_create(self, instance_id: str) -> Instance:
        with self._lock:
            if instance_id not in self.instances:
                inst = Instance(instance_id)
                self._counter += 1
                inst.number = self._counter
                inst.display_name = f"Instance {inst.number}"
                self.instances[instance_id] = inst
                return inst
            self.instances[instance_id].last_ping = time.time()
            return self.instances[instance_id]

    def touch(self, instance_id: str):
        if instance_id in self.instances:
            self.instances[instance_id].last_ping = time.time()

    def update_info(self, instance_id: str, info: Dict):
        with self._lock:
            if instance_id in self.instances:
                self.instances[instance_id].game_info = info

    def cleanup_stale(self):
        now = time.time()
        with self._lock:
            stale = [iid for iid, inst in self.instances.items()
                     if (now - inst.last_ping) > INSTANCE_TIMEOUT]
            for iid in stale:
                del self.instances[iid]
            return len(stale)

    def alive_instances(self) -> List[Instance]:
        with self._lock:
            return list(self.instances.values())

    def enqueue(self, code: str, target: str = "all"):
        if target == "all":
            for inst in self.alive_instances():
                inst.queue.put(code)
            self.legacy_queue.put(code)
        elif target == "legacy":
            self.legacy_queue.put(code)
        else:
            with self._lock:
                if target in self.instances:
                    self.instances[target].queue.put(code)

    def dequeue(self, instance_id: Optional[str]) -> str:
        if not instance_id:
            try:
                return self.legacy_queue.get_nowait()
            except queue.Empty:
                return ""
        with self._lock:
            inst = self.instances.get(instance_id)
        if inst is None:
            return ""
        try:
            return inst.queue.get_nowait()
        except queue.Empty:
            return ""

    def total_queue_size(self) -> int:
        n = self.legacy_queue.qsize()
        for inst in self.alive_instances():
            n += inst.queue.qsize()
        return n


# ═══════════════════════════════════════════════════════════════════════════════
#  BUILT-IN SCRIPT HUB
# ═══════════════════════════════════════════════════════════════════════════════

BUILTIN_HUB: List[Dict] = [
    {"name": "Infinite Yield", "author": "Edge", "category": "Admin",
     "desc": "Feature-rich admin commands",
     "code": 'loadstring(game:HttpGet("https://raw.githubusercontent.com/EdgeIY/infiniteyield/master/source"))()',
     "builtin": True},
    {"name": "Dex Explorer", "author": "Raspberry Pi", "category": "Utility",
     "desc": "In-game instance explorer",
     "code": 'loadstring(game:HttpGet("https://raw.githubusercontent.com/infyiff/backup/main/dex.lua"))()',
     "builtin": True},
    {"name": "Remote Spy", "author": "Various", "category": "Utility",
     "desc": "Monitor remote events/functions",
     "code": 'loadstring(game:HttpGet("https://raw.githubusercontent.com/infyiff/backup/main/SimpleSpyV3/main.lua"))()',
     "builtin": True},
    {"name": "Speed Hack", "author": "Vevox", "category": "Player",
     "desc": "WalkSpeed = 80",
     "code": "local h=game.Players.LocalPlayer.Character:FindFirstChildOfClass('Humanoid') if h then h.WalkSpeed=80 end",
     "builtin": True},
    {"name": "Jump Power", "author": "Vevox", "category": "Player",
     "desc": "JumpPower = 120",
     "code": "local h=game.Players.LocalPlayer.Character:FindFirstChildOfClass('Humanoid') if h then h.UseJumpPower=true h.JumpPower=120 end",
     "builtin": True},
    {"name": "Noclip", "author": "Vevox", "category": "Player",
     "desc": "Walk through walls",
     "code": "local nc=true\ngame:GetService('RunService').Stepped:Connect(function()\n    if nc and game.Players.LocalPlayer.Character then\n        for _,p in pairs(game.Players.LocalPlayer.Character:GetDescendants()) do\n            if p:IsA('BasePart') then p.CanCollide=false end\n        end\n    end\nend)",
     "builtin": True},
    {"name": "Fly", "author": "Vevox", "category": "Player",
     "desc": "Toggle flight",
     "code": 'loadstring(game:HttpGet("https://pastebin.com/raw/YSK13499"))()',
     "builtin": True},
    {"name": "Fullbright", "author": "Vevox", "category": "Visual",
     "desc": "Remove darkness/shadows",
     "code": "local L=game:GetService('Lighting')\nL.Brightness=2 L.ClockTime=14 L.FogEnd=1e6\nL.GlobalShadows=false L.OutdoorAmbient=Color3.fromRGB(128,128,128)\nL.Ambient=Color3.fromRGB(178,178,178)\nfor _,v in pairs(L:GetChildren()) do if v:IsA('PostEffect') then v.Enabled=false end end",
     "builtin": True},
    {"name": "ESP Players", "author": "Vevox", "category": "Visual",
     "desc": "Highlight all players",
     "code": "for _,p in pairs(game.Players:GetPlayers()) do\n    if p~=game.Players.LocalPlayer and p.Character then\n        local h=Instance.new('Highlight',p.Character)\n        h.FillColor=Color3.new(1,0,0) h.FillTransparency=0.5\n    end\nend",
     "builtin": True},
    {"name": "Anti-AFK", "author": "Vevox", "category": "Utility",
     "desc": "Prevent inactivity kick",
     "code": "local vu=game:GetService('VirtualUser')\ngame.Players.LocalPlayer.Idled:Connect(function()\n    vu:Button2Down(Vector2.new(0,0),workspace.CurrentCamera.CFrame)\n    task.wait(1)\n    vu:Button2Up(Vector2.new(0,0),workspace.CurrentCamera.CFrame)\nend)",
     "builtin": True},
    {"name": "ClickTP", "author": "Vevox", "category": "Player",
     "desc": "Click to teleport (E to toggle)",
     "code": "local UIS=game:GetService('UserInputService')\nlocal p=game.Players.LocalPlayer\nlocal m=p:GetMouse()\nlocal on=true\nUIS.InputBegan:Connect(function(i) if i.KeyCode==Enum.KeyCode.E then on=not on end end)\nm.Button1Down:Connect(function()\n    if on and p.Character and p.Character:FindFirstChild('HumanoidRootPart') then\n        p.Character.HumanoidRootPart.CFrame=CFrame.new(m.Hit.Position+Vector3.new(0,3,0))\n    end\nend)",
     "builtin": True},
    {"name": "RGB Character", "author": "Vevox", "category": "Fun",
     "desc": "Rainbow cycling colors",
     "code": "task.spawn(function()\n    local c=game.Players.LocalPlayer.Character local h=0\n    while c and c.Parent do h=(h+1)%360\n        local cl=Color3.fromHSV(h/360,1,1)\n        for _,p in pairs(c:GetDescendants()) do if p:IsA('BasePart') then p.Color=cl end end\n        task.wait(0.03)\n    end\nend)",
     "builtin": True},
    {"name": "FPS Counter", "author": "Vevox", "category": "Utility",
     "desc": "On-screen FPS display",
     "code": "local RS=game:GetService('RunService')\nlocal sg=Instance.new('ScreenGui',game.Players.LocalPlayer.PlayerGui)\nsg.ResetOnSpawn=false\nlocal l=Instance.new('TextLabel',sg)\nl.Size=UDim2.new(0,110,0,28) l.Position=UDim2.new(0,8,0,8)\nl.BackgroundColor3=Color3.fromRGB(10,10,10) l.BackgroundTransparency=0.2\nl.TextColor3=Color3.fromRGB(232,232,232) l.Font=Enum.Font.RobotoMono l.TextSize=14\nlocal f,c,e=0,0,0\nRS.RenderStepped:Connect(function(dt) c=c+1 e=e+dt\n    if e>=0.5 then f=math.floor(c/e) c=0 e=0 end\n    l.Text=' FPS: '..f\nend)",
     "builtin": True},
    {"name": "Reset Stats", "author": "Vevox", "category": "Utility",
     "desc": "Reset WalkSpeed/JumpPower",
     "code": "local h=game.Players.LocalPlayer.Character:FindFirstChildOfClass('Humanoid') if h then h.WalkSpeed=16 h.UseJumpPower=true h.JumpPower=50 end",
     "builtin": True},
]


# ═══════════════════════════════════════════════════════════════════════════════
#  HTTP BRIDGE SERVER
# ═══════════════════════════════════════════════════════════════════════════════

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, ct, body):
        self.send_response(code)
        self.send_header("Content-Type", ct)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body.encode("utf-8") if isinstance(body, str) else body)

    def _parse_id(self) -> Optional[str]:
        if "?" not in self.path:
            return None
        try:
            qs = self.path.split("?", 1)[1]
            for part in qs.split("&"):
                if part.startswith("id="):
                    return part[3:]
        except Exception:
            pass
        return None

    def _path_base(self) -> str:
        return self.path.split("?", 1)[0]

    def do_GET(self):
        a = self.server.app
        base = self._path_base()
        inst_id = self._parse_id()

        if base in ("/", ""):
            if inst_id:
                a.instances.get_or_create(inst_id)
                a.instances.touch(inst_id)
                code = a.instances.dequeue(inst_id)
            else:
                code = a.instances.dequeue(None)
            self._send(200, "text/plain", code)

        elif base == "/ping":
            if inst_id:
                a.instances.get_or_create(inst_id)
                a.instances.touch(inst_id)
                a.on_ping(inst_id)
            else:
                a.on_ping(None)
            self._send(200, "text/plain", "pong")

        elif base == "/health":
            self._send(200, "text/plain", "OK")

        elif base == "/status":
            self._send(200, "application/json", json.dumps({
                "queue": a.instances.total_queue_size(),
                "instances": len(a.instances.alive_instances()),
                "version": APP_VERSION,
            }))

        else:
            self._send(404, "text/plain", "")

    def do_POST(self):
        a = self.server.app
        base = self._path_base()
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n).decode("utf-8") if n else ""

        if base == "/callback":
            try:
                data = json.loads(body)
                iid = data.get("instance_id")
                if iid:
                    a.instances.get_or_create(iid)
                    a.instances.touch(iid)
                a.on_callback(data)
            except Exception:
                pass
            self._send(200, "text/plain", "OK")

        elif base == "/console":
            try:
                data = json.loads(body)
                iid = data.get("instance_id")
                if iid:
                    a.instances.get_or_create(iid)
                    a.instances.touch(iid)
                a.on_remote_console(data)
            except Exception:
                pass
            self._send(200, "text/plain", "OK")

        elif base == "/game-info":
            try:
                data = json.loads(body)
                iid = data.get("instance_id")
                if iid:
                    a.instances.get_or_create(iid)
                    a.instances.update_info(iid, data)
                a.on_game_info(data)
            except Exception:
                pass
            self._send(200, "text/plain", "OK")

        else:
            self._send(404, "text/plain", "")


class BridgeServer:
    def __init__(self, app, host, port):
        self.app = app
        self.host = host
        self.port = port
        self.httpd = None
        self.thread = None
        self.running = False

    def start(self):
        try:
            self.httpd = http.server.HTTPServer((self.host, self.port), Handler)
            self.httpd.app = self.app
            self.httpd.timeout = 1
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            return True
        except OSError:
            return False

    def _run(self):
        while self.running:
            try:
                self.httpd.handle_request()
            except Exception:
                if self.running:
                    time.sleep(0.1)

    def stop(self):
        self.running = False
        if self.httpd:
            try:
                self.httpd.server_close()
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
#  SYNTAX HIGHLIGHTING
# ═══════════════════════════════════════════════════════════════════════════════

LUA_KW = {
    "and", "break", "do", "else", "elseif", "end", "false", "for",
    "function", "goto", "if", "in", "local", "nil", "not", "or",
    "repeat", "return", "then", "true", "until", "while",
}
LUA_BI = {
    "print", "warn", "error", "type", "tostring", "tonumber", "pairs",
    "ipairs", "next", "select", "unpack", "require", "pcall", "xpcall",
    "setmetatable", "getmetatable", "rawget", "rawset", "rawequal",
    "assert", "loadstring", "load", "collectgarbage", "typeof",
    "newproxy", "setfenv", "getfenv",
}
LUA_GL = {
    "game", "workspace", "script", "Instance", "Color3", "Vector3",
    "Vector2", "CFrame", "UDim2", "UDim", "Enum", "math", "string",
    "table", "coroutine", "task", "os", "debug", "bit32",
    "tick", "time", "wait", "spawn", "delay",
    "Drawing", "syn", "fluxus", "hookfunction", "hookmetamethod",
    "getgenv", "getrenv", "getreg", "getgc", "getinstances",
    "getnilinstances", "getloadedmodules", "getconnections",
    "firetouchinterest", "fireclickdetector", "fireproximityprompt",
    "setclipboard", "setfflag", "iscclosure", "islclosure",
    "checkcaller", "getcallingscript", "getnamecallmethod",
    "identifyexecutor", "request", "http_request",
}
_FN_RE = re.compile(r'\b(\w+)\s*\(')


def hl_lua(tw: tk.Text):
    for t in ("kw", "bi", "gl", "st", "cm", "nm", "op", "fn", "mcm", "mst"):
        tw.tag_remove(t, "1.0", "end")
    code = tw.get("1.0", "end-1c")
    if not code.strip():
        return
    sz = 13
    try:
        f = tw.cget("font")
        if isinstance(f, str) and " " in f:
            sz = int(f.split()[-1])
    except Exception:
        pass
    tw.tag_configure("kw", foreground=C.SYN_KW, font=("Consolas", sz, "bold"))
    tw.tag_configure("bi", foreground=C.SYN_BI)
    tw.tag_configure("gl", foreground=C.SYN_GL)
    tw.tag_configure("st", foreground=C.SYN_ST)
    tw.tag_configure("cm", foreground=C.SYN_CM, font=("Consolas", sz, "italic"))
    tw.tag_configure("nm", foreground=C.SYN_NM)
    tw.tag_configure("op", foreground=C.SYN_OP)
    tw.tag_configure("fn", foreground=C.SYN_FN)
    tw.tag_configure("mcm", foreground=C.SYN_CM, font=("Consolas", sz, "italic"))
    tw.tag_configure("mst", foreground=C.SYN_ST)

    def ix(p):
        return f"1.0+{p}c"

    for m in re.finditer(r'--\[\[[\s\S]*?\]\]', code):
        tw.tag_add("mcm", ix(m.start()), ix(m.end()))
    for m in re.finditer(r'(?<!--)\[\[[\s\S]*?\]\]', code):
        tw.tag_add("mst", ix(m.start()), ix(m.end()))
    for m in re.finditer(r'--(?!\[\[)[^\n]*', code):
        tw.tag_add("cm", ix(m.start()), ix(m.end()))
    for m in re.finditer(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'', code):
        tw.tag_add("st", ix(m.start()), ix(m.end()))
    for m in re.finditer(r'\b0x[0-9a-fA-F]+\b|\b\d+\.?\d*(?:[eE][+-]?\d+)?\b', code):
        tw.tag_add("nm", ix(m.start()), ix(m.end()))
    for m in _FN_RE.finditer(code):
        n = m.group(1)
        if n not in LUA_KW and n not in LUA_BI and n not in LUA_GL:
            tw.tag_add("fn", ix(m.start(1)), ix(m.end(1)))
    for m in re.finditer(r'\b(' + '|'.join(LUA_KW) + r')\b', code):
        tw.tag_add("kw", ix(m.start()), ix(m.end()))
    for m in re.finditer(r'\b(' + '|'.join(LUA_BI) + r')\b', code):
        tw.tag_add("bi", ix(m.start()), ix(m.end()))
    for m in re.finditer(r'\b(' + '|'.join(re.escape(g) for g in LUA_GL) + r')\b', code):
        tw.tag_add("gl", ix(m.start()), ix(m.end()))
    for m in re.finditer(r'[=~<>]=?|\.\.\.?|[+\-*/%^#&|]', code):
        tw.tag_add("op", ix(m.start()), ix(m.end()))


# ═══════════════════════════════════════════════════════════════════════════════
#  LINE NUMBERS
# ═══════════════════════════════════════════════════════════════════════════════

class LineNums(tk.Canvas):
    def __init__(self, master, tw, **kw):
        super().__init__(master, **kw)
        self.tw = tw
        self.configure(bg=C.BG0, highlightthickness=0, width=46, bd=0, relief="flat")

    def redraw(self):
        self.delete("all")
        if not self.tw:
            return
        i = self.tw.index("@0,0")
        while True:
            dl = self.tw.dlineinfo(i)
            if dl is None:
                break
            y = dl[1]
            ln = str(i).split(".")[0]
            self.create_text(38, y + 2, anchor="ne", text=ln,
                             fill=C.T3, font=("Consolas", 11))
            i = self.tw.index(f"{i}+1line")
            if int(i.split(".")[0]) > int(self.tw.index("end").split(".")[0]):
                break


# ═══════════════════════════════════════════════════════════════════════════════
#  EDITOR TAB WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class EditorTab(tk.Frame):
    def __init__(self, master, app, index: int, tab_data: TabData,
                 is_active: bool, can_close: bool):
        bg_color = C.TAB_ACTIVE if is_active else C.TAB_INACTIVE
        super().__init__(master, bg=bg_color, bd=0, highlightthickness=0)

        self.app = app
        self.index = index
        self.tab_data = tab_data
        self.is_active = is_active
        self.bg_color = bg_color

        self.configure(width=TAB_WIDTH_MIN, height=TAB_BAR_HEIGHT - 2)
        self.pack_propagate(False)

        text_color = C.T1 if is_active else C.T2

        name = tab_data.name
        if tab_data.modified:
            name = "● " + name

        display_name = name if len(name) <= 15 else name[:13] + "…"

        self.label = tk.Label(
            self, text=display_name,
            font=("Segoe UI", 11, "bold" if is_active else "normal"),
            fg=text_color, bg=bg_color,
            cursor="hand2", padx=10
        )
        self.label.pack(side="left", fill="both", expand=True)

        if can_close:
            self.close_btn = tk.Label(
                self, text="×",
                font=("Segoe UI", 14, "bold"),
                fg=C.T2, bg=bg_color,
                cursor="hand2", padx=6
            )
            self.close_btn.pack(side="right", fill="y")
            self.close_btn.bind("<Button-1>", self._on_close_click)
            self.close_btn.bind("<Enter>", lambda e: self.close_btn.configure(fg=C.RED))
            self.close_btn.bind("<Leave>", lambda e: self.close_btn.configure(fg=C.T2))
        else:
            self.close_btn = None

        if is_active:
            self.indicator = tk.Frame(self, bg=C.ACCENT, height=2)
            self.indicator.pack(side="bottom", fill="x")

        for w in (self, self.label):
            w.bind("<Button-1>", self._on_press)
            w.bind("<B1-Motion>", self._on_drag)
            w.bind("<ButtonRelease-1>", self._on_release)
            if not is_active:
                w.bind("<Enter>", self._on_enter)
                w.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        if not self.is_active:
            hover_bg = C.BG5
            self.configure(bg=hover_bg)
            self.label.configure(bg=hover_bg)
            if self.close_btn:
                self.close_btn.configure(bg=hover_bg)

    def _on_leave(self, e):
        if not self.is_active:
            self.configure(bg=self.bg_color)
            self.label.configure(bg=self.bg_color)
            if self.close_btn:
                self.close_btn.configure(bg=self.bg_color)

    def _on_press(self, e):
        self.app._on_tab_press(self.index, e.x_root)

    def _on_drag(self, e):
        self.app._on_tab_drag(e.x_root)

    def _on_release(self, e):
        self.app._on_tab_release(self.index)

    def _on_close_click(self, e):
        self.app._close_tab(self.index)
        return "break"


# ═══════════════════════════════════════════════════════════════════════════════
#  WIDGETS
# ═══════════════════════════════════════════════════════════════════════════════

class SideBtn(ctk.CTkFrame):
    def __init__(self, master, text, icon="", command=None, active=False, **kw):
        super().__init__(master, fg_color="transparent", height=36, corner_radius=8, **kw)
        self.pack_propagate(False)
        self.cmd = command
        self._active = False
        self.inner = ctk.CTkFrame(self, fg_color="transparent", corner_radius=8)
        self.inner.pack(fill="both", expand=True, padx=3, pady=1)
        self.lbl = ctk.CTkLabel(self.inner, text=f"  {icon}  {text}",
                                 font=("Segoe UI", 13), text_color=C.T2,
                                 anchor="w", cursor="hand2")
        self.lbl.pack(fill="both", expand=True, padx=6)
        for w in [self, self.inner, self.lbl]:
            w.bind("<Button-1>", lambda e: self._click())
            w.bind("<Enter>", lambda e: self._enter())
            w.bind("<Leave>", lambda e: self._leave())
        if active:
            self.set_active(True)

    def _click(self):
        if self.cmd:
            self.cmd()

    def _enter(self):
        if not self._active:
            self.inner.configure(fg_color=C.BG5)

    def _leave(self):
        if not self._active:
            self.inner.configure(fg_color="transparent")

    def set_active(self, v):
        self._active = v
        self.inner.configure(fg_color=C.ACCENT_DARK if v else "transparent")
        self.lbl.configure(text_color=C.T1 if v else C.T2)


class StatusDot(ctk.CTkFrame):
    def __init__(self, master, text="", color=None, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        color = color or C.RED
        self.dot = ctk.CTkFrame(self, width=8, height=8, corner_radius=4, fg_color=color)
        self.dot.pack(side="left", padx=(0, 5))
        self.lbl = ctk.CTkLabel(self, text=text, font=("Consolas", 10), text_color=C.T2)
        self.lbl.pack(side="left")

    def set(self, text, color):
        self.dot.configure(fg_color=color)
        self.lbl.configure(text=text)


class Toast:
    def __init__(self, parent):
        self.parent = parent
        self._w = None

    def show(self, msg, kind="info", ms=3000):
        if self._w:
            try:
                self._w.destroy()
            except Exception:
                pass
        colors = {"info": C.BG6, "success": C.GREEN_BRIGHT, "error": C.RED, "warning": C.ORANGE}
        icons = {"info": "ℹ", "success": "✓", "error": "✕", "warning": "⚠"}
        bg = colors.get(kind, C.BG6)
        tc = "black" if kind in ("success", "warning") else "white"
        self._w = ctk.CTkFrame(self.parent, fg_color=bg, corner_radius=8)
        self._w.place(relx=0.5, rely=0.03, anchor="n")
        ctk.CTkLabel(self._w, text=f"  {icons.get(kind, '')}  {msg}  ",
                      text_color=tc, font=("Segoe UI", 12, "bold")).pack(padx=14, pady=7)
        self.parent.after(ms, self._hide)

    def _hide(self):
        if self._w:
            try:
                self._w.destroy()
            except Exception:
                pass
            self._w = None


# ═══════════════════════════════════════════════════════════════════════════════
#  ADD SCRIPT DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class AddScriptDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback, edit_data=None):
        super().__init__(parent)
        self.callback = callback
        self.edit_data = edit_data
        self.title("Edit Script" if edit_data else "Add Script to Hub")
        self.configure(fg_color=C.BG2)
        W, H = 560, 680
        self.geometry(f"{W}x{H}")
        self.minsize(W, H)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        if ICON_PATH:
            try:
                self.after(200, lambda: self.iconbitmap(ICON_PATH))
            except Exception:
                pass

        self.update_idletasks()
        try:
            px = parent.winfo_x() + (parent.winfo_width() // 2) - (W // 2)
            py = parent.winfo_y() + (parent.winfo_height() // 2) - (H // 2)
            self.geometry(f"+{max(0, px)}+{max(0, py)}")
        except Exception:
            pass

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        title_text = "Edit Script" if edit_data else "Add Custom Script"
        ctk.CTkLabel(self, text=title_text, font=("Segoe UI", 18, "bold"),
                      text_color=C.T1).grid(row=0, column=0, padx=24, pady=(20, 12), sticky="w")

        form_container = ctk.CTkFrame(self, fg_color="transparent")
        form_container.grid(row=1, column=0, padx=20, pady=0, sticky="nsew")
        form_container.grid_rowconfigure(0, weight=1)
        form_container.grid_columnconfigure(0, weight=1)

        form = ctk.CTkScrollableFrame(form_container, fg_color="transparent",
                                       scrollbar_button_color=C.SCROLL)
        form.grid(row=0, column=0, sticky="nsew")

        def _label(text):
            ctk.CTkLabel(form, text=text, font=("Segoe UI", 11),
                          text_color=C.T3, anchor="w").pack(fill="x", pady=(0, 2))

        def _entry(placeholder=""):
            e = ctk.CTkEntry(form, fg_color=C.BG7, border_color=C.BORDER,
                              text_color=C.T1, height=34, placeholder_text=placeholder)
            e.pack(fill="x", pady=(0, 12))
            return e

        _label("Script Name *")
        self.name_e = _entry("My Awesome Script")
        _label("Author")
        self.author_e = _entry("Your name")
        _label("Category")
        self.cat_e = _entry("Custom, Utility, Player, etc.")
        _label("Description")
        self.desc_e = _entry("What does this script do?")

        _label("Lua Code *")
        code_frame = ctk.CTkFrame(form, fg_color=C.BG0, corner_radius=6)
        code_frame.pack(fill="both", expand=True, pady=(0, 8))
        self.code_t = tk.Text(code_frame, bg=C.BG0, fg=C.T1, insertbackground=C.T1,
                               font=("Consolas", 12), height=12, relief="flat",
                               borderwidth=0, padx=10, pady=8, wrap="word",
                               selectbackground=C.BG5)
        code_scroll = tk.Scrollbar(code_frame, command=self.code_t.yview,
                                    bg=C.BG1, troughcolor=C.BG0, width=8, relief="flat", bd=0)
        code_scroll.pack(side="right", fill="y", padx=(0, 2), pady=2)
        self.code_t.configure(yscrollcommand=code_scroll.set)
        self.code_t.pack(side="left", fill="both", expand=True, padx=2, pady=2)

        ctk.CTkButton(form, text="📂  Load Code From File", height=30,
                       fg_color=C.BG5, hover_color=C.BG6, text_color=C.T1,
                       corner_radius=6, font=("Segoe UI", 11),
                       command=self._load_file).pack(anchor="w", pady=(0, 12))

        if edit_data:
            self.name_e.insert(0, edit_data.get("name", ""))
            self.author_e.insert(0, edit_data.get("author", ""))
            self.cat_e.insert(0, edit_data.get("category", ""))
            self.desc_e.insert(0, edit_data.get("desc", ""))
            self.code_t.insert("1.0", edit_data.get("code", ""))

        btn_bar = ctk.CTkFrame(self, fg_color=C.BG1, corner_radius=0, height=70)
        btn_bar.grid(row=2, column=0, sticky="ew")
        btn_bar.grid_propagate(False)
        btn_bar.grid_columnconfigure(0, weight=1)
        btn_inner = ctk.CTkFrame(btn_bar, fg_color="transparent")
        btn_inner.grid(row=0, column=0, sticky="e", padx=20, pady=15)

        ctk.CTkButton(btn_inner, text="Cancel", width=100, height=40,
                       fg_color=C.BG5, hover_color=C.BG6,
                       text_color=C.T1, corner_radius=8, font=("Segoe UI", 13),
                       command=self._cancel).pack(side="left", padx=(0, 10))

        save_text = "  💾  Save Changes  " if edit_data else "  ✓  Add Script  "
        ctk.CTkButton(btn_inner, text=save_text, width=180, height=40,
                       fg_color=C.GREEN_BRIGHT, hover_color="#00c060",
                       text_color="#000000", corner_radius=8,
                       font=("Segoe UI", 14, "bold"),
                       command=self._save).pack(side="left")

        self.name_e.focus_set()

    def _load_file(self):
        p = filedialog.askopenfilename(
            filetypes=[("Lua", "*.lua"), ("Text", "*.txt"), ("All", "*.*")], parent=self)
        if p:
            try:
                self.code_t.delete("1.0", "end")
                self.code_t.insert("1.0", Path(p).read_text(encoding="utf-8"))
                if not self.name_e.get().strip():
                    self.name_e.insert(0, Path(p).stem)
            except Exception as e:
                messagebox.showerror("Error", f"Could not read file:\n{e}", parent=self)

    def _cancel(self):
        self.grab_release()
        self.destroy()

    def _save(self):
        name = self.name_e.get().strip()
        code = self.code_t.get("1.0", "end-1c").strip()
        if not name:
            messagebox.showwarning("Missing Name", "Please enter a script name.", parent=self)
            self.name_e.focus_set()
            return
        if not code:
            messagebox.showwarning("Missing Code", "Please enter the Lua code.", parent=self)
            self.code_t.focus_set()
            return
        script = {
            "name": name,
            "author": self.author_e.get().strip() or "Custom",
            "category": self.cat_e.get().strip() or "Custom",
            "desc": self.desc_e.get().strip() or "",
            "code": code,
            "builtin": False,
        }
        try:
            self.callback(script, self.edit_data)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save:\n{e}", parent=self)
            return
        self.grab_release()
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════

class VevoxApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.settings = Settings.load()
        C.apply_theme(self.settings.theme)

        self.history = History()
        self.instances = InstanceManager()
        self.bridge_connected = False
        self.last_ping = 0.0
        self.roblox_attached = False
        self.server: Optional[BridgeServer] = None
        self._shutdown = False
        self._hl_job = None
        self._page = "editor"
        self._side_btns: Dict[str, SideBtn] = {}
        self._game_info: Dict = {}
        self._tabs, self._tab_idx = TabStore.load()
        if self._tab_idx >= len(self._tabs):
            self._tab_idx = 0
        self._custom_hub: List[Dict] = CustomHubStore.load()
        self.remote_links = RemoteLinks()
        self._target_instance = "all"

        self._drag_src_idx = None
        self._drag_start_x = 0
        self._drag_moved = False
        self._tab_widgets: List[EditorTab] = []

        self.title(APP_NAME)
        geo = f"{self.settings.win_w}x{self.settings.win_h}"
        if self.settings.win_x >= 0:
            geo += f"+{self.settings.win_x}+{self.settings.win_y}"
        self.geometry(geo)
        self.minsize(900, 550)
        self.configure(fg_color=C.BG0)
        ctk.set_appearance_mode("dark")

        if ICON_PATH:
            try:
                self.iconbitmap(ICON_PATH)
            except Exception:
                pass

        if self.settings.topmost:
            self.attributes("-topmost", True)
        if self.settings.opacity < 1.0:
            self.attributes("-alpha", self.settings.opacity)

        self._build()
        self.toast = Toast(self)
        self._start_server()
        self._proc_monitor()
        self._bridge_monitor()
        self._instance_cleanup_loop()

        self.remote_links.fetch_async(lambda ok: self.after(0, self._on_links_fetched, ok))

        self.protocol("WM_DELETE_WINDOW", self._quit)
        self.bind("<Control-Return>", lambda e: self._exec())
        self.bind("<Control-s>", lambda e: self._save_file())
        self.bind("<Control-o>", lambda e: self._open_file())
        self.bind("<Control-n>", lambda e: self._new_tab())
        self.bind("<Control-w>", lambda e: self._close_tab())
        self.bind("<Control-f>", lambda e: self._toggle_search())
        self.bind("<Control-l>", lambda e: self._clear_editor())
        self.bind("<F5>", lambda e: self._exec())

        self._log("Vevox v" + APP_VERSION + " started")
        self._log(f"Theme: {self.settings.theme}", "system")

    def _on_links_fetched(self, ok):
        if ok:
            self._log("Remote links loaded", "system")
        else:
            self._log(f"Links fetch failed: {self.remote_links.last_error}", "warn")

    def _apply_theme(self, theme_name: str):
        self.settings.theme = theme_name
        self.settings.save()
        C.apply_theme(theme_name)
        self._tabs[self._tab_idx].content = self.editor.get("1.0", "end-1c")
        current_page = self._page
        for w in list(self.winfo_children()):
            try:
                w.destroy()
            except Exception:
                pass
        self.configure(fg_color=C.BG0)
        self._build()
        self._nav(current_page)
        self._log(f"Theme changed to: {theme_name}", "system")
        self.toast.show(f"Theme: {theme_name}", "success", 1500)

    # ══════════════════════════════════════════════════════════════════════════
    #  BUILD
    # ══════════════════════════════════════════════════════════════════════════

    def _build(self):
        self._build_topbar()
        self.body = ctk.CTkFrame(self, fg_color=C.BG0, corner_radius=0)
        self.body.pack(fill="both", expand=True)
        self._build_sidebar()
        self._build_content()
        self._build_statusbar()

    def _build_topbar(self):
        top = ctk.CTkFrame(self, fg_color=C.BG_TOPBAR, height=38, corner_radius=0)
        top.pack(fill="x")
        top.pack_propagate(False)
        ctk.CTkLabel(top, text="  ◆", font=("Segoe UI", 16), text_color=C.T1
                      ).pack(side="left", padx=(10, 0))
        ctk.CTkLabel(top, text=APP_NAME, font=("Segoe UI", 14, "bold"),
                      text_color=C.T1).pack(side="left", padx=(4, 0))
        ctk.CTkLabel(top, text=f"v{APP_VERSION}", font=("Segoe UI", 9),
                      text_color=C.T3).pack(side="left", padx=(8, 0))
        right = ctk.CTkFrame(top, fg_color="transparent")
        right.pack(side="right", padx=4)
        ctk.CTkButton(right, text="─", width=30, height=26, fg_color="transparent",
                       hover_color=C.BG5, text_color=C.T3, corner_radius=4,
                       font=("Consolas", 13), command=self.iconify).pack(side="left", padx=1)
        ctk.CTkButton(right, text="✕", width=30, height=26, fg_color="transparent",
                       hover_color=C.RED, text_color=C.T3, corner_radius=4,
                       font=("Consolas", 13), command=self._quit).pack(side="left", padx=1)

    def _build_sidebar(self):
        self._side_btns = {}
        self.sidebar = ctk.CTkFrame(self.body, fg_color=C.BG1, width=180, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self._slbl("Main")
        self._sbtn("home", "Home", "⌂")
        self._sbtn("editor", "Editor", "✎", active=True)
        self._sbtn("hub", "Script Hub", "◈")
        self._sbtn("console", "Console", "▤")
        self._sbtn("files", "Scripts", "⊟")
        self._sbtn("history", "History", "↻")
        self._sbtn("instances", "Instances", "⊚")

        ctk.CTkFrame(self.sidebar, fg_color=C.BORDER, height=1).pack(fill="x", padx=14, pady=8)

        self._slbl("Tools")
        self._sbtn("bridge", "Bridge Setup", "⇄")
        self._sbtn("settings", "Settings", "⚙")

        ctk.CTkFrame(self.sidebar, fg_color=C.BORDER, height=1).pack(fill="x", padx=14, pady=8)

        self._slbl("Links")
        SideBtn(self.sidebar, "Discord", "◉",
                command=self._open_discord).pack(fill="x", padx=3)
        SideBtn(self.sidebar, "Website", "◎",
                command=self._open_website).pack(fill="x", padx=3)
        SideBtn(self.sidebar, "Open autoexec", "⊞",
                command=self._open_autoexec_folder).pack(fill="x", padx=3)
        SideBtn(self.sidebar, "Kill Roblox", "⏻",
                command=self._kill_roblox).pack(fill="x", padx=3)

        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(fill="both", expand=True)

        user = ctk.CTkFrame(self.sidebar, fg_color=C.BG3, corner_radius=10, height=50)
        user.pack(fill="x", padx=8, pady=8)
        user.pack_propagate(False)
        av = ctk.CTkFrame(user, width=30, height=30, corner_radius=15, fg_color=C.BG6)
        av.pack(side="left", padx=(10, 8), pady=10)
        av.pack_propagate(False)
        ctk.CTkLabel(av, text=self.settings.username[0].upper(),
                      font=("Segoe UI", 13, "bold"), text_color=C.T1
                      ).place(relx=0.5, rely=0.5, anchor="center")
        ui = ctk.CTkFrame(user, fg_color="transparent")
        ui.pack(side="left", fill="both", expand=True, pady=8)
        ctk.CTkLabel(ui, text=self.settings.username, font=("Segoe UI", 11, "bold"),
                      text_color=C.T1, anchor="w").pack(fill="x")
        ctk.CTkLabel(ui, text="Signed in", font=("Segoe UI", 9),
                      text_color=C.T3, anchor="w").pack(fill="x")

    def _slbl(self, t):
        ctk.CTkLabel(self.sidebar, text=f"  {t}", font=("Segoe UI", 10, "bold"),
                      text_color=C.T4, anchor="w").pack(fill="x", padx=14, pady=(12, 3))

    def _sbtn(self, pid, text, icon, active=False):
        b = SideBtn(self.sidebar, text, icon, command=lambda: self._nav(pid), active=active)
        b.pack(fill="x", padx=3)
        self._side_btns[pid] = b

    def _build_content(self):
        self.content = ctk.CTkFrame(self.body, fg_color=C.BG2, corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)
        self.pages: Dict[str, ctk.CTkFrame] = {}
        for p in ["home", "editor", "hub", "console", "files", "history",
                   "instances", "bridge", "settings"]:
            self.pages[p] = ctk.CTkFrame(self.content, fg_color=C.BG2, corner_radius=0)

        self._build_home()
        self._build_editor()
        self._build_hub()
        self._build_console()
        self._build_files()
        self._build_history()
        self._build_instances()
        self._build_bridge()
        self._build_settings()
        self._nav(self.settings.last_page if self.settings.last_page in self.pages else "editor")

    def _nav(self, pid):
        for f in self.pages.values():
            f.pack_forget()
        if pid in self.pages:
            self.pages[pid].pack(fill="both", expand=True)
            self._page = pid
            self.settings.last_page = pid
            if pid == "files":
                self._refresh_files()
            elif pid == "history":
                self._refresh_history()
            elif pid == "home":
                self._refresh_home()
            elif pid == "hub":
                self._populate_hub()
            elif pid == "bridge":
                self._refresh_bridge()
            elif pid == "instances":
                self._refresh_instances()
        for k, b in self._side_btns.items():
            b.set_active(k == pid)

    # ── REMOTE LINKS ─────────────────────────────────────────────────────────

    def _open_discord(self):
        url = self.remote_links.discord
        if url:
            webbrowser.open(url)
        else:
            self.toast.show("Fetching...", "info", 1500)
            def done(ok):
                if ok and self.remote_links.discord:
                    self.after(0, lambda: webbrowser.open(self.remote_links.discord))
                else:
                    self.after(0, lambda: self.toast.show("No Discord link set", "warning"))
            self.remote_links.fetch_async(done)

    def _open_website(self):
        url = self.remote_links.website
        if url:
            webbrowser.open(url)
        else:
            self.toast.show("Fetching...", "info", 1500)
            def done(ok):
                if ok and self.remote_links.website:
                    self.after(0, lambda: webbrowser.open(self.remote_links.website))
                else:
                    self.after(0, lambda: self.toast.show("No Website link set", "warning"))
            self.remote_links.fetch_async(done)

    # ── HOME ─────────────────────────────────────────────────────────────────

    def _build_home(self):
        p = self.pages["home"]
        ctk.CTkLabel(p, text="Overview", font=("Segoe UI", 20, "bold"),
                      text_color=C.T1, anchor="w").pack(fill="x", padx=24, pady=(20, 14))
        self.home_sc = ctk.CTkScrollableFrame(p, fg_color="transparent",
                                                scrollbar_button_color=C.SCROLL)
        self.home_sc.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    def _refresh_home(self):
        for w in self.home_sc.winfo_children():
            w.destroy()
        c1 = self._card(self.home_sc, "License")
        self._crow_val(c1, "Status", "Free", C.T1)
        self._crow_val(c1, "Expires", "Never", C.T2)

        c2 = self._card(self.home_sc, "Connection")
        n_inst = len(self.instances.alive_instances())
        self._crow_val(c2, "Server",
                        "Running" if self.server and self.server.running else "Stopped",
                        C.T1 if self.server and self.server.running else C.RED)
        self._crow_val(c2, "Bridge",
                        f"{n_inst} instance(s)" if n_inst else "Waiting",
                        C.T1 if n_inst else C.ORANGE)
        self._crow_val(c2, "Roblox",
                        "Attached ✓" if self.roblox_attached else "Not Found",
                        C.T1 if self.roblox_attached else C.RED)

        c3 = self._card(self.home_sc, "Statistics")
        sc = len(list(SCRIPTS_DIR.glob("*.lua")) + list(SCRIPTS_DIR.glob("*.txt")))
        self._crow_val(c3, "Executions", str(len(self.history.records)), C.T2)
        self._crow_val(c3, "Scripts Saved", str(sc), C.T2)
        self._crow_val(c3, "Custom Hub Scripts", str(len(self._custom_hub)), C.T2)
        self._crow_val(c3, "Current Theme", self.settings.theme, C.T2)
        self._crow_val(c3, "Editor Tabs", str(len(self._tabs)), C.T2)

        c4 = self._card(self.home_sc, "Community Links")
        rl = self.remote_links
        self._crow_val(c4, "Discord", rl.discord or "(not set)",
                        C.T1 if rl.discord else C.T3)
        self._crow_val(c4, "Website", rl.website or "(not set)",
                        C.T1 if rl.website else C.T3)
        if rl.last_fetch:
            age = int(time.time() - rl.last_fetch)
            ctk.CTkLabel(c4, text=f"  Last synced {age}s ago", font=("Segoe UI", 10),
                          text_color=C.T4).pack(anchor="w", padx=16, pady=(2, 8))

        c5 = self._card(self.home_sc, "What's New")
        vf = ctk.CTkFrame(c5, fg_color="transparent")
        vf.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(vf, text=f"v{APP_VERSION}", font=("Segoe UI", 14, "bold"),
                      text_color=C.T1).pack(side="left")
        tag = ctk.CTkFrame(vf, fg_color=C.T1, width=50, height=18, corner_radius=4)
        tag.pack(side="left", padx=8)
        ctk.CTkLabel(tag, text="LATEST", text_color=C.BG0,
                      font=("Segoe UI", 8, "bold")).place(relx=0.5, rely=0.5, anchor="center")
        for line in [
            "• Simplified — removed admin system",
            "• 6 built-in themes with distinct tab colors",
            "• Drag tabs left/right to reorder them",
            "• Multi-instance support with per-instance targeting",
            "• Bridge listener v5.0 for instance identification",
        ]:
            ctk.CTkLabel(c5, text=line, font=("Segoe UI", 11),
                          text_color=C.T3, anchor="w").pack(fill="x", padx=20, pady=1)
        ctk.CTkFrame(c5, height=8, fg_color="transparent").pack()

    def _card(self, parent, title):
        c = ctk.CTkFrame(parent, fg_color=C.BG3, corner_radius=12)
        c.pack(fill="x", pady=5)
        ctk.CTkLabel(c, text=title, font=("Segoe UI", 12, "bold"),
                      text_color=C.T2, anchor="w").pack(fill="x", padx=16, pady=(12, 4))
        return c

    def _crow(self, card, text):
        r = ctk.CTkFrame(card, fg_color="transparent", height=30)
        r.pack(fill="x", padx=16, pady=1)
        r.pack_propagate(False)
        ctk.CTkLabel(r, text=text, font=("Segoe UI", 13), text_color=C.T1,
                      anchor="w").pack(side="left")
        return r

    def _crow_val(self, card, label, value, color):
        r = self._crow(card, label)
        ctk.CTkLabel(r, text=value, text_color=color,
                      font=("Segoe UI", 13, "bold")).pack(side="right", padx=12)

    # ══════════════════════════════════════════════════════════════════════════
    #  EDITOR
    # ══════════════════════════════════════════════════════════════════════════

    def _build_editor(self):
        p = self.pages["editor"]

        self.tab_bar_outer = tk.Frame(p, bg=C.TAB_BAR, height=TAB_BAR_HEIGHT)
        self.tab_bar_outer.pack(fill="x", side="top")
        self.tab_bar_outer.pack_propagate(False)

        self.tab_container = tk.Frame(self.tab_bar_outer, bg=C.TAB_BAR)
        self.tab_container.pack(side="left", fill="y", padx=(4, 0), pady=(2, 0))

        self.new_tab_btn = tk.Label(
            self.tab_bar_outer, text="+ New Tab",
            font=("Segoe UI", 11, "bold"),
            fg=C.T1, bg=C.TAB_BAR,
            cursor="hand2", padx=12, pady=6
        )
        self.new_tab_btn.pack(side="left", padx=6, pady=2)
        self.new_tab_btn.bind("<Button-1>", lambda e: self._new_tab())
        self.new_tab_btn.bind("<Enter>", lambda e: self.new_tab_btn.configure(bg=C.BG5))
        self.new_tab_btn.bind("<Leave>", lambda e: self.new_tab_btn.configure(bg=C.TAB_BAR))

        self.search_bar = ctk.CTkFrame(p, fg_color=C.BG3, height=36, corner_radius=0)
        self._search_vis = False
        self.search_e = ctk.CTkEntry(self.search_bar, placeholder_text="Find...",
                                      width=220, height=26, fg_color=C.BG7,
                                      border_color=C.BORDER, text_color=C.T1)
        self.search_e.pack(side="left", padx=6, pady=5)
        self.search_e.bind("<Return>", lambda e: self._find())
        self.replace_e = ctk.CTkEntry(self.search_bar, placeholder_text="Replace...",
                                       width=180, height=26, fg_color=C.BG7,
                                       border_color=C.BORDER, text_color=C.T1)
        self.replace_e.pack(side="left", padx=3, pady=5)
        for t, c in [("Find", self._find), ("Replace", self._replace1), ("All", self._replace_all)]:
            ctk.CTkButton(self.search_bar, text=t, width=44, height=24,
                           fg_color=C.BG5, hover_color=C.BG6, text_color=C.T1,
                           corner_radius=4, command=c).pack(side="left", padx=2)
        ctk.CTkButton(self.search_bar, text="✕", width=26, height=24,
                       fg_color="transparent", hover_color=C.RED,
                       text_color=C.T3, corner_radius=4,
                       command=self._toggle_search).pack(side="right", padx=6)

        ef = ctk.CTkFrame(p, fg_color=C.BG_EDITOR, corner_radius=0)
        ef.pack(fill="both", expand=True)
        inner = tk.Frame(ef, bg=C.BG_EDITOR)
        inner.pack(fill="both", expand=True)

        self.ln = LineNums(inner, None)
        if self.settings.line_numbers:
            self.ln.pack(side="left", fill="y")

        self.editor = tk.Text(
            inner, bg=C.BG_EDITOR, fg=C.T1,
            insertbackground=C.T1, insertwidth=2,
            selectbackground=C.BG6, selectforeground=C.T1,
            font=(self.settings.font_family, self.settings.font_size),
            wrap="none" if not self.settings.wrap_text else "word",
            undo=True, maxundo=100, padx=10, pady=8,
            relief="flat", borderwidth=0, tabs=("4c",),
            spacing1=2, spacing3=2,
        )
        sby = tk.Scrollbar(inner, command=self.editor.yview, bg=C.BG1,
                            troughcolor=C.BG0, activebackground=C.SCROLL_H,
                            width=9, relief="flat", bd=0)
        sby.pack(side="right", fill="y")
        self.editor.configure(yscrollcommand=sby.set)
        sbx = tk.Scrollbar(inner, orient="horizontal", command=self.editor.xview,
                            bg=C.BG1, troughcolor=C.BG0, width=7, relief="flat", bd=0)
        sbx.pack(side="bottom", fill="x")
        self.editor.configure(xscrollcommand=sbx.set)
        self.editor.pack(side="left", fill="both", expand=True)
        self.ln.tw = self.editor

        self.editor.bind("<KeyRelease>", self._on_key)
        self.editor.bind("<MouseWheel>", lambda e: self.after(10, self._upd_ln))
        self.editor.bind("<Button-1>", lambda e: self.after(10, self._upd_ln))
        self.editor.bind("<Tab>", self._tab_key)
        self.editor.bind("<Button-3>", self._rmenu)

        self.ctx = tk.Menu(self.editor, tearoff=0, bg=C.BG3, fg=C.T1,
                            activebackground=C.BG6, activeforeground=C.T1,
                            relief="flat", bd=1)
        self.ctx.add_command(label="  Cut", command=lambda: self.editor.event_generate("<<Cut>>"))
        self.ctx.add_command(label="  Copy", command=lambda: self.editor.event_generate("<<Copy>>"))
        self.ctx.add_command(label="  Paste", command=lambda: self.editor.event_generate("<<Paste>>"))
        self.ctx.add_separator()
        self.ctx.add_command(label="  Find/Replace", command=self._toggle_search)
        self.ctx.add_command(label="  Select All", command=lambda: self.editor.tag_add("sel", "1.0", "end"))
        self.ctx.add_separator()
        self.ctx.add_command(label="  ▶ Execute", command=self._exec)
        self.ctx.add_command(label="  Clear", command=self._clear_editor)

        bot = ctk.CTkFrame(p, fg_color=C.BG1, height=44, corner_radius=0)
        bot.pack(fill="x", side="bottom")
        bot.pack_propagate(False)
        bs = {"height": 30, "corner_radius": 6, "font": ("Segoe UI", 12, "bold")}

        self.exec_btn = ctk.CTkButton(bot, text="  ▶  Execute", width=115,
                                       fg_color=C.ACCENT, hover_color=C.ACCENT_HOVER,
                                       text_color=C.ACCENT_TEXT, command=self._exec, **bs)
        self.exec_btn.pack(side="left", padx=(8, 4), pady=7)

        self.target_var = ctk.StringVar(value="All Instances")
        self.target_menu = ctk.CTkOptionMenu(
            bot, values=["All Instances"], variable=self.target_var,
            width=140, height=30, fg_color=C.BG5, button_color=C.BG6,
            dropdown_fg_color=C.BG3, text_color=C.T1,
            font=("Segoe UI", 11), command=self._on_target_change
        )
        self.target_menu.pack(side="left", padx=(0, 6), pady=7)

        for txt, cmd in [("Clear", self._clear_editor), ("Open", self._open_file), ("Save", self._save_file)]:
            ctk.CTkButton(bot, text=f"  {txt}", width=65, fg_color=C.BG5,
                           hover_color=C.BG6, text_color=C.T1, command=cmd, **bs
                           ).pack(side="left", padx=2, pady=7)

        self.info_lbl = ctk.CTkLabel(bot, text="Ln 1, Col 1", font=("Consolas", 10), text_color=C.T3)
        self.info_lbl.pack(side="right", padx=10)
        self.q_lbl = ctk.CTkLabel(bot, text="Queue: 0", font=("Consolas", 10), text_color=C.T3)
        self.q_lbl.pack(side="right", padx=6)

        self.editor.insert("1.0", self._tabs[self._tab_idx].content)
        self._refresh_tab_bar()
        self._sched_hl()
        self._upd_ln()
        self._upd_info()
        self._refresh_target_menu()

    def _on_target_change(self, choice: str):
        if choice == "All Instances":
            self._target_instance = "all"
        else:
            for inst in self.instances.alive_instances():
                if choice.startswith(inst.display_name):
                    self._target_instance = inst.id
                    return
            self._target_instance = "all"

    def _refresh_target_menu(self):
        if not hasattr(self, "target_menu"):
            return
        options = ["All Instances"]
        for inst in sorted(self.instances.alive_instances(), key=lambda i: i.number):
            player = inst.game_info.get("player", "")
            label = f"{inst.display_name}" + (f" ({player})" if player else "")
            options.append(label)
        try:
            self.target_menu.configure(values=options)
            if self._target_instance != "all":
                exists = any(i.id == self._target_instance for i in self.instances.alive_instances())
                if not exists:
                    self._target_instance = "all"
                    self.target_var.set("All Instances")
        except Exception:
            pass

    def _refresh_tab_bar(self):
        for w in list(self.tab_container.winfo_children()):
            try:
                w.destroy()
            except Exception:
                pass
        self._tab_widgets = []

        can_close = len(self._tabs) > 1
        for i, tab in enumerate(self._tabs):
            tab_w = EditorTab(
                self.tab_container, self, i, tab,
                is_active=(i == self._tab_idx),
                can_close=can_close
            )
            tab_w.pack(side="left", padx=(0, 2), pady=(4, 0))
            self._tab_widgets.append(tab_w)

        self.tab_container.update_idletasks()

    def _on_tab_press(self, idx: int, x_root: int):
        self._drag_src_idx = idx
        self._drag_start_x = x_root
        self._drag_moved = False

    def _on_tab_drag(self, x_root: int):
        if self._drag_src_idx is None:
            return
        dx = x_root - self._drag_start_x
        if abs(dx) < 12:
            return

        self._drag_moved = True

        try:
            for i, w in enumerate(self._tab_widgets):
                if not w.winfo_exists():
                    continue
                x1 = w.winfo_rootx()
                x2 = x1 + w.winfo_width()
                if x1 <= x_root <= x2 and i != self._drag_src_idx:
                    self._tabs[self._drag_src_idx].content = self.editor.get("1.0", "end-1c")
                    tab = self._tabs.pop(self._drag_src_idx)
                    self._tabs.insert(i, tab)
                    self._tab_idx = i
                    self._drag_src_idx = i
                    self._refresh_tab_bar()
                    self._save_tabs()
                    return
        except Exception as e:
            logger.debug(f"drag error: {e}")

    def _on_tab_release(self, idx: int):
        was_drag = self._drag_moved
        src = self._drag_src_idx
        self._drag_src_idx = None
        self._drag_start_x = 0
        self._drag_moved = False

        if not was_drag and src is not None:
            self._switch_tab(src)

    def _switch_tab(self, idx: int):
        if idx == self._tab_idx or idx >= len(self._tabs) or idx < 0:
            return
        self._tabs[self._tab_idx].content = self.editor.get("1.0", "end-1c")
        self._tab_idx = idx
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", self._tabs[idx].content)
        self._refresh_tab_bar()
        self._sched_hl()
        self._upd_ln()
        self._save_tabs()

    def _new_tab(self):
        if len(self._tabs) >= MAX_TABS:
            self.toast.show(f"Max {MAX_TABS} tabs", "warning")
            return
        self._tabs[self._tab_idx].content = self.editor.get("1.0", "end-1c")
        new_num = len(self._tabs) + 1
        self._tabs.append(TabData(name=f"Script {new_num}", content="-- New Script\n\n"))
        self._tab_idx = len(self._tabs) - 1
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", self._tabs[self._tab_idx].content)
        self._refresh_tab_bar()
        self._sched_hl()
        self._upd_ln()
        self._save_tabs()
        self.toast.show(f"New tab: Script {new_num}", "success", 1500)

    def _close_tab(self, idx=None):
        if idx is None:
            idx = self._tab_idx
        if len(self._tabs) <= 1:
            self.toast.show("Can't close last tab", "warning", 1500)
            return
        removed_name = self._tabs[idx].name
        self._tabs.pop(idx)
        if self._tab_idx == idx:
            self._tab_idx = max(0, idx - 1)
        elif self._tab_idx > idx:
            self._tab_idx -= 1
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", self._tabs[self._tab_idx].content)
        self._refresh_tab_bar()
        self._sched_hl()
        self._upd_ln()
        self._save_tabs()
        self.toast.show(f"Closed: {removed_name}", "info", 1500)

    def _save_tabs(self):
        self._tabs[self._tab_idx].content = self.editor.get("1.0", "end-1c")
        TabStore.save(self._tabs, self._tab_idx)

    def _on_key(self, e=None):
        self._sched_hl()
        self._upd_ln()
        self._upd_info()
        if not self._tabs[self._tab_idx].modified:
            self._tabs[self._tab_idx].modified = True
            self._refresh_tab_bar()

    def _sched_hl(self):
        if self._hl_job:
            self.after_cancel(self._hl_job)
        self._hl_job = self.after(200, self._do_hl)

    def _do_hl(self):
        try:
            hl_lua(self.editor)
        except Exception:
            pass

    def _upd_ln(self):
        try:
            self.ln.redraw()
        except Exception:
            pass

    def _upd_info(self):
        try:
            pos = self.editor.index("insert")
            ln, col = pos.split(".")
            ch = len(self.editor.get("1.0", "end-1c"))
            self.info_lbl.configure(text=f"Ln {ln}, Col {int(col)+1}  |  {ch} chars")
        except Exception:
            pass

    def _tab_key(self, e):
        self.editor.insert("insert", "    ")
        return "break"

    def _rmenu(self, e):
        self.ctx.tk_popup(e.x_root, e.y_root)

    def _clear_editor(self):
        self.editor.delete("1.0", "end")
        self._on_key()

    def _toggle_search(self):
        if self._search_vis:
            self.search_bar.pack_forget()
            self._search_vis = False
            self.editor.tag_remove("srch", "1.0", "end")
        else:
            self.search_bar.pack(fill="x", after=self.tab_bar_outer)
            self._search_vis = True
            self.search_e.focus_set()

    def _find(self):
        q = self.search_e.get()
        if not q:
            return
        self.editor.tag_remove("srch", "1.0", "end")
        self.editor.tag_configure("srch", background=C.ORANGE, foreground="black")
        start, cnt = "1.0", 0
        while True:
            pos = self.editor.search(q, start, stopindex="end", nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(q)}c"
            self.editor.tag_add("srch", pos, end)
            if cnt == 0:
                self.editor.see(pos)
            start = end
            cnt += 1
        self.toast.show(f"{cnt} match(es)", "info" if cnt else "warning", 2000)

    def _replace1(self):
        q, r = self.search_e.get(), self.replace_e.get()
        if not q:
            return
        pos = self.editor.search(q, "insert", stopindex="end", nocase=True)
        if pos:
            self.editor.delete(pos, f"{pos}+{len(q)}c")
            self.editor.insert(pos, r)
            self._sched_hl()

    def _replace_all(self):
        q, r = self.search_e.get(), self.replace_e.get()
        if not q:
            return
        txt = self.editor.get("1.0", "end-1c")
        new, n = re.subn(re.escape(q), r, txt, flags=re.IGNORECASE)
        if n:
            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", new)
            self._sched_hl()
            self.toast.show(f"Replaced {n}", "success")
        else:
            self.toast.show("No matches", "warning")

    def _load_to_editor(self, code, name=""):
        self._tabs[self._tab_idx].content = self.editor.get("1.0", "end-1c")
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", code.strip())
        self._tabs[self._tab_idx].name = name or "Loaded"
        self._tabs[self._tab_idx].modified = True
        self._refresh_tab_bar()
        self._sched_hl()
        self._upd_ln()
        self._nav("editor")
        self._save_tabs()
        self.toast.show(f"Loaded: {name}", "info")

    # ── SCRIPT HUB ───────────────────────────────────────────────────────────

    def _build_hub(self):
        p = self.pages["hub"]
        hdr = ctk.CTkFrame(p, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        ctk.CTkLabel(hdr, text="Script Hub", font=("Segoe UI", 20, "bold"),
                      text_color=C.T1).pack(side="left")
        ctk.CTkButton(hdr, text="  +  Add Script  ", width=130, height=32,
                       fg_color=C.GREEN_BRIGHT, hover_color="#00c060",
                       text_color="#000000", corner_radius=8,
                       font=("Segoe UI", 13, "bold"),
                       command=self._add_hub_script).pack(side="right")

        filt = ctk.CTkFrame(p, fg_color="transparent")
        filt.pack(fill="x", padx=24, pady=(0, 6))
        self.hub_search = ctk.StringVar()
        self.hub_search.trace_add("write", lambda *a: self._populate_hub())
        ctk.CTkEntry(filt, textvariable=self.hub_search, placeholder_text="Search...",
                      width=260, height=30, fg_color=C.BG7, border_color=C.BORDER,
                      text_color=C.T1).pack(side="left")
        self.hub_cat = ctk.StringVar(value="All")
        self.hub_cat_menu = ctk.CTkOptionMenu(filt, values=["All"], variable=self.hub_cat,
                                                width=110, height=30, fg_color=C.BG5,
                                                button_color=C.BG6, dropdown_fg_color=C.BG3,
                                                text_color=C.T1,
                                                command=lambda v: self._populate_hub())
        self.hub_cat_menu.pack(side="left", padx=8)
        self.hub_custom_only = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(filt, text="Custom Only", variable=self.hub_custom_only,
                         fg_color=C.T1, hover_color=C.ACCENT_HOVER,
                         checkmark_color=C.BG0,
                         border_color=C.BORDER, text_color=C.T2,
                         command=lambda: self._populate_hub()).pack(side="left", padx=8)

        self.hub_sc = ctk.CTkScrollableFrame(p, fg_color="transparent",
                                               scrollbar_button_color=C.SCROLL)
        self.hub_sc.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    def _populate_hub(self):
        for w in self.hub_sc.winfo_children():
            w.destroy()
        all_s = BUILTIN_HUB + self._custom_hub
        cats = sorted(set(s.get("category", "Other") for s in all_s))
        try:
            self.hub_cat_menu.configure(values=["All"] + cats)
        except Exception:
            pass
        search = self.hub_search.get().lower()
        cat = self.hub_cat.get()
        co = self.hub_custom_only.get()
        cnt = 0
        for s in all_s:
            if co and s.get("builtin"):
                continue
            if search and search not in s["name"].lower() and search not in s.get("desc", "").lower():
                continue
            if cat != "All" and s.get("category", "") != cat:
                continue
            is_c = not s.get("builtin", False)
            card = ctk.CTkFrame(self.hub_sc, fg_color=C.BG3, corner_radius=10, height=68)
            card.pack(fill="x", pady=3)
            card.pack_propagate(False)
            if is_c:
                ctk.CTkFrame(card, width=3, fg_color=C.PURPLE, corner_radius=0
                              ).pack(side="left", fill="y")
            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True, padx=12, pady=8)
            tr = ctk.CTkFrame(info, fg_color="transparent")
            tr.pack(fill="x")
            ctk.CTkLabel(tr, text=s["name"], font=("Segoe UI", 13, "bold"),
                          text_color=C.T1, anchor="w").pack(side="left")
            cb = C.BG6 if s.get("builtin") else C.PURPLE
            ctk.CTkLabel(tr, text=s.get("category", ""), font=("Segoe UI", 9),
                          text_color=C.T1, fg_color=cb, corner_radius=4,
                          width=55, height=16).pack(side="left", padx=8)
            if is_c:
                ctk.CTkLabel(tr, text="CUSTOM", font=("Segoe UI", 8, "bold"),
                              text_color=C.PURPLE).pack(side="left", padx=4)
            d = s.get("desc", "")
            if d:
                ctk.CTkLabel(info, text=d, font=("Segoe UI", 11),
                              text_color=C.T3, anchor="w").pack(fill="x")
            btns = ctk.CTkFrame(card, fg_color="transparent")
            btns.pack(side="right", padx=10)
            code = s["code"]
            name = s["name"]
            ctk.CTkButton(btns, text="▶", width=34, height=28,
                           fg_color=C.T1, hover_color=C.ACCENT_HOVER,
                           text_color=C.BG0, corner_radius=6, font=("Segoe UI", 14),
                           command=lambda c=code: self._exec_code(c, "hub")).pack(side="left", padx=2)
            ctk.CTkButton(btns, text="✎", width=34, height=28,
                           fg_color=C.BG5, hover_color=C.BG6,
                           text_color=C.T1, corner_radius=6,
                           command=lambda c=code, n=name: self._load_to_editor(c, n)).pack(side="left", padx=2)
            if is_c:
                sd = s
                ctk.CTkButton(btns, text="⚙", width=34, height=28,
                               fg_color=C.BG5, hover_color=C.ORANGE,
                               text_color=C.T1, corner_radius=6,
                               command=lambda d=sd: self._edit_hub(d)).pack(side="left", padx=2)
                ctk.CTkButton(btns, text="✕", width=34, height=28,
                               fg_color="transparent", hover_color=C.RED,
                               text_color=C.T3, corner_radius=6,
                               command=lambda d=sd: self._del_hub(d)).pack(side="left", padx=2)
            cnt += 1
        if cnt == 0:
            ctk.CTkLabel(self.hub_sc, text="No scripts found",
                          font=("Segoe UI", 13), text_color=C.T3).pack(pady=40)

    def _add_hub_script(self):
        try:
            AddScriptDialog(self, self._on_hub_save)
        except Exception as e:
            self._log(f"Failed to open dialog: {e}", "error")
            self.toast.show(f"Error: {e}", "error")

    def _on_hub_save(self, script, edit_data=None):
        try:
            if edit_data:
                self._custom_hub = [s for s in self._custom_hub
                                     if s.get("name") != edit_data.get("name")]
            self._custom_hub.append(script)
            CustomHubStore.save(self._custom_hub)
            self._populate_hub()
            action = "Updated" if edit_data else "Added"
            self._log(f"{action} custom script: {script['name']}", "system")
            self.toast.show(f"{action}: {script['name']}", "success")
        except Exception as e:
            self._log(f"Save script failed: {e}", "error")
            self.toast.show(f"Save failed: {e}", "error")

    def _edit_hub(self, sd):
        try:
            AddScriptDialog(self, self._on_hub_save, edit_data=sd)
        except Exception as e:
            self.toast.show(f"Error: {e}", "error")

    def _del_hub(self, sd):
        if messagebox.askyesno("Delete", f"Delete '{sd['name']}' from hub?"):
            self._custom_hub = [s for s in self._custom_hub if s.get("name") != sd.get("name")]
            CustomHubStore.save(self._custom_hub)
            self._populate_hub()
            self.toast.show(f"Deleted: {sd['name']}", "info")

    # ── CONSOLE ──────────────────────────────────────────────────────────────

    def _build_console(self):
        p = self.pages["console"]
        hdr = ctk.CTkFrame(p, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        ctk.CTkLabel(hdr, text="Console", font=("Segoe UI", 20, "bold"),
                      text_color=C.T1).pack(side="left")
        bf = ctk.CTkFrame(hdr, fg_color="transparent")
        bf.pack(side="right")
        for t, c in [("Clear", self._clear_con), ("Copy", self._copy_con), ("Export", self._export_con)]:
            ctk.CTkButton(bf, text=t, width=55, height=26, fg_color=C.BG5,
                           hover_color=C.BG6, text_color=C.T1, corner_radius=6,
                           command=c).pack(side="left", padx=2)

        cf = ctk.CTkFrame(p, fg_color=C.BG0, corner_radius=10)
        cf.pack(fill="both", expand=True, padx=20, pady=(0, 6))
        self.con = tk.Text(cf, bg=C.BG0, fg=C.T1, font=("Consolas", 11),
                            wrap="word", relief="flat", borderwidth=0, padx=10, pady=8,
                            insertbackground=C.T1, state="disabled",
                            selectbackground=C.BG5)
        csb = tk.Scrollbar(cf, command=self.con.yview, bg=C.BG1, troughcolor=C.BG0,
                            width=7, relief="flat", bd=0)
        csb.pack(side="right", fill="y", padx=(0, 3), pady=3)
        self.con.configure(yscrollcommand=csb.set)
        self.con.pack(fill="both", expand=True, padx=3, pady=3)
        self.con.tag_configure("info", foreground=C.T1)
        self.con.tag_configure("warn", foreground=C.ORANGE)
        self.con.tag_configure("error", foreground=C.RED)
        self.con.tag_configure("system", foreground=C.PURPLE)
        self.con.tag_configure("time", foreground=C.T4)

        inp = ctk.CTkFrame(p, fg_color=C.BG3, height=40, corner_radius=10)
        inp.pack(fill="x", padx=20, pady=(0, 10))
        inp.pack_propagate(False)
        ctk.CTkLabel(inp, text="›", font=("Consolas", 16, "bold"),
                      text_color=C.T1).pack(side="left", padx=(10, 4))
        self.cmd_e = ctk.CTkEntry(inp, placeholder_text="Execute Lua...",
                                   fg_color="transparent", border_width=0,
                                   text_color=C.T1, font=("Consolas", 12), height=30)
        self.cmd_e.pack(side="left", fill="both", expand=True, padx=4)
        self.cmd_e.bind("<Return>", self._exec_cmd)

    def _exec_cmd(self, e=None):
        code = self.cmd_e.get().strip()
        if code:
            self._log(f"› {code}", "info")
            self._exec_code(code, "console")
            self.cmd_e.delete(0, "end")

    # ── FILES ────────────────────────────────────────────────────────────────

    def _build_files(self):
        p = self.pages["files"]
        hdr = ctk.CTkFrame(p, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        ctk.CTkLabel(hdr, text="Scripts", font=("Segoe UI", 20, "bold"),
                      text_color=C.T1).pack(side="left")
        bf = ctk.CTkFrame(hdr, fg_color="transparent")
        bf.pack(side="right")
        ctk.CTkButton(bf, text="Open Folder", width=100, height=26, fg_color=C.BG5,
                       hover_color=C.BG6, text_color=C.T1, corner_radius=6,
                       command=self._open_scripts_dir).pack(side="left", padx=2)
        ctk.CTkButton(bf, text="Refresh", width=70, height=26, fg_color=C.BG5,
                       hover_color=C.BG6, text_color=C.T1, corner_radius=6,
                       command=self._refresh_files).pack(side="left", padx=2)
        self.files_sc = ctk.CTkScrollableFrame(p, fg_color="transparent",
                                                 scrollbar_button_color=C.SCROLL)
        self.files_sc.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    def _refresh_files(self):
        for w in self.files_sc.winfo_children():
            w.destroy()
        files = sorted(SCRIPTS_DIR.glob("*.lua")) + sorted(SCRIPTS_DIR.glob("*.txt"))
        if not files:
            ctk.CTkLabel(self.files_sc, text=f"No scripts found.\nSave .lua files to:\n{SCRIPTS_DIR}",
                          font=("Segoe UI", 12), text_color=C.T3).pack(pady=40)
            return
        for fp in files:
            row = ctk.CTkFrame(self.files_sc, fg_color=C.BG3, corner_radius=8, height=40)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=f"  {fp.name}", font=("Consolas", 12),
                          text_color=C.T1, anchor="w").pack(side="left", padx=6)
            ctk.CTkLabel(row, text=f"{fp.stat().st_size/1024:.1f}KB", font=("Consolas", 10),
                          text_color=C.T3).pack(side="left", padx=6)
            mt = datetime.datetime.fromtimestamp(fp.stat().st_mtime).strftime("%m/%d %H:%M")
            ctk.CTkLabel(row, text=mt, font=("Consolas", 10), text_color=C.T4).pack(side="left", padx=6)
            path = fp
            ctk.CTkButton(row, text="▶", width=28, height=24, fg_color=C.T1,
                           hover_color=C.ACCENT_HOVER, text_color=C.BG0, corner_radius=4,
                           command=lambda p=path: self._run_file(p)).pack(side="right", padx=2, pady=8)
            ctk.CTkButton(row, text="✎", width=28, height=24, fg_color=C.BG5,
                           hover_color=C.BG6, text_color=C.T1, corner_radius=4,
                           command=lambda p=path: self._edit_file(p)).pack(side="right", padx=2, pady=8)
            ctk.CTkButton(row, text="✕", width=28, height=24, fg_color="transparent",
                           hover_color=C.RED, text_color=C.T3, corner_radius=4,
                           command=lambda p=path: self._del_file(p)).pack(side="right", padx=2, pady=8)

    def _open_scripts_dir(self):
        if sys.platform == "win32":
            os.startfile(SCRIPTS_DIR)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(SCRIPTS_DIR)])
        else:
            subprocess.Popen(["xdg-open", str(SCRIPTS_DIR)])

    def _run_file(self, p):
        try:
            self._exec_code(p.read_text(encoding="utf-8"), "file")
        except Exception as e:
            self.toast.show(f"Error: {e}", "error")

    def _edit_file(self, p):
        try:
            self._load_to_editor(p.read_text(encoding="utf-8"), p.name)
        except Exception as e:
            self.toast.show(f"Error: {e}", "error")

    def _del_file(self, p):
        if messagebox.askyesno("Delete", f"Delete {p.name}?"):
            try:
                p.unlink()
                self._refresh_files()
                self.toast.show(f"Deleted {p.name}", "info")
            except Exception as e:
                self.toast.show(f"Error: {e}", "error")

    # ── HISTORY ──────────────────────────────────────────────────────────────

    def _build_history(self):
        p = self.pages["history"]
        hdr = ctk.CTkFrame(p, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        ctk.CTkLabel(hdr, text="Execution History", font=("Segoe UI", 20, "bold"),
                      text_color=C.T1).pack(side="left")
        ctk.CTkButton(hdr, text="Clear All", width=80, height=26, fg_color=C.BG5,
                       hover_color=C.RED, text_color=C.T1, corner_radius=6,
                       command=self._clear_hist).pack(side="right")
        self.hist_sc = ctk.CTkScrollableFrame(p, fg_color="transparent",
                                                scrollbar_button_color=C.SCROLL)
        self.hist_sc.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    def _refresh_history(self):
        for w in self.hist_sc.winfo_children():
            w.destroy()
        if not self.history.records:
            ctk.CTkLabel(self.hist_sc, text="No executions yet",
                          font=("Segoe UI", 12), text_color=C.T3).pack(pady=40)
            return
        for rec in reversed(self.history.records[-100:]):
            row = ctk.CTkFrame(self.hist_sc, fg_color=C.BG3, corner_radius=8, height=42)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)
            sc = {"queued": C.ORANGE, "success": C.T1, "error": C.RED}.get(
                rec.get("status", ""), C.T3)
            ctk.CTkFrame(row, width=3, fg_color=sc, corner_radius=1
                          ).pack(side="left", fill="y", padx=(5, 7), pady=7)
            inf = ctk.CTkFrame(row, fg_color="transparent")
            inf.pack(side="left", fill="both", expand=True, pady=5)
            ctk.CTkLabel(inf, text=rec.get("snippet", "")[:75],
                          font=("Consolas", 11), text_color=C.T1, anchor="w").pack(fill="x")
            target = rec.get("target", "all")
            meta = f"{rec.get('time', '')}  •  {rec.get('source', '')}  •  →{target}  •  {rec.get('chars', 0)} chars"
            ctk.CTkLabel(inf, text=meta, font=("Segoe UI", 9),
                          text_color=C.T4, anchor="w").pack(fill="x")

    def _clear_hist(self):
        if messagebox.askyesno("Clear", "Clear all history?"):
            self.history.clear()
            self._refresh_history()

    # ── INSTANCES PAGE ───────────────────────────────────────────────────────

    def _build_instances(self):
        p = self.pages["instances"]
        hdr = ctk.CTkFrame(p, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        ctk.CTkLabel(hdr, text="Connected Instances", font=("Segoe UI", 20, "bold"),
                      text_color=C.T1).pack(side="left")
        ctk.CTkButton(hdr, text="Refresh", width=80, height=26, fg_color=C.BG5,
                       hover_color=C.BG6, text_color=C.T1, corner_radius=6,
                       command=self._refresh_instances).pack(side="right")

        self.inst_sc = ctk.CTkScrollableFrame(p, fg_color="transparent",
                                                scrollbar_button_color=C.SCROLL)
        self.inst_sc.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    def _refresh_instances(self):
        for w in self.inst_sc.winfo_children():
            w.destroy()

        instances = sorted(self.instances.alive_instances(), key=lambda i: i.number)

        if not instances:
            ctk.CTkLabel(
                self.inst_sc,
                text="No connected instances.\n\n"
                     "Launch Roblox → the bridge listener will connect and appear here.\n"
                     "Each Roblox window gets its own instance.\n\n"
                     "Older listeners (v4.x) will not show up here but still receive scripts.",
                font=("Segoe UI", 12), text_color=C.T3, justify="center"
            ).pack(pady=40)
            return

        for inst in instances:
            card = ctk.CTkFrame(self.inst_sc, fg_color=C.BG3, corner_radius=10)
            card.pack(fill="x", pady=4)

            hdr = ctk.CTkFrame(card, fg_color="transparent")
            hdr.pack(fill="x", padx=14, pady=(10, 4))

            ctk.CTkLabel(hdr, text=inst.display_name,
                          font=("Segoe UI", 14, "bold"),
                          text_color=C.T1).pack(side="left")
            ctk.CTkLabel(hdr, text=f"ID: {inst.short_id}",
                          font=("Consolas", 10),
                          text_color=C.T4).pack(side="left", padx=8)

            age = time.time() - inst.last_ping
            age_txt = f"{int(age)}s ago"
            age_col = C.T1 if age < 6 else (C.ORANGE if age < 12 else C.RED)
            ctk.CTkLabel(hdr, text=f"Last ping: {age_txt}",
                          font=("Consolas", 10),
                          text_color=age_col).pack(side="right")

            gi = inst.game_info
            if gi:
                info_grid = ctk.CTkFrame(card, fg_color="transparent")
                info_grid.pack(fill="x", padx=14, pady=(0, 6))
                rows = [
                    ("Player", gi.get("player", "?")),
                    ("Display", gi.get("displayName", "?")),
                    ("Game", gi.get("placeName", "?")),
                    ("PlaceId", str(gi.get("placeId", "?"))),
                ]
                for label, val in rows:
                    r = ctk.CTkFrame(info_grid, fg_color="transparent")
                    r.pack(fill="x", pady=1)
                    ctk.CTkLabel(r, text=f"{label}:", width=80,
                                  font=("Segoe UI", 11),
                                  text_color=C.T3, anchor="w").pack(side="left")
                    ctk.CTkLabel(r, text=val, font=("Segoe UI", 11),
                                  text_color=C.T2, anchor="w").pack(side="left")
            else:
                ctk.CTkLabel(card, text="  (no game info yet)",
                              font=("Segoe UI", 11), text_color=C.T3,
                              anchor="w").pack(fill="x", padx=14, pady=(0, 6))

            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.pack(fill="x", padx=14, pady=(4, 10))

            iid = inst.id
            n = inst.number
            ctk.CTkButton(actions, text=f"Target this instance",
                           width=170, height=28,
                           fg_color=C.BG5, hover_color=C.T1,
                           text_color=C.T1, corner_radius=6,
                           command=lambda i=iid, nn=n: self._target_specific(i, nn)
                           ).pack(side="left", padx=(0, 5))

            ctk.CTkButton(actions, text="Run editor here",
                           width=140, height=28,
                           fg_color=C.T1, hover_color=C.ACCENT_HOVER,
                           text_color=C.BG0, corner_radius=6,
                           command=lambda i=iid: self._exec_to_instance(i)
                           ).pack(side="left", padx=3)

            q = inst.queue.qsize()
            ctk.CTkLabel(actions, text=f"Queue: {q}",
                          font=("Consolas", 10),
                          text_color=C.T3).pack(side="right")

        if self._page == "instances":
            self.after(2000, lambda: self._page == "instances" and self._refresh_instances())

    def _target_specific(self, instance_id: str, num: int):
        self._target_instance = instance_id
        self.target_var.set(f"Instance {num}")
        self._refresh_target_menu()
        self.toast.show(f"Now targeting Instance {num}", "success", 2000)
        self._nav("editor")

    def _exec_to_instance(self, instance_id: str):
        code = self.editor.get("1.0", "end-1c").strip()
        if not code:
            self.toast.show("Editor is empty", "warning")
            return
        saved_target = self._target_instance
        self._target_instance = instance_id
        self._exec_code(code, "editor")
        self._target_instance = saved_target

    # ── BRIDGE SETUP ─────────────────────────────────────────────────────────

    def _build_bridge(self):
        p = self.pages["bridge"]
        ctk.CTkLabel(p, text="Bridge Setup", font=("Segoe UI", 20, "bold"),
                      text_color=C.T1, anchor="w").pack(fill="x", padx=24, pady=(20, 8))
        self.bridge_sc = ctk.CTkScrollableFrame(p, fg_color="transparent",
                                                  scrollbar_button_color=C.SCROLL)
        self.bridge_sc.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    def _detect_autoexec(self) -> Optional[Path]:
        if self.settings.autoexec_path:
            p = Path(self.settings.autoexec_path)
            if p.is_dir():
                return p
        for h in POTASSIUM_HINTS:
            if h.is_dir():
                return h
        return None

    def _listener_ver(self, folder: Path) -> Optional[str]:
        f = folder / "bridge_listener.lua"
        if not f.exists():
            return None
        try:
            head = f.read_text(encoding="utf-8", errors="ignore")[:400]
            m = re.search(r"Bridge Listener v([\d.]+)", head)
            return m.group(1) if m else "unknown"
        except Exception:
            return "unreadable"

    def _listener_src(self) -> str:
        return BRIDGE_LISTENER_SOURCE.format(port=self.settings.bridge_port)

    def _refresh_bridge(self):
        for w in self.bridge_sc.winfo_children():
            w.destroy()
        folder = self._detect_autoexec()

        c1 = self._card(self.bridge_sc, "autoexec Location")
        self._crow_val(c1, "Detected", str(folder) if folder else "Not found",
                        C.T1 if folder else C.RED)
        bf = ctk.CTkFrame(c1, fg_color="transparent")
        bf.pack(fill="x", padx=16, pady=(4, 12))
        ctk.CTkButton(bf, text="Browse...", width=90, height=28, fg_color=C.BG5,
                       hover_color=C.BG6, text_color=C.T1, corner_radius=6,
                       command=self._pick_autoexec).pack(side="left")

        c2 = self._card(self.bridge_sc, "Listener Status")
        installed = self._listener_ver(folder) if folder else None
        self._crow_val(c2, "Installed", installed or "Not installed",
                        C.T1 if installed == BRIDGE_LISTENER_VERSION
                        else (C.ORANGE if installed else C.RED))
        self._crow_val(c2, "Expected", BRIDGE_LISTENER_VERSION, C.T2)
        self._crow_val(c2, "Port", str(self.settings.bridge_port), C.T2)
        if installed and installed != BRIDGE_LISTENER_VERSION:
            ctk.CTkLabel(c2, text="  ⚠ Version mismatch — click Install to update",
                          font=("Segoe UI", 11), text_color=C.ORANGE,
                          anchor="w").pack(fill="x", padx=16, pady=(2, 0))
        af = ctk.CTkFrame(c2, fg_color="transparent")
        af.pack(fill="x", padx=16, pady=(8, 12))
        ctk.CTkButton(af, text="Install / Update", width=140, height=32,
                       fg_color=C.T1, hover_color=C.ACCENT_HOVER,
                       text_color=C.BG0, corner_radius=6, font=("Segoe UI", 12, "bold"),
                       command=self._install_listener).pack(side="left", padx=(0, 6))
        ctk.CTkButton(af, text="Copy Source", width=100, height=32,
                       fg_color=C.BG5, hover_color=C.BG6, text_color=C.T1,
                       corner_radius=6, command=self._copy_listener).pack(side="left", padx=3)
        ctk.CTkButton(af, text="Remove", width=80, height=32,
                       fg_color=C.BG5, hover_color=C.RED, text_color=C.T1,
                       corner_radius=6, command=self._remove_listener).pack(side="left", padx=3)

        c3 = self._card(self.bridge_sc, "Live Connection")
        n_inst = len(self.instances.alive_instances())
        self._crow_val(c3, "HTTP Server",
                        f"Listening :{self.settings.bridge_port}" if self.server and self.server.running else "Stopped",
                        C.T1 if self.server and self.server.running else C.RED)
        self._crow_val(c3, "Connected instances", str(n_inst),
                        C.T1 if n_inst else C.ORANGE)
        self._crow_val(c3, "Roblox process",
                        "Running" if self.roblox_attached else "Not running",
                        C.T1 if self.roblox_attached else C.RED)
        ctk.CTkFrame(c3, height=8, fg_color="transparent").pack()

    def _pick_autoexec(self):
        d = filedialog.askdirectory(title="Select autoexec folder")
        if d:
            self.settings.autoexec_path = d
            self.settings.save()
            self._refresh_bridge()
            self.toast.show("Path saved", "success")

    def _install_listener(self):
        folder = self._detect_autoexec()
        if not folder:
            self.toast.show("Set autoexec folder first", "warning")
            return
        try:
            (folder / "bridge_listener.lua").write_text(self._listener_src(), encoding="utf-8")
            self._log(f"Listener v{BRIDGE_LISTENER_VERSION} installed to {folder}", "system")
            self.toast.show("Installed — rejoin game to load", "success", 4000)
            self._refresh_bridge()
        except Exception as e:
            self.toast.show(f"Failed: {e}", "error", 5000)

    def _copy_listener(self):
        self.clipboard_clear()
        self.clipboard_append(self._listener_src())
        self.toast.show("Source copied", "success")

    def _remove_listener(self):
        folder = self._detect_autoexec()
        if not folder:
            return
        f = folder / "bridge_listener.lua"
        if f.exists() and messagebox.askyesno("Remove", f"Delete {f.name}?"):
            try:
                f.unlink()
                self._refresh_bridge()
                self.toast.show("Removed", "info")
            except Exception as e:
                self.toast.show(f"Error: {e}", "error")

    def _open_autoexec_folder(self):
        folder = self._detect_autoexec()
        if not folder:
            self.toast.show("Set autoexec path in Bridge Setup", "warning")
            self._nav("bridge")
            return
        if sys.platform == "win32":
            os.startfile(folder)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)])

    def _kill_roblox(self):
        if not HAS_PSUTIL:
            self.toast.show("psutil required", "warning")
            return
        if not messagebox.askyesno("Kill Roblox", "Force-close all Roblox processes?"):
            return
        n = 0
        for proc in psutil.process_iter(["name"]):
            if proc.info["name"] in ROBLOX_PROCESSES:
                try:
                    proc.kill()
                    n += 1
                except Exception:
                    pass
        self._log(f"Killed {n} process(es)", "warn")
        self.toast.show(f"Killed {n} process(es)", "info")

    # ── SETTINGS ─────────────────────────────────────────────────────────────

    def _build_settings(self):
        p = self.pages["settings"]
        ctk.CTkLabel(p, text="Settings", font=("Segoe UI", 20, "bold"),
                      text_color=C.T1, anchor="w").pack(fill="x", padx=24, pady=(20, 8))
        sc = ctk.CTkScrollableFrame(p, fg_color="transparent", scrollbar_button_color=C.SCROLL)
        sc.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Profile
        s1 = self._scard(sc, "Profile")
        self._slabel(s1, "Username")
        self.uname_e = ctk.CTkEntry(s1, fg_color=C.BG7, border_color=C.BORDER,
                                     text_color=C.T1, height=30)
        self.uname_e.insert(0, self.settings.username)
        self.uname_e.pack(fill="x", pady=(2, 8))
        self.uname_e.bind("<FocusOut>", lambda e: self._save_profile())
        self.uname_e.bind("<Return>", lambda e: self._save_profile())

        # Appearance
        s_theme = self._scard(sc, "Appearance")
        self._slabel(s_theme, "Theme")
        theme_var = ctk.StringVar(value=self.settings.theme)
        ctk.CTkOptionMenu(
            s_theme, values=list(THEMES.keys()), variable=theme_var,
            fg_color=C.BG5, button_color=C.BG6, dropdown_fg_color=C.BG3,
            text_color=C.T1, font=("Segoe UI", 12), height=32,
            command=lambda v: self._apply_theme(v)
        ).pack(fill="x", pady=(2, 10))
        ctk.CTkLabel(s_theme, text="Changing theme rebuilds the UI. Your tabs and settings are preserved.",
                      font=("Segoe UI", 10), text_color=C.T3, wraplength=500,
                      justify="left").pack(anchor="w", pady=(0, 4))

        # Community Links (read-only display)
        s_links = self._scard(sc, "Community Links")
        self._link_st = ctk.CTkLabel(s_links, text="", font=("Consolas", 10),
                                      text_color=C.T3, anchor="w")
        self._link_st.pack(fill="x", pady=(0, 4))
        self._link_d = ctk.CTkLabel(s_links, text="", font=("Consolas", 11),
                                     text_color=C.T2, anchor="w")
        self._link_d.pack(fill="x", pady=1)
        self._link_w = ctk.CTkLabel(s_links, text="", font=("Consolas", 11),
                                     text_color=C.T2, anchor="w")
        self._link_w.pack(fill="x", pady=1)
        lbf = ctk.CTkFrame(s_links, fg_color="transparent")
        lbf.pack(fill="x", pady=(8, 0))
        ctk.CTkButton(lbf, text="Refresh", width=80, height=26, fg_color=C.BG5,
                       hover_color=C.BG6, text_color=C.T1, corner_radius=6,
                       command=self._refresh_links).pack(side="left", padx=(0, 4))
        self._render_links()

        # Editor
        s2 = self._scard(sc, "Editor")
        self._slabel(s2, f"Font Size: {self.settings.font_size}")
        self._font_lbl = s2.winfo_children()[-1]
        fs = ctk.CTkSlider(s2, from_=10, to=24, number_of_steps=14,
                            fg_color=C.BG7, progress_color=C.T1,
                            button_color=C.T1, button_hover_color=C.ACCENT_HOVER,
                            command=self._set_font)
        fs.set(self.settings.font_size)
        fs.pack(fill="x", pady=(2, 10))
        for text, attr, default in [
            ("Word Wrap", "wrap_text", self.settings.wrap_text),
            ("Line Numbers", "line_numbers", self.settings.line_numbers),
            ("Confirm Before Execute", "confirm_exec", self.settings.confirm_exec),
            ("Auto-Clear After Execute", "auto_clear", self.settings.auto_clear),
        ]:
            var = ctk.BooleanVar(value=default)
            ctk.CTkCheckBox(s2, text=text, variable=var,
                             fg_color=C.T1, hover_color=C.ACCENT_HOVER,
                             checkmark_color=C.BG0,
                             border_color=C.BORDER, text_color=C.T1, font=("Segoe UI", 12),
                             command=lambda v=var, a=attr: self._set_toggle(a, v.get())
                             ).pack(anchor="w", pady=3)

        # Window
        s3 = self._scard(sc, "Window")
        tv = ctk.BooleanVar(value=self.settings.topmost)
        ctk.CTkCheckBox(s3, text="Always on Top", variable=tv,
                         fg_color=C.T1, hover_color=C.ACCENT_HOVER,
                         checkmark_color=C.BG0,
                         border_color=C.BORDER, text_color=C.T1,
                         command=lambda: self._set_topmost(tv.get())).pack(anchor="w", pady=3)
        self._slabel(s3, f"Opacity: {int(self.settings.opacity*100)}%")
        self._op_lbl = s3.winfo_children()[-1]
        op = ctk.CTkSlider(s3, from_=0.5, to=1.0, number_of_steps=10,
                            fg_color=C.BG7, progress_color=C.T1,
                            button_color=C.T1, command=self._set_opacity)
        op.set(self.settings.opacity)
        op.pack(fill="x", pady=(2, 8))

        # Info
        s4 = self._scard(sc, "Info")
        ctk.CTkLabel(s4, text=f"Server: {BRIDGE_URL}", font=("Consolas", 11),
                      text_color=C.T2).pack(anchor="w")
        ctk.CTkLabel(s4, text=f"Scripts: {SCRIPTS_DIR}", font=("Consolas", 10),
                      text_color=C.T3).pack(anchor="w", pady=(3, 0))
        ctk.CTkLabel(s4, text=f"Config: {CONFIG_DIR}", font=("Consolas", 10),
                      text_color=C.T4).pack(anchor="w", pady=(2, 0))

        # Shortcuts
        s5 = self._scard(sc, "Keyboard Shortcuts")
        for s in ["Ctrl+Enter / F5 — Execute", "Ctrl+S — Save", "Ctrl+O — Open",
                   "Ctrl+N — New Tab", "Ctrl+W — Close Tab",
                   "Ctrl+F — Find/Replace", "Ctrl+L — Clear Editor",
                   "Drag editor tabs to reorder"]:
            ctk.CTkLabel(s5, text=s, font=("Consolas", 10), text_color=C.T3).pack(anchor="w", pady=1)

        # About
        s6 = self._scard(sc, "About")
        ctk.CTkLabel(s6, text=f"◆ {APP_NAME} v{APP_VERSION}",
                      font=("Segoe UI", 16, "bold"), text_color=C.T1).pack(anchor="w")
        ctk.CTkLabel(s6, text="Professional Executor & HTTP Bridge",
                      font=("Segoe UI", 11), text_color=C.T3).pack(anchor="w", pady=(2, 0))

    def _scard(self, parent, title):
        c = ctk.CTkFrame(parent, fg_color=C.BG3, corner_radius=12)
        c.pack(fill="x", pady=4)
        ctk.CTkLabel(c, text=title, font=("Segoe UI", 13, "bold"),
                      text_color=C.T1).pack(anchor="w", padx=14, pady=(12, 4))
        inner = ctk.CTkFrame(c, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=(0, 12))
        return inner

    def _slabel(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=("Segoe UI", 11),
                      text_color=C.T3).pack(anchor="w")

    def _save_profile(self):
        self.settings.username = self.uname_e.get().strip() or "User"
        self.settings.save()

    def _render_links(self):
        rl = self.remote_links
        if rl.last_fetch:
            age = int(time.time() - rl.last_fetch)
            st = f"Synced {age}s ago"
        else:
            st = "Never synced"
        if rl.last_error:
            st += f"  •  {rl.last_error}"
        self._link_st.configure(text=st)
        self._link_d.configure(text=f"Discord:  {rl.discord or '(not set)'}")
        self._link_w.configure(text=f"Website:  {rl.website or '(not set)'}")

    def _refresh_links(self):
        self.toast.show("Refreshing...", "info", 1200)
        def done(ok):
            self.after(0, self._render_links)
            self.after(0, lambda: self.toast.show(
                "Links refreshed" if ok else f"Failed: {self.remote_links.last_error}",
                "success" if ok else "error"))
        self.remote_links.fetch_async(done)

    def _set_font(self, val):
        sz = int(val)
        self.settings.font_size = sz
        self.settings.save()
        self.editor.configure(font=(self.settings.font_family, sz))
        self._font_lbl.configure(text=f"Font Size: {sz}")
        self._upd_ln()

    def _set_toggle(self, attr, val):
        setattr(self.settings, attr, val)
        self.settings.save()
        if attr == "wrap_text":
            self.editor.configure(wrap="word" if val else "none")
        elif attr == "line_numbers":
            if val:
                self.ln.pack(side="left", fill="y", before=self.editor)
                self._upd_ln()
            else:
                self.ln.pack_forget()

    def _set_topmost(self, val):
        self.settings.topmost = val
        self.settings.save()
        self.attributes("-topmost", val)

    def _set_opacity(self, val):
        self.settings.opacity = round(val, 2)
        self.settings.save()
        self.attributes("-alpha", val)
        self._op_lbl.configure(text=f"Opacity: {int(val*100)}%")

    # ── STATUS BAR ───────────────────────────────────────────────────────────

    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, fg_color=C.BG_TOPBAR, height=24, corner_radius=0)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self.st_rbx = StatusDot(bar, "Roblox: Scanning", C.ORANGE)
        self.st_rbx.pack(side="left", padx=(10, 14))
        self.st_br = StatusDot(bar, "Bridge: 0 clients", C.ORANGE)
        self.st_br.pack(side="left", padx=(0, 14))
        self.st_sv = StatusDot(bar, "Server: Starting", C.ORANGE)
        self.st_sv.pack(side="left")
        self.exec_lbl = ctk.CTkLabel(bar, text=f"Execs: {len(self.history.records)}",
                                      font=("Consolas", 10), text_color=C.T3)
        self.exec_lbl.pack(side="right", padx=10)

    # ══════════════════════════════════════════════════════════════════════════
    #  EXECUTION
    # ══════════════════════════════════════════════════════════════════════════

    def _exec(self):
        code = self.editor.get("1.0", "end-1c").strip()
        if not code:
            self.toast.show("Editor is empty", "warning")
            return
        self._exec_code(code, "editor")

    def _exec_code(self, code, source="editor"):
        code = code.strip()
        if not code:
            return
        if self.settings.confirm_exec:
            if not messagebox.askyesno("Confirm", "Execute?"):
                return

        target = self._target_instance
        target_label = "all"
        if target != "all":
            for inst in self.instances.alive_instances():
                if inst.id == target:
                    target_label = inst.display_name
                    break

        self.instances.enqueue(code, target)
        self.q_lbl.configure(text=f"Queue: {self.instances.total_queue_size()}")
        self.history.add(code, "queued", source, target_label)
        self._log(f"Queued ({source}) → {target_label}: {code[:55]}...", "system")
        self.toast.show(f"Queued → {target_label}", "success", 1500)
        self.exec_lbl.configure(text=f"Execs: {len(self.history.records)}")
        if self.settings.auto_clear and source == "editor":
            self._clear_editor()

    # ── FILE OPS ─────────────────────────────────────────────────────────────

    def _open_file(self):
        path = filedialog.askopenfilename(
            initialdir=self.settings.last_dir or str(SCRIPTS_DIR),
            filetypes=[("Lua", "*.lua"), ("Text", "*.txt"), ("All", "*.*")])
        if path:
            try:
                code = Path(path).read_text(encoding="utf-8")
                self._load_to_editor(code, Path(path).name)
                self._tabs[self._tab_idx].filepath = path
                self.settings.last_dir = str(Path(path).parent)
                if path not in self.settings.recent_files:
                    self.settings.recent_files.insert(0, path)
                    self.settings.recent_files = self.settings.recent_files[:20]
                self.settings.save()
                self._save_tabs()
            except Exception as e:
                self.toast.show(f"Error: {e}", "error")

    def _save_file(self):
        code = self.editor.get("1.0", "end-1c")
        if not code.strip():
            self.toast.show("Nothing to save", "warning")
            return
        tab = self._tabs[self._tab_idx]
        if tab.filepath:
            try:
                Path(tab.filepath).write_text(code, encoding="utf-8")
                tab.modified = False
                self._refresh_tab_bar()
                self._save_tabs()
                self.toast.show(f"Saved {Path(tab.filepath).name}", "success")
                return
            except Exception:
                pass
        path = filedialog.asksaveasfilename(
            initialdir=str(SCRIPTS_DIR), defaultextension=".lua",
            filetypes=[("Lua", "*.lua"), ("Text", "*.txt")])
        if path:
            try:
                Path(path).write_text(code, encoding="utf-8")
                tab.filepath = path
                tab.name = Path(path).name
                tab.modified = False
                self._refresh_tab_bar()
                self._save_tabs()
                self.toast.show(f"Saved {Path(path).name}", "success")
            except Exception as e:
                self.toast.show(f"Error: {e}", "error")

    # ── CONSOLE ──────────────────────────────────────────────────────────────

    def _log(self, msg, tag="info"):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        logger.info(msg)

        def _do():
            try:
                self.con.configure(state="normal")
                self.con.insert("end", f"[{ts}] ", "time")
                self.con.insert("end", f"{msg}\n", tag)
                lines = int(self.con.index("end-1c").split(".")[0])
                if lines > MAX_CONSOLE:
                    self.con.delete("1.0", f"{lines - MAX_CONSOLE}.0")
                self.con.see("end")
                self.con.configure(state="disabled")
            except Exception:
                pass

        self.after(0, _do)

    def _clear_con(self):
        self.con.configure(state="normal")
        self.con.delete("1.0", "end")
        self.con.configure(state="disabled")

    def _copy_con(self):
        self.con.configure(state="normal")
        t = self.con.get("1.0", "end-1c")
        self.con.configure(state="disabled")
        self.clipboard_clear()
        self.clipboard_append(t)
        self.toast.show("Copied!", "success")

    def _export_con(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                             filetypes=[("Text", "*.txt"), ("Log", "*.log")])
        if path:
            self.con.configure(state="normal")
            t = self.con.get("1.0", "end-1c")
            self.con.configure(state="disabled")
            Path(path).write_text(t, encoding="utf-8")
            self.toast.show("Exported!", "success")

    # ── BRIDGE ───────────────────────────────────────────────────────────────

    def _start_server(self):
        self.server = BridgeServer(self, BRIDGE_HOST, self.settings.bridge_port)
        if self.server.start():
            self.st_sv.set(f"Server: :{self.settings.bridge_port}", C.T1)
            self._log(f"Server on :{self.settings.bridge_port}", "system")
        else:
            self.st_sv.set("Server: FAILED", C.RED)
            self._log("Server failed — port in use?", "error")
            self.toast.show("Server failed!", "error", 5000)

    def on_ping(self, instance_id: Optional[str]):
        self.last_ping = time.time()
        if not self.bridge_connected:
            self.bridge_connected = True
            self.after(0, lambda: self._log("First bridge connection", "system"))
            self.after(0, lambda: self.toast.show("Bridge connected ✓", "success"))
        self.after(0, self._update_bridge_status)
        self.after(0, self._refresh_target_menu)

    def _update_bridge_status(self):
        n = len(self.instances.alive_instances())
        if n == 0:
            self.st_br.set("Bridge: Waiting", C.ORANGE)
        elif n == 1:
            self.st_br.set("Bridge: 1 client", C.T1)
        else:
            self.st_br.set(f"Bridge: {n} clients", C.T1)

    def on_callback(self, data):
        s = data.get("status", "?")
        m = data.get("message", "")
        iid = data.get("instance_id", "?")
        short = iid[:6] if iid else "?"
        t = "info" if s == "success" else "error"
        self.after(0, lambda: self._log(f"[{short}] {s}: {m}", t))
        if s == "error":
            self.after(0, lambda: self.toast.show(f"Error: {m[:50]}", "error", 4000))

    def on_remote_console(self, data):
        msg = data.get("message", "")
        lvl = data.get("level", "info")
        iid = data.get("instance_id", "?")
        short = iid[:6] if iid else "?"
        tag = {"print": "info", "warn": "warn", "error": "error"}.get(lvl, "info")
        self.after(0, lambda: self._log(f"[{short}] {msg}", tag))

    def on_game_info(self, data):
        self._game_info = data
        iid = data.get("instance_id", "?")
        self.after(0, lambda: self._log(
            f"Game info [{iid[:6]}]: {data.get('placeName', '?')} as {data.get('player', '?')}",
            "system"
        ))
        self.after(0, self._refresh_target_menu)

    def _bridge_monitor(self):
        def chk():
            if self._shutdown:
                return
            n = len(self.instances.alive_instances())
            if self.bridge_connected and n == 0:
                self.bridge_connected = False
                self.st_br.set("Bridge: Waiting", C.ORANGE)
            self.after(3000, chk)
        self.after(3000, chk)

    def _instance_cleanup_loop(self):
        def cleanup():
            if self._shutdown:
                return
            removed = self.instances.cleanup_stale()
            if removed:
                self._log(f"Removed {removed} stale instance(s)", "system")
                self._update_bridge_status()
                self._refresh_target_menu()
                if self._page == "instances":
                    self._refresh_instances()
            self.after(5000, cleanup)
        self.after(5000, cleanup)

    def _proc_monitor(self):
        if not HAS_PSUTIL:
            self.st_rbx.set("Roblox: psutil missing", C.T3)
            return

        def chk():
            if self._shutdown:
                return
            found = False
            try:
                for p in psutil.process_iter(["name"]):
                    if p.info["name"] in ROBLOX_PROCESSES:
                        found = True
                        break
            except Exception:
                pass
            was = self.roblox_attached
            self.roblox_attached = found
            if found and not was:
                self.st_rbx.set("Roblox: Attached ✓", C.T1)
                self._log("Roblox detected", "system")
            elif not found and was:
                self.st_rbx.set("Roblox: Detached", C.RED)
                self._log("Roblox lost", "warn")
            elif not found:
                self.st_rbx.set("Roblox: Not Found", C.RED)
            self.after(3000, chk)
        self.after(1000, chk)

    # ── SHUTDOWN ─────────────────────────────────────────────────────────────

    def _quit(self):
        self._shutdown = True
        self._tabs[self._tab_idx].content = self.editor.get("1.0", "end-1c")
        TabStore.save(self._tabs, self._tab_idx)
        CustomHubStore.save(self._custom_hub)
        self.settings.win_w = self.winfo_width()
        self.settings.win_h = self.winfo_height()
        self.settings.win_x = self.winfo_x()
        self.settings.win_y = self.winfo_y()
        self.settings.save()
        if self.server:
            self.server.stop()
        logger.info("Shutdown")
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = VevoxApp()
    app.mainloop()