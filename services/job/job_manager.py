import win32print
from typing import List, Dict, Optional
from core import AppLogger, PrinterAccessManager
from .parser import format_job_info


class PrinterJobManager:
    """Gerencia operações diretas em jobs de impressão"""

    def __init__(self):
        self.logger = AppLogger.instance.get_logger(__name__)  # type: ignore
        self.access_manager = PrinterAccessManager.instance

    def list_jobs(self, printer_name: str) -> List[Dict]:
        handle = self.access_manager.open_printer(printer_name)  # type: ignore
        if not handle:
            return []

        try:
            jobs = win32print.EnumJobs(handle, 0, -1, 2)
            jobs_info = [format_job_info(job, self.access_manager) for job in jobs]
            self.logger.info(f"Encontrados {len(jobs_info)} jobs em {printer_name}")
            return jobs_info
        except Exception as e:
            self.logger.error(f"Erro ao listar jobs em {printer_name}: {e}", exc_info=True)
            return []
        finally:
            self.access_manager.close_printer(printer_name)  # type: ignore

    def get_job(self, printer_name: str, job_id: int) -> Optional[Dict]:
        handle = self.access_manager.open_printer(printer_name)  # type: ignore
        if not handle:
            return None

        try:
            job_info = win32print.GetJob(handle, job_id, 2)
            return format_job_info(job_info, self.access_manager)
        except Exception as e:
            self.logger.error(f"Erro ao obter informações do job {job_id}: {e}", exc_info=True)
            return None
        finally:
            self.access_manager.close_printer(printer_name)  # type: ignore

    def cancel_job(self, printer_name: str, job_id: int) -> bool:
        return self._control_job(printer_name, job_id, win32print.JOB_CONTROL_CANCEL, "cancelado")

    def pause_job(self, printer_name: str, job_id: int) -> bool:
        return self._control_job(printer_name, job_id, win32print.JOB_CONTROL_PAUSE, "pausado")

    def resume_job(self, printer_name: str, job_id: int) -> bool:
        return self._control_job(printer_name, job_id, win32print.JOB_CONTROL_RESUME, "retomado")

    def restart_job(self, printer_name: str, job_id: int) -> bool:
        return self._control_job(printer_name, job_id, win32print.JOB_CONTROL_RESTART, "reiniciado")

    def cancel_all_jobs(self, printer_name: str) -> bool:
        handle = self.access_manager.open_printer(printer_name)  # type: ignore
        if not handle:
            return False
        try:
            win32print.SetPrinter(handle, 0, None, win32print.PRINTER_CONTROL_PURGE)
            self.logger.info(f"Todos os jobs cancelados na impressora {printer_name}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao cancelar todos os jobs: {e}", exc_info=True)
            return False
        finally:
            self.access_manager.close_printer(printer_name)  # type: ignore

    def _control_job(self, printer_name: str, job_id: int, command: int, action: str) -> bool:
        handle = self.access_manager.open_printer(printer_name)  # type: ignore
        if not handle:
            return False
        try:
            win32print.SetJob(handle, job_id, 0, None, command)
            self.logger.info(f"Job {job_id} {action} na impressora {printer_name}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao {action} job {job_id}: {e}", exc_info=True)
            return False
        finally:
            self.access_manager.close_printer(printer_name)  # type: ignore
