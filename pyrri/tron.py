import time
import signal
from pathlib import Path

from win32.lib import win32con

from pyrri.time_utils import get_current_time_info
from pyrri.winproc.core import get_active_window_info, browser_force_navigate, send_key, terminate_process, \
    minimize_window, set_shutdown_handler, is_session_locked


class Tron:

    def __init__(self, logfile):
        self.logfile = logfile
        self.stopped = False
        self.last_pinfo = None

    def log(self, msg):
        with open(self.logfile, mode='at', encoding="utf-8") as fh:
            print(msg, file=fh)

    def is_restricted_time(self):
        day, hour, minute = get_current_time_info()
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
        pinfo = get_active_window_info()


        day, hour, minute = get_current_time_info()
        title, exe_name, pid, hwnd = pinfo
        if pinfo != self.last_pinfo:
            self.log(f"ACTIVE[{day=} {hour=} {minute=}] {exe_name=} - {title=}")
        self.last_pinfo = pinfo
        if 'chrome' in exe_name:
            if 'Minecraft' in title or 'GeForce NOW' in title:
                time.sleep(2.0)
                browser_force_navigate(hwnd, "https://www.wikipedia.com/")
                time.sleep(5.0)
        if 'firefox' in exe_name or 'iexplore' in exe_name or 'edge' in exe_name or 'opera' in exe_name:
            minimize_window(hwnd)
            terminate_process(pid)
        if exe_name == 'Minecraft.exe':
            self.log("ACTION: Minimizing Minecraft Launcher")
            minimize_window(hwnd)
        if 'java' in exe_name and 'Minecraft' in title:
            self.log("ACTION: Minimizing Minecraft")
            minimize_window(hwnd)
        if exe_name == 'steamwebhelper.exe':
            self.log("ACTION: Minimizing Steam")
            minimize_window(hwnd)
        if exe_name == 'WindowsTerminal.exe':
            self.log("ACTION: Minimizing Terminal")
            minimize_window(hwnd)

    def install_signal_handlers(self):
        """
        Installs signal handlers to ignore termination signals.
        """
        def ignore_signal(signum, frame):
            self.log(f"EVENT: Received signal {signum}, ignoring.")

        # Standard signals
        signal.signal(signal.SIGINT, ignore_signal)
        signal.signal(signal.SIGTERM, ignore_signal)

        
        # Windows specific: SIGBREAK (Ctrl+Break)
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, ignore_signal)
        if hasattr(signal, 'SIGSTOP'):
            signal.signal(signal.SIGSTOP, ignore_signal)

    def run(self):
        while not self.stopped:
            if self.is_restricted_time():
                self.process_guard()
                time.sleep(4.0)
            else:
                time.sleep(30.0) # Sleep longer when not restricted

    def stop(self):
        self.stopped = True



if __name__=="__main__":

    tron = Tron(Path(__file__).parent / "logfile.txt")

    def on_shutdown(ctrl_type):
        tron.log(f"ACTION: Shutting down... ({ctrl_type})")
        tron.stop()

    set_shutdown_handler(on_shutdown)
    tron.run() # Will only return via shutdown handler.
