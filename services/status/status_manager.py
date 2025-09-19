from core import AppLogger
from .status_checker import PrinterStatusChecker
from .status_monitor import PrinterStatusMonitor
from .status_controller import PrinterStatusController

class PrinterStatusManager:
    """API de alto nível para status da impressora"""

    def __init__(self, access_manager):
        logger_instance = AppLogger.instance
        self.logger = logger_instance.get_logger(__name__)  # type: ignore
        self.checker = PrinterStatusChecker(access_manager)
        self.monitor = PrinterStatusMonitor(self.checker)
        self.controller = PrinterStatusController(access_manager)
    def get_status(self, printer_name: str):
        return self.checker.get_printer_status(printer_name)
    def monitor_status(self, printer_name: str, interval=5, duration=60):
        return self.monitor.monitor_printer_status(printer_name, interval, duration)
    def change_status(self, printer_name: str, action: str):
        return self.controller.modify_printer_status(printer_name, action)
