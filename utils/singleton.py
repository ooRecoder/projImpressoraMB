import win32event
import win32api
import winerror
import win32gui
import win32con


class Singleton:
    """
    Implementação do Singleton como uma classe decorator.
    Mais robusta para preservar o nome e docstring da classe original.
    """
    def __init__(self, cls):
        self.cls = cls
        self.instance = None
    
    def __call__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = self.cls(*args, **kwargs)
        return self.instance
    
    def __instancecheck__(self, instance):
        return isinstance(instance, self.cls)
    
class LockApp:
    def __init__(self, app_name="MyApp", window_title=None):
        self.app_name = app_name
        self.window_title = window_title
        self.mutex = win32event.CreateMutex(None, False, app_name) # type: ignore
        self.last_error = win32api.GetLastError()
    
    def is_already_running(self):
        return self.last_error == winerror.ERROR_ALREADY_EXISTS
    
    def bring_to_front(self):
        """Traz a janela existente para frente"""
        if self.window_title:
            hwnd = win32gui.FindWindow(None, self.window_title)
            if hwnd:
                # Restaura se minimizado
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                # Traz para frente
                win32gui.SetForegroundWindow(hwnd)
                return True
        return False
    
    def __del__(self):
        if self.mutex:
            win32api.CloseHandle(self.mutex)