import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import win32con

# Add project root to path so we can import pyrri
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyrri.winproc import core


class TestWinProc(unittest.TestCase):
    @patch("pyrri.winproc.core.win32gui")
    @patch("pyrri.winproc.core.win32process")
    @patch("pyrri.winproc.core.psutil")
    def test_get_active_window_info(
        self, mock_psutil, mock_win32process, mock_win32gui
    ):
        # Setup mocks
        mock_hwnd = 12345
        mock_pid = 6789
        mock_title = "Test Window"
        mock_exe = "test_app.exe"

        mock_win32gui.GetForegroundWindow.return_value = mock_hwnd
        mock_win32gui.GetWindowText.return_value = mock_title
        mock_win32process.GetWindowThreadProcessId.return_value = (0, mock_pid)

        mock_process = MagicMock()
        mock_process.name.return_value = mock_exe
        mock_psutil.Process.return_value = mock_process

        # Execute
        title, exe_name, pid, hwnd = core.get_active_window_info()

        # Assert
        self.assertEqual(title, mock_title)
        self.assertEqual(exe_name, mock_exe)
        self.assertEqual(pid, mock_pid)
        self.assertEqual(hwnd, mock_hwnd)

        mock_win32gui.GetForegroundWindow.assert_called_once()
        mock_win32gui.GetWindowText.assert_called_with(mock_hwnd)
        mock_psutil.Process.assert_called_with(mock_pid)

    @patch("pyrri.winproc.core.ctypes")
    def test_is_session_locked_locked(self, mock_ctypes):
        # Setup mock to fail opening desktop (simulating locked state)
        mock_ctypes.windll.user32.OpenInputDesktop.return_value = 0

        # Execute
        is_locked = core.is_session_locked()

        # Assert
        self.assertTrue(is_locked)
        mock_ctypes.windll.user32.OpenInputDesktop.assert_called_once()

    @patch("pyrri.winproc.core.ctypes")
    def test_is_session_locked_unlocked(self, mock_ctypes):
        # Setup mock to succeed opening desktop (simulating unlocked state)
        mock_handle = 999
        mock_ctypes.windll.user32.OpenInputDesktop.return_value = mock_handle

        # Execute
        is_locked = core.is_session_locked()

        # Assert
        self.assertFalse(is_locked)
        mock_ctypes.windll.user32.CloseDesktop.assert_called_with(mock_handle)

    @patch("pyrri.winproc.core.win32gui")
    def test_minimize_window(self, mock_win32gui):
        hwnd = 12345
        core.minimize_window(hwnd)
        # win32con.SW_MINIMIZE is 6
        mock_win32gui.ShowWindow.assert_called_with(hwnd, 6)

    @patch("pyrri.winproc.core.win32api")
    def test_show_topmost_message(self, mock_win32api):
        text = "Hello"
        title = "World"
        core.show_topmost_message(text, title)
        # MB_OK | MB_TOPMOST = 0 | 0x00040000
        mock_win32api.MessageBox.assert_called_with(0, text, title, 0x00040000)

    @patch("pyrri.winproc.core.ctypes")
    def test_lock_session(self, mock_ctypes):
        core.lock_session()
        mock_ctypes.windll.user32.LockWorkStation.assert_called_once()

    @patch("pyrri.winproc.core.psutil")
    def test_terminate_process(self, mock_psutil):
        pid = 5555
        mock_process = MagicMock()
        mock_psutil.Process.return_value = mock_process

        core.terminate_process(pid)

        mock_psutil.Process.assert_called_with(pid)
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()

    @patch("pyrri.winproc.core.win32api")
    def test_set_shutdown_handler(self, mock_win32api):
        handler = MagicMock()
        core.set_shutdown_handler(handler)
        mock_win32api.SetConsoleCtrlHandler.assert_called_once()

    @patch("pyrri.winproc.core.win32api")
    def test_send_key(self, mock_win32api):
        hwnd = 12345
        key_code = 0x0D  # VK_RETURN
        scan_code = 0x1C
        mock_win32api.MapVirtualKey.return_value = scan_code

        # Test both down and up
        core.send_key(hwnd, key_code, down=True, up=True)

        lparam_down = 1 | (scan_code << 16)
        lparam_up = 1 | (scan_code << 16) | (1 << 30) | (1 << 31)

        expected_calls = [
            call.MapVirtualKey(key_code, 0),
            call.PostMessage(hwnd, win32con.WM_KEYDOWN, key_code, lparam_down),
            call.PostMessage(hwnd, win32con.WM_KEYUP, key_code, lparam_up),
        ]
        mock_win32api.assert_has_calls(expected_calls)

    @patch("pyrri.winproc.core.win32api")
    def test_send_char(self, mock_win32api):
        hwnd = 12345
        char = "A"

        core.send_char(hwnd, char)

        mock_win32api.PostMessage.assert_called_once_with(
            hwnd, win32con.WM_CHAR, ord(char), 0
        )

    @patch("pyrri.winproc.core.send_char")
    @patch("pyrri.winproc.core.send_key")
    @patch("pyrri.winproc.core.time")
    def test_browser_force_navigate(self, mock_time, mock_send_key, mock_send_char):
        hwnd = 12345
        url = "a"

        core.browser_force_navigate(hwnd, url)

        # Verify sequence: F6 -> 'a' (via send_char) -> Enter
        mock_send_key.assert_has_calls(
            [call(hwnd, win32con.VK_F6), call(hwnd, win32con.VK_RETURN)]
        )

        mock_send_char.assert_called_once_with(hwnd, "a")


if __name__ == "__main__":
    unittest.main()
