from typing import Dict, Union
import time
import win32print

from .logging import AppLogger
from .printer_access_manager import PrinterAccessManager, PrinterStatus
from .print_manager import PrinterPrint


class PrinterStatusManager:
    """Classe para gerenciar e verificar o status de impressoras de forma mais alto nível"""

    def __init__(self, PCA):
        logger_instance = AppLogger.instance
        self.logger = AppLogger.instance.get_logger(__name__)  # type: ignore
        self.access_manager = PCA
        self.printer_print = PrinterPrint(PCA, logger_instance)
        self.logger.info("PrinterStatusManager inicializado")
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
    def modify_printer_status(self, printer_name: str, action: str) -> bool:
        handle = None
        try:
            desired_access = win32print.PRINTER_ACCESS_ADMINISTER
            handle = self.access_manager.open_printer(printer_name, desired_access) # type: ignore
            
            if not handle:
                self.logger.error(f"Não foi possível abrir a impressora {printer_name}")
                return False

            if action == 'pause':
                # Para Level=0 (PRINTER_CONTROL_*), pPrinter deve ser None
                win32print.SetPrinter(handle, 0, None, win32print.PRINTER_CONTROL_PAUSE)
                self.logger.info(f"Impressora {printer_name} pausada")
                
            elif action == 'resume':
                # Para Level=0 (PRINTER_CONTROL_*), pPrinter deve ser None
                win32print.SetPrinter(handle, 0, None, win32print.PRINTER_CONTROL_RESUME)
                self.logger.info(f"Impressora {printer_name} retomada")
                
            else:
                self.logger.error(f"Ação {action} não reconhecida")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Erro ao modificar status da impressora {printer_name}: {e}", exc_info=True)
            return False
        finally:
            self.access_manager.close_printer(printer_name) # type: ignore
    def check_paper_status(self, printer_name: str, force_update: bool = False) -> Dict[str, Union[bool, str]]:
        """
        Verifica o estado do papel na impressora com verificações adicionais
        para maior confiabilidade
        
        Args:
            printer_name: Nome da impressora
            force_update: Se True, força atualização do status imprimindo uma página em branco
            
        Returns:
            Dict com informações sobre o estado do papel
        """
        self.logger.debug(f"Verificando estado do papel na impressora: {printer_name}")
        
        try:
            # Se forçando atualização, imprime uma página em branco primeiro
            if force_update:
                self.logger.info(f"Forçando atualização do status do papel em {printer_name} através de impressão de teste")
                print_result = self.printer_print.print_blank_page(printer_name, copies=1)
                
                if not print_result['success']:
                    self.logger.warning(f"Falha ao imprimir página de teste para atualizar status: {print_result.get('error', 'Erro desconhecido')}")
                    # Continua mesmo com falha, pois pode ser que o status já esteja disponível
                
                # Aguarda um breve momento para o sistema atualizar o status
                time.sleep(2)
            
            status = self.get_printer_status(printer_name)
            
            paper_status: Dict[str, Union[bool, str]] = {
                'paper_available': True,
                'paper_jam': False,
                'paper_low': False,
                'paper_out': False,
                'status_updated': True,
                'force_update_performed': force_update
            }
            
            status_codes = status.get('status_code', 0)
            
            self.logger.debug(f"Código de status da impressora {printer_name}: {status_codes}")
            
            # Verifica múltiplos códigos de status relacionados a papel
            paper_out_detected = bool(status_codes & win32print.PRINTER_STATUS_PAPER_OUT)
            paper_jam_detected = bool(status_codes & win32print.PRINTER_STATUS_PAPER_JAM)
            paper_problem_detected = bool(status_codes & win32print.PRINTER_STATUS_PAPER_PROBLEM)
            offline_status = bool(status_codes & win32print.PRINTER_STATUS_OFFLINE)
            
            # Se a impressora está offline, o status do papel pode não ser confiável
            if offline_status:
                self.logger.warning(f"Impressora {printer_name} offline - status do papel pode não ser confiável")
                paper_status['status_updated'] = False
            
            if paper_out_detected:
                paper_status['paper_available'] = False
                paper_status['paper_out'] = True
                self.logger.warning(f"Impressora {printer_name}: Papel esgotado")
            
            if paper_jam_detected:
                paper_status['paper_jam'] = True
                paper_status['paper_available'] = False
                self.logger.warning(f"Impressora {printer_name}: Papel encravado")
            
            if paper_problem_detected:
                paper_status['paper_low'] = True
                # Não necessariamente significa papel indisponível, apenas problema
                self.logger.warning(f"Impressora {printer_name}: Problema com o papel detectado")
            
            # Verificação adicional: se todos os flags de papel estão zerados mas a impressora está online
            if (not paper_out_detected and not paper_jam_detected and not paper_problem_detected and 
                not offline_status and status.get('is_online', False)):
                paper_status['paper_available'] = True
                self.logger.info(f"Impressora {printer_name}: Papel disponível e em bom estado")
            
            # Log do estado final do papel
            if paper_status['paper_available']:
                self.logger.info(f"Impressora {printer_name}: Papel disponível")
            else:
                self.logger.error(f"Impressora {printer_name}: Problemas com papel - "
                                f"Esgotado: {paper_status['paper_out']}, "
                                f"Encravado: {paper_status['paper_jam']}, "
                                f"Problema: {paper_status['paper_low']}")
            
            self.logger.debug(f"Estado do papel para {printer_name}: {paper_status}")
            return paper_status
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar estado do papel na impressora {printer_name}: {e}", exc_info=True)
            return {
                'paper_available': False,
                'paper_jam': False,
                'paper_low': False,
                'paper_out': False,
                'status_updated': False,
                'force_update_performed': force_update,
                'error': str(e)
            }
