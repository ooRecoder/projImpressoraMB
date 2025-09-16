import win32print
import time
from typing import Dict, List
from enum import Enum

# Importa o sistema de logging
from .logging import AppLogger

class PrinterStatus(Enum):
    """Enumeração dos possíveis status de impressora"""
    READY = "Pronta"
    PAUSED = "Pausada"
    ERROR = "Erro"
    PENDING_DELETION = "Exclusão pendente"
    PAPER_JAM = "Papel emperrado"
    PAPER_OUT = "Sem papel"
    MANUAL_FEED = "Alimentação manual"
    PAPER_PROBLEM = "Problema de papel"
    OFFLINE = "Offline"
    IO_ACTIVE = "E/S ativa"
    BUSY = "Ocupada"
    PRINTING = "Imprimindo"
    OUTPUT_BIN_FULL = "Bandeja de saída cheia"
    NOT_AVAILABLE = "Não disponível"
    WAITING = "Aguardando"
    PROCESSING = "Processando"
    INITIALIZING = "Inicializando"
    WARMING_UP = "Aquecendo"
    TONER_LOW = "Toner baixo"
    NO_TONER = "Sem toner"
    PAGE_PUNT = "Page punt"
    USER_INTERVENTION = "Intervenção do usuário"
    OUT_OF_MEMORY = "Memória insuficiente"
    DOOR_OPEN = "Porta aberta"
    SERVER_UNKNOWN = "Servidor desconhecido"
    POWER_SAVE = "Modo de economia de energia"
    UNKNOWN = "Status desconhecido"

class PrinterStatusManager:
    """Classe para gerenciar e verificar o status de impressoras"""
    
    def __init__(self):
        self.printer_handle = None
        self.logger = AppLogger.instance.get_logger(__name__) # type: ignore
        self.logger.info("PrinterStatusManager inicializado")
    
    def open_printer(self, printer_name: str) -> bool:
        """
        Abre uma conexão com a impressora
        
        Args:
            printer_name: Nome da impressora
            
        Returns:
            True se conseguiu abrir, False caso contrário
        """
        try:
            self.logger.debug(f"Tentando abrir impressora: {printer_name}")
            self.printer_handle = win32print.OpenPrinter(printer_name)
            self.logger.info(f"Impressora {printer_name} aberta com sucesso")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao abrir impressora {printer_name}: {e}", 
                            exc_info=True)
            return False
    
    def close_printer(self) -> None:
        """Fecha a conexão com a impressora"""
        if self.printer_handle:
            try:
                win32print.ClosePrinter(self.printer_handle)
                self.logger.debug("Conexão com impressora fechada")
            except Exception as e:
                self.logger.warning(f"Erro ao fechar impressora: {e}")
            finally:
                self.printer_handle = None
    
    def get_printer_status(self, printer_name: str) -> Dict:
        """
        Obtém o status completo da impressora
        
        Args:
            printer_name: Nome da impressora
            
        Returns:
            Dicionário com informações de status
        """
        self.logger.debug(f"Obtendo status da impressora: {printer_name}")
        
        if not self.open_printer(printer_name):
            self.logger.warning(f"Impressora {printer_name} não disponível")
            return {
                'status': PrinterStatus.NOT_AVAILABLE,
                'details': 'Impressora não disponível',
                'is_online': False,
                'is_ready': False
            }
        
        try:
            # Obtém informações da impressora
            self.logger.debug("Obtendo informações da impressora")
            printer_info = win32print.GetPrinter(self.printer_handle, 2) # type: ignore
            
            # Status da impressora
            status_code = printer_info['Status']
            status_text = self._decode_status_code(status_code)
            
            self.logger.info(f"Status da impressora {printer_name}: {status_text.value} (código: {status_code})")
            
            # Informações adicionais
            attributes = printer_info['Attributes']
            is_shared = bool(attributes & win32print.PRINTER_ATTRIBUTE_SHARED)
            is_network = bool(attributes & win32print.PRINTER_ATTRIBUTE_NETWORK)
            
            # Jobs na fila
            jobs = self.get_job_count(printer_name)
            
            if jobs > 0:
                self.logger.info(f"Encontrados {jobs} jobs na fila da impressora {printer_name}")
                
            result = {
                'status': status_text,
                'status_code': status_code,
                'is_online': not bool(status_code & win32print.PRINTER_STATUS_OFFLINE),
                'is_ready': status_code == 0,
                'is_shared': is_shared,
                'is_network': is_network,
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
            self.logger.error(f"Erro ao obter status da impressora {printer_name}: {e}", 
                            exc_info=True)
            return {
                'status': PrinterStatus.ERROR,
                'details': f"Erro ao obter status: {e}",
                'is_online': False,
                'is_ready': False
            }
        finally:
            self.close_printer()
    
    def _decode_status_code(self, status_code: int) -> PrinterStatus:
        """Decodifica o código de status da impressora"""
        if status_code == 0:
            return PrinterStatus.READY
        
        status_mapping = {
            win32print.PRINTER_STATUS_PAUSED: PrinterStatus.PAUSED,
            win32print.PRINTER_STATUS_ERROR: PrinterStatus.ERROR,
            win32print.PRINTER_STATUS_PENDING_DELETION: PrinterStatus.PENDING_DELETION,
            win32print.PRINTER_STATUS_PAPER_JAM: PrinterStatus.PAPER_JAM,
            win32print.PRINTER_STATUS_PAPER_OUT: PrinterStatus.PAPER_OUT,
            win32print.PRINTER_STATUS_MANUAL_FEED: PrinterStatus.MANUAL_FEED,
            win32print.PRINTER_STATUS_PAPER_PROBLEM: PrinterStatus.PAPER_PROBLEM,
            win32print.PRINTER_STATUS_OFFLINE: PrinterStatus.OFFLINE,
            win32print.PRINTER_STATUS_IO_ACTIVE: PrinterStatus.IO_ACTIVE,
            win32print.PRINTER_STATUS_BUSY: PrinterStatus.BUSY,
            win32print.PRINTER_STATUS_PRINTING: PrinterStatus.PRINTING,
            win32print.PRINTER_STATUS_OUTPUT_BIN_FULL: PrinterStatus.OUTPUT_BIN_FULL,
            win32print.PRINTER_STATUS_NOT_AVAILABLE: PrinterStatus.NOT_AVAILABLE,
            win32print.PRINTER_STATUS_WAITING: PrinterStatus.WAITING,
            win32print.PRINTER_STATUS_PROCESSING: PrinterStatus.PROCESSING,
            win32print.PRINTER_STATUS_INITIALIZING: PrinterStatus.INITIALIZING,
            win32print.PRINTER_STATUS_WARMING_UP: PrinterStatus.WARMING_UP,
            win32print.PRINTER_STATUS_TONER_LOW: PrinterStatus.TONER_LOW,
            win32print.PRINTER_STATUS_NO_TONER: PrinterStatus.NO_TONER,
            win32print.PRINTER_STATUS_PAGE_PUNT: PrinterStatus.PAGE_PUNT,
            win32print.PRINTER_STATUS_USER_INTERVENTION: PrinterStatus.USER_INTERVENTION,
            win32print.PRINTER_STATUS_OUT_OF_MEMORY: PrinterStatus.OUT_OF_MEMORY,
            win32print.PRINTER_STATUS_DOOR_OPEN: PrinterStatus.DOOR_OPEN,
            win32print.PRINTER_STATUS_SERVER_UNKNOWN: PrinterStatus.SERVER_UNKNOWN,
            win32print.PRINTER_STATUS_POWER_SAVE: PrinterStatus.POWER_SAVE,
        }
        
        # Verifica cada bit de status
        for code, status in status_mapping.items():
            if status_code & code:
                self.logger.debug(f"Status code {status_code} mapeado para {status}")
                return status
        
        self.logger.warning(f"Status code {status_code} não reconhecido, retornando UNKNOWN")
        return PrinterStatus.UNKNOWN
    
    def get_job_count(self, printer_name: str) -> int:
        """
        Obtém o número de jobs na fila de impressão
        
        Args:
            printer_name: Nome da impressora
            
        Returns:
            Número de jobs na fila
        """
        try:
            self.logger.debug(f"Obtendo contagem de jobs para impressora: {printer_name}")
            
            if not self.open_printer(printer_name):
                return 0
            
            jobs = win32print.EnumJobs(self.printer_handle, 0, -1, 1) # type: ignore
            job_count = len(jobs)
            
            self.logger.debug(f"Encontrados {job_count} jobs na impressora {printer_name}")
            return job_count
            
        except Exception as e:
            self.logger.error(f"Erro ao obter contagem de jobs para {printer_name}: {e}")
            return 0
        finally:
            self.close_printer()
    
    def get_jobs_info(self, printer_name: str) -> List[Dict]:
        """
        Obtém informações detalhadas sobre os jobs na fila
        
        Args:
            printer_name: Nome da impressora
            
        Returns:
            Lista de dicionários com informações dos jobs
        """
        self.logger.debug(f"Obtendo informações detalhadas de jobs para: {printer_name}")
        
        try:
            if not self.open_printer(printer_name):
                self.logger.warning(f"Não foi possível abrir impressora {printer_name} para obter jobs")
                return []
            
            jobs = win32print.EnumJobs(self.printer_handle, 0, -1, 2) # type: ignore
            jobs_info = []
            
            self.logger.info(f"Processando {len(jobs)} jobs da impressora {printer_name}")
            
            for job in jobs:
                job_info = {
                    'job_id': job['JobId'],
                    'document_name': job['pDocument'],
                    'status': self._decode_job_status(job['Status']),
                    'status_code': job['Status'],
                    'pages_printed': job['PagesPrinted'],
                    'total_pages': job['TotalPages'],
                    'submitted_time': job['Submitted'].time() if job['Submitted'] else None,
                    'user_name': job['pUserName'],
                    'machine_name': job['pMachineName'],
                    'data_type': job['pDatatype'],
                    'priority': job['Priority']
                }
                jobs_info.append(job_info)
                
                self.logger.debug(f"Job {job['JobId']}: {job['pDocument']} - {job_info['status']}")
            
            return jobs_info
            
        except Exception as e:
            self.logger.error(f"Erro ao obter jobs da impressora {printer_name}: {e}", 
                            exc_info=True)
            return []
        finally:
            self.close_printer()
    
    def _decode_job_status(self, status_code: int) -> str:
        """Decodifica o status do job de impressão"""
        status_mapping = {
            win32print.JOB_STATUS_PAUSED: "Pausado",
            win32print.JOB_STATUS_ERROR: "Erro",
            win32print.JOB_STATUS_DELETING: "Excluindo",
            win32print.JOB_STATUS_SPOOLING: "Spooling",
            win32print.JOB_STATUS_PRINTING: "Imprimindo",
            win32print.JOB_STATUS_OFFLINE: "Offline",
            win32print.JOB_STATUS_PAPEROUT: "Sem papel",
            win32print.JOB_STATUS_PRINTED: "Impresso",
            win32print.JOB_STATUS_DELETED: "Excluído",
            win32print.JOB_STATUS_BLOCKED_DEVQ: "Bloqueado",
            win32print.JOB_STATUS_USER_INTERVENTION: "Intervenção do usuário",
            win32print.JOB_STATUS_RESTART: "Reiniciando"
        }
        
        statuses = []
        for code, status in status_mapping.items():
            if status_code & code:
                statuses.append(status)
        
        return ", ".join(statuses) if statuses else "Aguardando"
    
    def is_printer_ready(self, printer_name: str) -> bool:
        """
        Verifica rapidamente se a impressora está pronta
        
        Args:
            printer_name: Nome da impressora
            
        Returns:
            True se estiver pronta, False caso contrário
        """
        self.logger.debug(f"Verificando se impressora {printer_name} está pronta")
        status = self.get_printer_status(printer_name)
        is_ready = status['is_ready']
        
        if is_ready:
            self.logger.info(f"Impressora {printer_name} está pronta")
        else:
            self.logger.warning(f"Impressora {printer_name} não está pronta. Status: {status['status'].value}")
        
        return is_ready
    
    def monitor_printer_status(self, printer_name: str, interval: int = 5, duration: int = 60) -> None:
        """
        Monitora o status da impressora por um período
        
        Args:
            printer_name: Nome da impressora
            interval: Intervalo entre verificações em segundos
            duration: Duração total do monitoramento em segundos
        """
        self.logger.info(f"Iniciando monitoramento da impressora: {printer_name} "
                       f"por {duration} segundos com intervalo de {interval} segundos")
        
        start_time = time.time()
        end_time = start_time + duration
        check_count = 0
        
        while time.time() < end_time:
            check_count += 1
            self.logger.debug(f"Verificação #{check_count} do monitoramento")
            
            status = self.get_printer_status(printer_name)
            
            self.logger.info(f"Monitoramento - Status: {status['status'].value}, "
                           f"Online: {'Sim' if status['is_online'] else 'Não'}, "
                           f"Jobs: {status['job_count']}")
            
            time.sleep(interval)
        
        self.logger.info(f"Monitoramento da impressora {printer_name} concluído. "
                       f"Total de verificações: {check_count}")


if __name__ == "__main__":
    # Inicializa o logger
    logger = AppLogger().get_logger(__name__)
    logger.info("Iniciando teste do PrinterStatusManager")
    
    # Cria instância do gerenciador
    printer_manager = PrinterStatusManager()
    
    # Obtém todas as impressoras disponíveis
    try:
        printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
        logger.info(f"Impressoras encontradas: {len(printers)}")
        
        for i, printer in enumerate(printers):
            printer_name = printer[2]
            logger.debug(f"Impressora {i+1}: {printer_name}")
            
            # Testa o status de cada impressora
            status = printer_manager.get_printer_status(printer_name)
            logger.info(f"Status de {printer_name}: {status['status'].value}")
            
            # Testa jobs se houver
            jobs = printer_manager.get_jobs_info(printer_name)
            if jobs:
                logger.info(f"Jobs encontrados em {printer_name}: {len(jobs)}")
            
    except Exception as e:
        logger.error(f"Erro durante teste: {e}", exc_info=True)
    
    logger.info("Teste do PrinterStatusManager concluído")