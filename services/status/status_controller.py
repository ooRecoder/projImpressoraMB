import win32print
from core import AppLogger


class PrinterStatusController:
    """Controla estado da impressora (pausa, retoma)"""

    def __init__(self, access_manager):
        self.logger = AppLogger.instance.get_logger(__name__)  # type: ignore
        self.access_manager = access_manager

    def modify_printer_status(self, printer_name: str, action: str) -> bool:
        try:
            handle = self.access_manager.open_printer(printer_name, win32print.PRINTER_ACCESS_ADMINISTER)  # type: ignore
            if not handle:
                return False

            if action == "pause":
                win32print.SetPrinter(handle, 0, None, win32print.PRINTER_CONTROL_PAUSE)
            elif action == "resume":
                win32print.SetPrinter(handle, 0, None, win32print.PRINTER_CONTROL_RESUME)
            else:
                self.logger.error(f"Ação {action} inválida")
                return False

            self.logger.info(f"Ação {action} executada em {printer_name}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao executar {action} em {printer_name}: {e}", exc_info=True)
            return False
        finally:
            self.access_manager.close_printer(printer_name)  # type: ignore
