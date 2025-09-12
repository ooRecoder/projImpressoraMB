from asyncio.windows_events import NULL
from typing import List, Tuple, Optional
from utils import Singleton
import win32print

@Singleton
class PrinterListManager:
    """Classe para gerenciar e organizar informações de impressoras"""
    
    def __init__(self):
        self.raw_data = None
        self.organized_data = None
    
    def list_available_printers(self) -> Tuple:
        """
        Lista todas as impressoras disponíveis e retorna os dados brutos
        
        Returns:
            Tuple com dados brutos das impressoras
        """
        self.raw_data = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL, None, 1)
        return self.raw_data
    
    def organize_printer_data(self, printer_data: Optional[Tuple] = None) -> List[dict]:
        """
        Organiza os dados das impressoras em formato estruturado
        
        Args:
            printer_data: Dados brutos das impressoras (opcional)
            
        Returns:
            Lista de dicionários com informações organizadas
        """
        if printer_data is None:
            if self.raw_data is None:
                self.list_available_printers()
            printer_data = self.raw_data
        
        organized_printers = []
        
        for printer in printer_data: # type: ignore
            full_name = printer[1]
            printer_info = {
                'id': printer[0],
                'full_name': full_name,
                'display_name': printer[2],
                'description': printer[3],
                'type': 'network' if any(x in full_name for x in ['http://', 'WSD']) else 'local',
                'protocol': self._detect_protocol(full_name)
            }
            organized_printers.append(printer_info)
        
        self.organized_data = organized_printers
        return organized_printers
    
    def _detect_protocol(self, full_name: str) -> str:
        """Detecta o protocolo da impressora baseado no nome completo"""
        if 'WSD' in full_name:
            return 'WSD'
        elif 'IPP' in full_name:
            return 'IPP'
        elif 'http://' in full_name or 'https://' in full_name:
            return 'HTTP'
        else:
            return 'unknown'
    
    def list_name_printers(self, printer_data: Optional[Tuple] = None) -> List[str]:
        """
        Extrai apenas os nomes das impressoras
        
        Args:
            printer_data: Dados brutos das impressoras (opcional)
            
        Returns:
            Lista com os nomes das impressoras
        """
        if printer_data is None:
            if self.raw_data is None:
                self.list_available_printers()
            printer_data = self.raw_data
        
        return [printer[2] for printer in printer_data] # type: ignore
    
    def get_printer_by_name(self, name: str) -> Optional[dict]:
        """
        Retorna informações de uma impressora específica pelo nome
        
        Args:
            name: Nome da impressora a ser buscada
            
        Returns:
            Dicionário com informações da impressora ou None se não encontrada
        """
        if self.organized_data is None:
            self.organize_printer_data()
        
        for printer in self.organized_data: # type: ignore
            if printer['display_name'] == name:
                return printer
        return None
    
    def get_network_printers(self) -> List[dict]:
        """
        Retorna apenas impressoras de rede
        
        Returns:
            Lista de impressoras de rede
        """
        if self.organized_data is None:
            self.organize_printer_data()
        
        return [printer for printer in self.organized_data if printer['type'] == 'network'] # type: ignore
    
    def get_local_printers(self) -> List[dict]:
        """
        Retorna apenas impressoras locais
        
        Returns:
            Lista de impressoras locais
        """
        if self.organized_data is None:
            self.organize_printer_data()
        
        return [printer for printer in self.organized_data if printer['type'] == 'local'] # type: ignore

