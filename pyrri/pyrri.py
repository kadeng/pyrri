import time
import signal
from dataclasses import dataclass
from enum import StrEnum, auto
from pathlib import Path
from collections import namedtuple
from time import process_time_ns

from win32.lib import win32con

from pyrri.time_utils import get_current_time_info
from pyrri.winproc.core import get_active_window_info, browser_force_navigate, send_key, terminate_process, \
    minimize_window, set_shutdown_handler, is_session_locked
from pyrri.configuration import Configuration, RestrictionAction

ProcessInfo = namedtuple('ProcessInfo', ['title', 'exe_name', 'pid', 'hwnd'])

class Pyrri:

    def __init__(self, logfile, config_url=None, config_file=None , silent=True):
        self.logfile = logfile
        self.stopped = False
        self.last_pinfo = None
        self.config = None
        self.config_url = config_url
        self.config_file = config_file
        self.last_config_update = 0
        self.silent = silent
        
        self.update_config()

    def log(self, msg):
        if not self.silent:
            print(msg)
        with open(self.logfile, mode='at', encoding="utf-8") as fh:
            print(msg, file=fh)

    def update_config(self):
        try:
            if self.config_url:
                self.log(f"Updating configuration from {self.config_url}")
                self.config = Configuration.load_from_url(self.config_url)
                self.last_config_update = time.time()
            elif self.config_file and self.config_file.exists():
                self.log(f"Loading configuration from {self.config_file}")
                self.config = Configuration.load_from_file(self.config_file)
                self.last_config_update = time.time()
            else:
                self.log("No configuration source available.")
        except Exception as e:
            self.log(f"ERROR: Failed to update configuration: {e}")

    def is_restricted_time(self):
        if not self.config.enabled:
            return False
        day, hour, minute = get_current_time_info()
        
        if self.config and self.config.unrestricted_times:
            # If we have a config, check if we are in an unrestricted timespan
            if self.config.unrestricted_times.is_in_timespan(day, hour, minute):
                return False
            return True
            
        # Fallback to hardcoded logic if no config
        # Weekends
        if day>=5:
            return hour>=21 or hour<10
        # Mondays, Tuesdays
        if day in (0,1):
            return True
        if day in (2,3,4):
            return hour<=16 or hour>=20

    def process_guard(self):
        if is_session_locked():
            return
            
        raw_pinfo = get_active_window_info()
        # Handle case where no window is active
        if not raw_pinfo or raw_pinfo[0] is None:
            return
            
        pinfo = ProcessInfo(*raw_pinfo)

        day, hour, minute = get_current_time_info()
        title, exe_name, pid, hwnd = pinfo
        
        if pinfo != self.last_pinfo:
            self.log(f"ACTIVE[{day=} {hour=} {minute=}] {exe_name=} - {title=}")
        self.last_pinfo = pinfo

        if self.config:
            # Use configuration rules
            for rule in self.config.rules:
                match_proc = True
                match_title = True
                
                if rule.process_regex:
                    if not exe_name or not rule.process_regex.search(exe_name):
                        match_proc = False
                
                if rule.title_regex:
                    if not title or not rule.title_regex.search(title):
                        match_title = False
                        
                if match_proc and match_title:
                    self.restriction_action(pinfo, rule.action)
                    # We only apply the first matching rule
                    break
        else:
            # Fallback to hardcoded logic
            if 'chrome' in exe_name:
                if 'Minecraft' in title or 'GeForce NOW' in title:
                    self.restriction_action(pinfo, RestrictionAction.FORCE_NAVIGATE_WIKIPEDIA)
            if 'firefox' in exe_name or 'iexplore' in exe_name or 'edge' in exe_name or 'opera' in exe_name:
                self.restriction_action(pinfo, RestrictionAction.TERMINATE)
            if exe_name == 'Minecraft.exe':
                self.log("ACTION: Minimizing Minecraft Launcher")
                self.restriction_action(pinfo, RestrictionAction.MINIMIZE)
            if 'java' in exe_name and 'Minecraft' in title:
                self.log("ACTION: Minimizing Minecraft")
                self.restriction_action(pinfo, RestrictionAction.MINIMIZE)
            if exe_name == 'steamwebhelper.exe':
                self.log("ACTION: Minimizing Steam")
                self.restriction_action(pinfo, RestrictionAction.MINIMIZE)
            if exe_name == 'WindowsTerminal.exe':
                self.log("ACTION: Minimizing Terminal")
                self.restriction_action(pinfo, RestrictionAction.MINIMIZE)

    def install_signal_handlers(self):
        """
        Installs signal handlers to ignore termination signals.
        """

        # Standard signals
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

        # Windows specific: SIGBREAK (Ctrl+Break)
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, signal.SIG_IGN)
        if hasattr(signal, 'SIGSTOP'):
            signal.signal(signal.SIGSTOP, signal.SIG_IGN)

    def run(self):
        while not self.stopped:
            # Refresh config every hour if URL is set
            if self.config_url and (time.time() - self.last_config_update > 1200):
                self.update_config()

            if self.is_restricted_time():
                self.process_guard()
                time.sleep(4.0)
            else:
                time.sleep(30.0) # Sleep longer when not restricted

    def stop(self):
        self.stopped = True

    def restriction_action(self, pinfo : ProcessInfo, action: RestrictionAction):
        match action:
            case RestrictionAction.MINIMIZE:
                self.log(f"Minimizing window '{pinfo.title}' of {pinfo.exe_name}")
                minimize_window(pinfo.hwnd)
            case RestrictionAction.TERMINATE:
                self.log(f"Killing process belonging to '{pinfo.title}' of {pinfo.exe_name}")
                minimize_window(pinfo.hwnd)
                terminate_process(pinfo.pid)
            case RestrictionAction.FORCE_NAVIGATION:
                self.log(f"Navigating away from browser window '{pinfo.title}' of {pinfo.exe_name}")
                time.sleep(2.0)
                browser_force_navigate(pinfo.hwnd, "https://en.wikipedia.org/wiki/Special:Random")
                time.sleep(5.0)
            case _:
                self.log(f"Unknown restriction {action=} for {pinfo=}")

if __name__=="__main__":
    # Look for default_config.json in the project root (parent of pyrri package)
    project_root = Path(__file__).parent.parent
    default_config_path = project_root / "default_config.json"
    
    tron = Pyrri(Path(__file__).parent / "logfile.txt", config_file=default_config_path)

    def on_shutdown(ctrl_type):
        tron.log(f"ACTION: Shutting down... ({ctrl_type})")
        tron.stop()

    set_shutdown_handler(on_shutdown)
    tron.run() # Will only return via shutdown handler.
