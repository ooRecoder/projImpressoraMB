import time
from core import AppLogger
from .status_checker import PrinterStatusChecker


class PrinterStatusMonitor:
    """Monitoramento contínuo do status da impressora"""

    def __init__(self, checker: PrinterStatusChecker):
        self.logger = AppLogger.instance.get_logger(__name__)  # type: ignore
        self.checker = checker

    def monitor_printer_status(self, printer_name: str, interval: int = 5, duration: int = 60):
        self.logger.info(f"Iniciando monitoramento da impressora {printer_name}")

        start_time = time.time()
        while time.time() - start_time < duration:
            status = self.checker.get_printer_status(printer_name)
            self.logger.info(
                f"[Monitoramento] {printer_name}: {status['status']} | "
                f"Online: {status['is_online']} | Jobs: {status['job_count']}"
            )
            time.sleep(interval)

        self.logger.info(f"Monitoramento da impressora {printer_name} concluído")
