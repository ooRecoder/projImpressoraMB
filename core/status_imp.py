from typing import Dict, List
import time
import win32print

from .logging import AppLogger
from .printer_acess_manager import PrinterAccessManager, PrinterStatus  # importa a classe já existente


class PrinterStatusManager:
    """Classe para gerenciar e verificar o status de impressoras de forma mais alto nível"""

    def __init__(self):
        self.logger = AppLogger.instance.get_logger(__name__)  # type: ignore
        self.logger.info("PrinterStatusManager inicializado")
        self.access_manager = PrinterAccessManager.instance

    def get_printer_status(self, printer_name: str) -> Dict:
        """
        Obtém o status completo da impressora
        """
        self.logger.debug(f"Obtendo status da impressora: {printer_name}")

        handle = self.access_manager.open_printer(printer_name) # type: ignore
        if not handle:
            self.logger.warning(f"Impressora {printer_name} não disponível")
            return {
                'status': PrinterStatus.UNKNOWN,
                'details': 'Impressora não disponível',
                'is_online': False,
                'is_ready': False
            }

        try:
            printer_info = win32print.GetPrinter(handle, 2)

            # Usa o decode já existente
            status_list = self.access_manager._decode_status(printer_info['Status']) # type: ignore
            attributes_list = self.access_manager._decode_attributes(printer_info['Attributes']) # type: ignore

            jobs = self.get_job_count(printer_name)

            result = {
                'status': status_list,
                'status_code': printer_info['Status'],
                'is_online': not bool(printer_info['Status'] & win32print.PRINTER_STATUS_OFFLINE),
                'is_ready': printer_info['Status'] == 0,
                'attributes': attributes_list,
                'job_count': jobs,
                'printer_name': printer_name,
                'server_name': printer_info['pServerName'],
                'share_name': printer_info['pShareName'],
                'port_name': printer_info['pPortName'],
                'driver_name': printer_info['pDriverName'],
                'location': printer_info['pLocation'],
                'comment': printer_info['pComment']
            }

            self.logger.debug(f"Status completo obtido: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Erro ao obter status da impressora {printer_name}: {e}", exc_info=True)
            return {
                'status': [PrinterStatus.ERROR.name],
                'details': f"Erro ao obter status: {e}",
                'is_online': False,
                'is_ready': False
            }
        finally:
            self.access_manager.close_printer(printer_name) # type: ignore

    def get_job_count(self, printer_name: str) -> int:
        """Obtém o número de jobs na fila de impressão"""
        try:
            handle = self.access_manager.open_printer(printer_name) # type: ignore
            if not handle:
                return 0

            jobs = win32print.EnumJobs(handle, 0, -1, 1)
            return len(jobs)
        except Exception as e:
            self.logger.error(f"Erro ao obter contagem de jobs para {printer_name}: {e}")
            return 0
        finally:
            self.access_manager.close_printer(printer_name) # type: ignore
            
    def is_printer_ready(self, printer_name: str) -> bool:
        """Verifica rapidamente se a impressora está pronta"""
        status = self.get_printer_status(printer_name)
        return status.get('is_ready', False)

    def monitor_printer_status(self, printer_name: str, interval: int = 5, duration: int = 60) -> None:
        """Monitora o status da impressora por um período"""
        self.logger.info(f"Iniciando monitoramento da impressora {printer_name}")

        start_time = time.time()
        while time.time() - start_time < duration:
            status = self.get_printer_status(printer_name)
            self.logger.info(
                f"[Monitoramento] {printer_name}: {status['status']} | "
                f"Online: {status['is_online']} | Jobs: {status['job_count']}"
            )
            time.sleep(interval)

        self.logger.info(f"Monitoramento da impressora {printer_name} concluído")
