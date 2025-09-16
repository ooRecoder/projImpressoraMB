import win32print
from typing import List, Dict, Optional

from .logging import AppLogger
from .printer_acess_manager import PrinterAccessManager

class PrinterJobManager:
    """Classe para gerenciar jobs de impressão"""

    def __init__(self):
        self.logger = AppLogger.instance.get_logger(__name__)  # type: ignore
        self.access_manager = PrinterAccessManager.instance
        self.logger.info("PrinterJobManager inicializado")

    def list_jobs(self, printer_name: str) -> List[Dict]:
        """Lista todos os jobs de impressão de uma impressora"""
        handle = self.access_manager.open_printer(printer_name) # type: ignore
        if not handle:
            return []

        try:
            jobs = win32print.EnumJobs(handle, 0, -1, 2)
            jobs_info = []
            for job in jobs:
                jobs_info.append({
                    "job_id": job["JobId"],
                    "document_name": job["pDocument"],
                    "status": self.access_manager._decode_job_status(job["Status"]), # type: ignore
                    "status_code": job["Status"],
                    "pages_printed": job["PagesPrinted"],
                    "total_pages": job["TotalPages"],
                    "submitted_time": job["Submitted"].isoformat() if job["Submitted"] else None,
                    "user_name": job["pUserName"],
                    "machine_name": job["pMachineName"],
                    "data_type": job["pDatatype"],
                    "priority": job["Priority"]
                })
            self.logger.info(f"Encontrados {len(jobs_info)} jobs em {printer_name}")
            return jobs_info
        except Exception as e:
            self.logger.error(f"Erro ao listar jobs em {printer_name}: {e}", exc_info=True)
            return []
        finally:
            self.access_manager.close_printer(printer_name) # type: ignore

    def get_job(self, printer_name: str, job_id: int) -> Optional[Dict]:
        """Obtém informações detalhadas de um job específico"""
        handle = self.access_manager.open_printer(printer_name) # type: ignore
        if not handle:
            return None

        try:
            job_info = win32print.GetJob(handle, job_id, 2)
            return {
                "job_id": job_info["JobId"],
                "document_name": job_info["pDocument"],
                "status": self.access_manager._decode_job_status(job_info["Status"]), # type: ignore
                "status_code": job_info["Status"],
                "pages_printed": job_info["PagesPrinted"],
                "total_pages": job_info["TotalPages"],
                "submitted_time": job_info["Submitted"].isoformat() if job_info["Submitted"] else None,
                "user_name": job_info["pUserName"],
                "machine_name": job_info["pMachineName"],
                "data_type": job_info["pDatatype"],
                "priority": job_info["Priority"]
            }
        except Exception as e:
            self.logger.error(f"Erro ao obter informações do job {job_id} em {printer_name}: {e}", exc_info=True)
            return None
        finally:
            self.access_manager.close_printer(printer_name) # type: ignore

    def cancel_job(self, printer_name: str, job_id: int) -> bool:
        """Cancela um job de impressão"""
        handle = self.access_manager.open_printer(printer_name) # type: ignore
        if not handle:
            return False

        try:
            win32print.SetJob(handle, job_id, 0, None, win32print.JOB_CONTROL_CANCEL)
            self.logger.info(f"Job {job_id} cancelado na impressora {printer_name}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao cancelar job {job_id} em {printer_name}: {e}", exc_info=True)
            return False
        finally:
            self.access_manager.close_printer(printer_name) # type: ignore

    def pause_job(self, printer_name: str, job_id: int) -> bool:
        """Pausa um job de impressão"""
        return self._control_job(printer_name, job_id, win32print.JOB_CONTROL_PAUSE, "pausado")

    def resume_job(self, printer_name: str, job_id: int) -> bool:
        """Retoma um job pausado"""
        return self._control_job(printer_name, job_id, win32print.JOB_CONTROL_RESUME, "retomado")

    def restart_job(self, printer_name: str, job_id: int) -> bool:
        """Reinicia um job"""
        return self._control_job(printer_name, job_id, win32print.JOB_CONTROL_RESTART, "reiniciado")

    def cancel_all_jobs(self, printer_name: str) -> bool:
        """Cancela todos os jobs da impressora"""
        handle = self.access_manager.open_printer(printer_name) # type: ignore
        if not handle:
            return False

        try:
            win32print.SetPrinter(handle, 0, None, win32print.PRINTER_CONTROL_PURGE)
            self.logger.info(f"Todos os jobs da impressora {printer_name} foram cancelados")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao cancelar todos os jobs da impressora {printer_name}: {e}", exc_info=True)
            return False
        finally:
            self.access_manager.close_printer(printer_name) # type: ignore

    def _control_job(self, printer_name: str, job_id: int, command: int, action: str) -> bool:
        """Executa um comando em um job"""
        handle = self.access_manager.open_printer(printer_name) # type: ignore
        if not handle:
            return False

        try:
            win32print.SetJob(handle, job_id, 0, None, command)
            self.logger.info(f"Job {job_id} {action} na impressora {printer_name}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao {action} job {job_id} em {printer_name}: {e}", exc_info=True)
            return False
        finally:
            self.access_manager.close_printer(printer_name) # type: ignore
