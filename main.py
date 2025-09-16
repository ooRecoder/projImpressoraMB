from utils import LockApp
import win32print
from core import (
    PrinterListManager,
    PrinterStatusManager,
    AppLogger,
    PrinterAccessManager,
    PrinterJobManager,
)
import time


def main():
    singleton = LockApp()

    if singleton.is_already_running():
        raise RuntimeError("Aplicativo já está em execução")

    # Garante inicialização das singletons
    AppLogger()
    PrinterListManager()
    PrinterAccessManager()

def test():
    printer_list = PrinterListManager.instance
    if not AppLogger.instance or not printer_list:
        raise ImportError("Instância do logger não inicializada")

    logger = AppLogger.instance.get_logger(__name__)

    # Cria instâncias de gerenciadores
    printer_status = PrinterStatusManager()
    printer_job = PrinterJobManager()
    
    
    if not printer_list:
        return
    
    printers = printer_list.list_name_printers()
    return

if __name__ == "__main__":
    main()
    test()

    
    