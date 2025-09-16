from typing import Dict, Optional, Any, List
from utils import Singleton
from .logging import AppLogger  # importa o logger centralizado
import win32print
import time
from enum import Enum


class PrinterStatus(Enum):
    """Enumeração para status de impressora"""
    READY = 0
    PAUSED = 1
    ERROR = 2
    PENDING_DELETION = 3
    PAPER_JAM = 4
    PAPER_OUT = 5
    MANUAL_FEED = 6
    PAPER_PROBLEM = 7
    OFFLINE = 8
    IO_ACTIVE = 9
    BUSY = 10
    PRINTING = 11
    OUTPUT_BIN_FULL = 12
    NOT_AVAILABLE = 13
    WAITING = 14
    PROCESSING = 15
    INITIALIZING = 16
    WARMING_UP = 17
    TONER_LOW = 18
    NO_TONER = 19
    PAGE_PUNT = 20
    USER_INTERVENTION = 21
    OUT_OF_MEMORY = 22
    DOOR_OPEN = 23
    SERVER_UNKNOWN = 24
    POWER_SAVE = 25
    UNKNOWN = 99


@Singleton
class PrinterAccessManager:
    """Classe para gerenciar acesso e operações em impressoras"""
    
    def __init__(self):
        from .list_available_imp import PrinterListManager
        self.open_handles: Dict[str, Any] = {}
        self.printer_list_manager = PrinterListManager.instance
        self.logger = AppLogger.instance.get_logger(__name__) # type: ignore
    
    def open_printer(self, printer_name: str, desired_access: int = win32print.PRINTER_ACCESS_USE) -> Optional[Any]:
        """Abre uma conexão com a impressora com nível de acesso específico"""
        try:
            if printer_name in self.open_handles:
                self.logger.debug(f"Handle já aberto para a impressora: {printer_name}")
                return self.open_handles[printer_name]
            
            handle = win32print.OpenPrinter(printer_name, {"DesiredAccess": desired_access})
            self.open_handles[printer_name] = handle
            self.logger.info(f"Impressora '{printer_name}' aberta com sucesso (acesso: {desired_access}).")
            return handle
        except Exception as e:
            self.logger.error(f"Erro ao abrir impressora {printer_name}: {e}", exc_info=True)
            return None
    def close_printer(self, printer_name: str) -> bool:
        """Fecha a conexão com uma impressora"""
        try:
            if printer_name in self.open_handles:
                win32print.ClosePrinter(self.open_handles[printer_name])
                del self.open_handles[printer_name]
                self.logger.info(f"Impressora '{printer_name}' fechada com sucesso.")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao fechar impressora {printer_name}: {e}", exc_info=True)
            return False
    
    def close_all_printers(self) -> bool:
        """Fecha todas as conexões abertas com impressoras"""
        success = True
        for printer_name in list(self.open_handles.keys()):
            if not self.close_printer(printer_name):
                success = False
        if success:
            self.logger.info("Todas as conexões com impressoras foram fechadas.")
        else:
            self.logger.warning("Algumas impressoras não puderam ser fechadas corretamente.")
        return success
    
    def _decode_status(self, status_code: int) -> List[str]:
        """Decodifica o código de status da impressora"""
        status_messages = []
        status_mapping = {
            win32print.PRINTER_STATUS_PAUSED: "Pausada",
            win32print.PRINTER_STATUS_ERROR: "Erro",
            win32print.PRINTER_STATUS_PENDING_DELETION: "Exclusão pendente",
            win32print.PRINTER_STATUS_PAPER_JAM: "Papel encravado",
            win32print.PRINTER_STATUS_PAPER_OUT: "Sem papel",
            win32print.PRINTER_STATUS_MANUAL_FEED: "Alimentação manual",
            win32print.PRINTER_STATUS_PAPER_PROBLEM: "Problema com papel",
            win32print.PRINTER_STATUS_OFFLINE: "Offline",
            win32print.PRINTER_STATUS_IO_ACTIVE: "I/O ativo",
            win32print.PRINTER_STATUS_BUSY: "Ocupada",
            win32print.PRINTER_STATUS_PRINTING: "Imprimindo",
            win32print.PRINTER_STATUS_OUTPUT_BIN_FULL: "Bandeja de saída cheia",
            win32print.PRINTER_STATUS_NOT_AVAILABLE: "Não disponível",
            win32print.PRINTER_STATUS_WAITING: "Aguardando",
            win32print.PRINTER_STATUS_PROCESSING: "Processando",
            win32print.PRINTER_STATUS_INITIALIZING: "Inicializando",
            win32print.PRINTER_STATUS_WARMING_UP: "Aquecendo",
            win32print.PRINTER_STATUS_TONER_LOW: "Toner baixo",
            win32print.PRINTER_STATUS_NO_TONER: "Sem toner",
            win32print.PRINTER_STATUS_PAGE_PUNT: "Page punt",
            win32print.PRINTER_STATUS_USER_INTERVENTION: "Intervenção do usuário necessária",
            win32print.PRINTER_STATUS_OUT_OF_MEMORY: "Memória insuficiente",
            win32print.PRINTER_STATUS_DOOR_OPEN: "Porta aberta",
            win32print.PRINTER_STATUS_SERVER_UNKNOWN: "Servidor desconhecido",
            win32print.PRINTER_STATUS_POWER_SAVE: "Modo de economia de energia"
        }
        for code, message in status_mapping.items():
            if status_code & code:
                status_messages.append(message)
        
        if not status_messages:
            status_messages.append("Pronta")
        
        return status_messages
    
    def _decode_attributes(self, attributes: int) -> List[str]:
        """Decodifica os atributos da impressora"""
        attribute_messages = []
        attribute_mapping = {
            win32print.PRINTER_ATTRIBUTE_QUEUED: "Em fila",
            win32print.PRINTER_ATTRIBUTE_DIRECT: "Direct",
            win32print.PRINTER_ATTRIBUTE_DEFAULT: "Padrão",
            win32print.PRINTER_ATTRIBUTE_SHARED: "Compartilhada",
            win32print.PRINTER_ATTRIBUTE_NETWORK: "Rede",
            win32print.PRINTER_ATTRIBUTE_HIDDEN: "Oculta",
            win32print.PRINTER_ATTRIBUTE_LOCAL: "Local",
            win32print.PRINTER_ATTRIBUTE_ENABLE_DEVQ: "Device queue habilitada",
            win32print.PRINTER_ATTRIBUTE_KEEPPRINTEDJOBS: "Manter trabalhos impressos",
            win32print.PRINTER_ATTRIBUTE_DO_COMPLETE_FIRST: "Completar primeiro",
            win32print.PRINTER_ATTRIBUTE_WORK_OFFLINE: "Trabalhar offline",
            win32print.PRINTER_ATTRIBUTE_ENABLE_BIDI: "Bidirectional habilitado",
            win32print.PRINTER_ATTRIBUTE_RAW_ONLY: "Apenas raw",
            win32print.PRINTER_ATTRIBUTE_PUBLISHED: "Publicada"
        }
        for code, message in attribute_mapping.items():
            if attributes & code:
                attribute_messages.append(message)
        
        return attribute_messages
    
    def _decode_job_status(self, status_code: int) -> List[str]:
        """Decodifica o status do trabalho de impressão"""
        status_messages = []
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
            win32print.JOB_STATUS_RESTART: "Reiniciar"
        }
        for code, message in status_mapping.items():
            if status_code & code:
                status_messages.append(message)
        
        if not status_messages:
            status_messages.append("Na fila")
        
        return status_messages
    
    def test_printer_connection(self, printer_name: str, timeout: int = 10) -> Dict[str, Any]:
        """Testa a conexão com a impressora"""
        result = {
            'printer_name': printer_name,
            'success': False,
            'response_time': 0,
            'error': None
        }
        start_time = time.time()
        
        try:
            handle = win32print.OpenPrinter(printer_name)
            if not handle:
                result['error'] = "Não foi possível abrir a impressora"
                self.logger.warning(f"Falha ao abrir impressora {printer_name}")
                return result
            
            win32print.GetPrinter(handle, 2)
            
            result['success'] = True
            result['response_time'] = time.time() - start_time
            self.logger.info(f"Conexão com a impressora '{printer_name}' bem-sucedida em {result['response_time']:.3f}s")
            
            win32print.ClosePrinter(handle)
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Erro ao testar conexão com a impressora {printer_name}: {e}", exc_info=True)
        
        return result
    
    def __del__(self):
        """Destrutor - fecha todas as conexões abertas"""
        self.close_all_printers()
        self.logger.debug("Destrutor chamado: conexões fechadas.")
