from utils import LockApp
from core import PrinterListManager

def main():
    singleton = LockApp()
    
    if singleton.is_already_running():
        return

    PrinterListManager()
    

if __name__ == "__main__":
    main()