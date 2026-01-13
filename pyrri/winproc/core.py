import ctypes
import time
import win32api
import win32con
import win32gui
import win32process
import psutil


def get_active_window_info():
    """
    Returns a tuple containing (window_title, executable_name, pid, hwnd)
    of the currently focused / topmost window.
    """
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return None, None, None, None

    title = win32gui.GetWindowText(hwnd)
    _, pid = win32process.GetWindowThreadProcessId(hwnd)

    try:
        process = psutil.Process(pid)
        exe_name = process.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        exe_name = None

    return title, exe_name, pid, hwnd


def is_session_locked():
    """
    Determines if the Windows login session is locked.
    """
    user32 = ctypes.windll.user32
    # Open the input desktop
    hDesktop = user32.OpenInputDesktop(0, False, 0x0100)  # DESKTOP_SWITCHDESKTOP
    if not hDesktop:
        # If we can't open the input desktop, it might be locked or UAC prompt
        return True

    # If we can open it, close the handle and return False (not locked)
    user32.CloseDesktop(hDesktop)
    return False


def minimize_window(hwnd):
    """
    Minimizes the specified window.
    """
    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)


def show_topmost_message(text, title="Alert"):
    """
    Displays a message box on top of all other windows.
    """
    # MB_TOPMOST = 0x00040000
    # MB_OK = 0x00000000
    win32api.MessageBox(0, text, title, win32con.MB_OK | win32con.MB_TOPMOST)


def lock_session():
    """
    Locks the current Windows session.
    """
    ctypes.windll.user32.LockWorkStation()


def terminate_process(pid):
    """
    Terminates the process with the given PID.
    """
    try:
        process = psutil.Process(pid)
        process.terminate()
        process.wait(timeout=3)
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass


def set_shutdown_handler(handler_func):
    """
    Sets a handler for Windows shutdown/reboot messages.
    The handler_func should accept one argument (ctrl_type).
    """

    def _handler(ctrl_type):
        if ctrl_type in (win32con.CTRL_SHUTDOWN_EVENT, win32con.CTRL_LOGOFF_EVENT):
            handler_func(ctrl_type)
            return True  # Indicate we handled it
        return False  # Let other handlers process it

    win32api.SetConsoleCtrlHandler(_handler, True)


def send_key(hwnd, key_code, down=True, up=True):
    """
    Sends a key press and/or release event to the specified window.

    :param hwnd: The handle of the window.
    :param key_code: The virtual key code (e.g., win32con.VK_RETURN).
    :param down: Whether to send a key down event.
    :param up: Whether to send a key up event.
    """
    scan_code = win32api.MapVirtualKey(key_code, 0)

    if down:
        # Repeat count = 1 (bits 0-15)
        # Scan code (bits 16-23)
        lparam = 1 | (scan_code << 16)
        win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, key_code, lparam)

    if up:
        # Repeat count = 1 (bits 0-15)
        # Scan code (bits 16-23)
        # Transition state (bit 31) = 1 (always 1 for WM_KEYUP)
        # Previous key state (bit 30) = 1 (always 1 for WM_KEYUP)
        # Context code (bit 29) = 0
        lparam = 1 | (scan_code << 16) | (1 << 30) | (1 << 31)
        win32api.PostMessage(hwnd, win32con.WM_KEYUP, key_code, lparam)


def send_char(hwnd, char):
    """
    Sends a single character to the window using WM_CHAR.
    This handles case sensitivity and special characters automatically.
    """
    win32api.PostMessage(hwnd, win32con.WM_CHAR, ord(char), 0)


def browser_force_navigate(hwnd, url):
    """
    Sends F6 to focus the address bar, types the URL, and presses Enter.

    :param hwnd: The handle of the browser window.
    :param url: The URL string to navigate to.
    """
    # Send F6 to focus address bar
    send_key(hwnd, win32con.VK_F6)
    time.sleep(0.1)  # Small delay to allow focus change

    # Send each character of the URL using WM_CHAR
    for char in url:
        send_char(hwnd, char)

    time.sleep(0.1)
    # Send Enter to navigate
    send_key(hwnd, win32con.VK_RETURN)
