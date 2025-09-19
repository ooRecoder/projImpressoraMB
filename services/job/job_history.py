import win32print
from datetime import datetime, timedelta
from typing import List, Dict
from core import AppLogger, PrinterAccessManager
from .parser import format_job_info


class PrinterJobHistory:
    """Consulta histórico de jobs de impressão"""

    def __init__(self):
        self.logger = AppLogger.instance.get_logger(__name__)  # type: ignore
        self.access_manager = PrinterAccessManager.instance

    def get_job_history(self, printer_name: str, hours_back: int = 24) -> List[Dict]:
        handle = self.access_manager.open_printer(printer_name)  # type: ignore
        if not handle:
            return []

        try:
            jobs = win32print.EnumJobs(handle, 0, -1, 2)
            cutoff = datetime.now() - timedelta(hours=hours_back)

            recent = []
            for job in jobs:
                if job["Submitted"] and job["Submitted"] > cutoff:
                    recent.append(format_job_info(job, self.access_manager))

            return sorted(recent, key=lambda x: x['submitted_time'] or '', reverse=True)
        except Exception as e:
            self.logger.error(f"Erro ao obter histórico: {e}", exc_info=True)
            return []
        finally:
            self.access_manager.close_printer(printer_name)  # type: ignore
