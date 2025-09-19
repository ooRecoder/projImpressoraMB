import threading
import time
from typing import List, Dict, Callable, Optional
from datetime import datetime
from core import AppLogger, PrinterJobManager
from .job_utils import detect_job_changes


class PrinterJobMonitor:
    """Gerencia monitoramento contínuo de jobs"""

    def __init__(self):
        self.logger = AppLogger.instance.get_logger(__name__)  # type: ignore
        self.job_manager = PrinterJobManager()
        self._monitoring = False
        self._monitor_thread = None

    def monitor_jobs(self, 
                    printer_name: str,
                    callback: Callable[[Dict], None],
                    interval: int = 5,
                    specific_job_ids: Optional[List[int]] = None,
                    monitor_all: bool = True) -> bool:
        if self._monitoring:
            self.logger.warning("Monitoramento já em execução")
            return False

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(printer_name, callback, interval, specific_job_ids, monitor_all),
            daemon=True
        )
        self._monitor_thread.start()
        self.logger.info(f"Monitoramento iniciado para {printer_name}")
        return True

    def stop_monitoring(self):
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        self.logger.info("Monitoramento parado")

    def is_monitoring(self) -> bool:
        return self._monitoring

    def _monitor_loop(self, printer_name, callback, interval, specific_job_ids, monitor_all):
        last_jobs_state = {}
        while self._monitoring:
            try:
                current_jobs = self.job_manager.list_jobs(printer_name)
                jobs_dict = {job['job_id']: job for job in current_jobs}

                if not monitor_all and specific_job_ids:
                    jobs_dict = {jid: job for jid, job in jobs_dict.items() if jid in specific_job_ids}

                changes = detect_job_changes(last_jobs_state, jobs_dict)
                if changes:
                    for change in changes:
                        callback(change)

                last_jobs_state = jobs_dict
            except Exception as e:
                self.logger.error(f"Erro no loop de monitoramento: {e}", exc_info=True)

            time.sleep(interval)
