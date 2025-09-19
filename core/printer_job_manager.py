import win32print
from typing import List, Dict, Optional, Callable
import time
from .logging import AppLogger
from .printer_access_manager import PrinterAccessManager
from datetime import datetime, timedelta
import threading


class PrinterJobManager:
    """Classe para gerenciar jobs de impressão"""

    def __init__(self):
        self.logger = AppLogger.instance.get_logger(__name__)  # type: ignore
        self.access_manager = PrinterAccessManager.instance
        self._monitoring = False
        self._monitor_threading = None
    def __del__(self):
        """Destrutor - garante que o monitoramento seja parado antes da destruição do objeto"""
        try:
            if self._monitoring:
                self.stop_monitoring()
                self.logger.debug("Monitoramento parado no destrutor")
        except Exception as e:
            # Log silencioso para evitar erros durante a destruição
            try:
                self.logger.error(f"Erro no destrutor: {e}", exc_info=True)
            except:
                pass  # Ignora erros de logging durante a destruição
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
    def monitor_jobs(self, 
                    printer_name: str, 
                    callback: Callable[[Dict], None],
                    interval: int = 5,
                    specific_job_ids: Optional[List[int]] = None,
                    monitor_all: bool = True) -> bool:
        """
        Inicia o monitoramento de jobs de impressão
        
        Args:
            printer_name: Nome da impressora a ser monitorada
            callback: Função chamada quando há mudanças nos jobs
            interval: Intervalo de verificação em segundos
            specific_job_ids: Lista de IDs específicos para monitorar
            monitor_all: Se True, monitora todos os jobs; se False, apenas os específicos
        
        Returns:
            bool: True se o monitoramento foi iniciado com sucesso
        """
        if self._monitoring:
            self.logger.warning("Monitoramento já está em execução")
            return False

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(printer_name, callback, interval, specific_job_ids, monitor_all),
            daemon=True
        )
        self._monitor_thread.start()
        
        self.logger.info(f"Monitoramento iniciado para impressora {printer_name}")
        return True
    def stop_monitoring(self):
        """Para o monitoramento de jobs"""
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        self.logger.info("Monitoramento parado")
    def _monitor_loop(self, 
                    printer_name: str, 
                    callback: Callable[[Dict], None],
                    interval: int,
                    specific_job_ids: Optional[List[int]],  # ← Parâmetro definido aqui
                    monitor_all: bool):
        """Loop principal de monitoramento"""
        last_jobs_state = {}
        
        while self._monitoring:
            try:
                current_jobs = self.list_jobs(printer_name)
                current_jobs_dict = {job['job_id']: job for job in current_jobs}
                
                # Filtrar jobs se necessário
                if not monitor_all and specific_job_ids:
                    current_jobs_dict = {job_id: job for job_id, job in current_jobs_dict.items() 
                                    if job_id in specific_job_ids} 
                
                # Verificar mudanças
                changes = self._detect_job_changes(last_jobs_state, current_jobs_dict)
                
                if changes:
                    for change_info in changes:
                        callback(change_info)
                
                last_jobs_state = current_jobs_dict
                
            except Exception as e:
                self.logger.error(f"Erro no loop de monitoramento: {e}", exc_info=True)
            
            # Aguardar próximo ciclo
            for _ in range(interval * 10):
                if not self._monitoring:
                    break
                time.sleep(0.1)
    def _detect_job_changes(self, 
                          old_jobs: Dict[int, Dict], 
                          new_jobs: Dict[int, Dict]) -> List[Dict]:
        """
        Detecta mudanças entre estados de jobs
        
        Returns:
            Lista de dicionários com informações das mudanças
        """
        changes = []
        
        # Jobs novos
        for job_id, job_info in new_jobs.items():
            if job_id not in old_jobs:
                changes.append({
                    'type': 'JOB_ADDED',
                    'job_id': job_id,
                    'job_info': job_info,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Jobs removidos
        for job_id in old_jobs:
            if job_id not in new_jobs:
                changes.append({
                    'type': 'JOB_REMOVED',
                    'job_id': job_id,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Jobs com status alterado
        for job_id, new_job_info in new_jobs.items():
            if job_id in old_jobs:
                old_job_info = old_jobs[job_id]
                
                if (old_job_info['status_code'] != new_job_info['status_code'] or
                    old_job_info['pages_printed'] != new_job_info['pages_printed']):
                    
                    changes.append({
                        'type': 'JOB_UPDATED',
                        'job_id': job_id,
                        'old_status': old_job_info['status'],
                        'new_status': new_job_info['status'],
                        'old_status_code': old_job_info['status_code'],
                        'new_status_code': new_job_info['status_code'],
                        'old_pages_printed': old_job_info['pages_printed'],
                        'new_pages_printed': new_job_info['pages_printed'],
                        'job_info': new_job_info,
                        'timestamp': datetime.now().isoformat()
                    })
        
        return changes
    def get_job_history(self, 
                       printer_name: str, 
                       hours_back: int = 24) -> List[Dict]:
        """
        Obtém histórico de jobs recentes
        
        Args:
            printer_name: Nome da impressora
            hours_back: Número de horas para buscar no histórico
        
        Returns:
            Lista de jobs recentes
        """
        handle = self.access_manager.open_printer(printer_name) # type: ignore
        if not handle:
            return []

        try:
            # Buscar jobs completados/falhos (status 4 ou 5)
            jobs = win32print.EnumJobs(handle, 0, -1, 2)
            
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            recent_jobs = []
            
            for job in jobs:
                if job["Submitted"] and job["Submitted"] > cutoff_time:
                    job_info = {
                        "job_id": job["JobId"],
                        "document_name": job["pDocument"],
                        "status": self.access_manager._decode_job_status(job["Status"]), # type: ignore
                        "status_code": job["Status"],
                        "pages_printed": job["PagesPrinted"],
                        "total_pages": job["TotalPages"],
                        "submitted_time": job["Submitted"].isoformat() if job["Submitted"] else None,
                        "completion_time": None,
                        "user_name": job["pUserName"],
                        "machine_name": job["pMachineName"],
                        "data_type": job["pDatatype"],
                        "priority": job["Priority"]
                    }
                    recent_jobs.append(job_info)
            
            return sorted(recent_jobs, key=lambda x: x['submitted_time'] or '', reverse=True)
            
        except Exception as e:
            self.logger.error(f"Erro ao obter histórico de jobs: {e}", exc_info=True)
            return []
        finally:
            self.access_manager.close_printer(printer_name) # type: ignore
    def is_monitoring(self) -> bool:
        """Verifica se o monitoramento está ativo"""
        return self._monitoring
    