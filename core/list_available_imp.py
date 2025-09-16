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

    def extract_printer_model(self, printer_name: str) -> Optional[str]:
        """
        Extrai o modelo da impressora a partir do nome completo
        
        Args:
            printer_name: Nome completo da impressora
            
        Returns:
            String com o modelo da impressora ou None se não encontrado
        """
        # Padrões comuns para detectar modelos de impressora
        patterns = [
            # Padrão EPSON L3250, L4260, etc.
            r'\b(L[0-9]{3,4})\b',
            # Padrão HP Deskjet 2700, Laserjet MFP M28w, etc.
            r'\b([A-Za-z]+ [0-9]+[a-zA-Z]*)\b',
            # Padrão Canon PIXMA G3600, MG3600, etc.
            r'\b([A-Z]{2,}[0-9]+)\b',
            # Padrão Brother DCP-L2550DW, MFC-L8900CDW, etc.
            r'\b([A-Z]{3}-[A-Z]?[0-9]+[A-Z]*)\b',
            # Padrão Samsung SL-M4070FR, etc.
            r'\b([A-Z]{2}-[A-Z]?[0-9]+[A-Z]*)\b'
        ]
        
        import re
        
        for pattern in patterns:
            match = re.search(pattern, printer_name)
            if match:
                return match.group(1)
        
        return None

    def list_printer_models(self) -> List[dict]:
        """
        Lista todos os modelos de impressora detectados
        
        Returns:
            Lista de dicionários com informações dos modelos
        """
        if self.organized_data is None:
            self.organize_printer_data()
        
        printer_models = []
        
        for printer in self.organized_data: # type: ignore
            model = self.extract_printer_model(printer['full_name'])
            if not model:
                model = self.extract_printer_model(printer['display_name'])
            
            printer_info = {
                'display_name': printer['display_name'],
                'full_name': printer['full_name'],
                'model': model,
                'type': printer['type'],
                'protocol': printer['protocol']
            }
            printer_models.append(printer_info)
        
        return printer_models

    def get_printers_by_model(self, model_pattern: str) -> List[dict]:
        """
        Filtra impressoras por padrão de modelo
        
        Args:
            model_pattern: Padrão do modelo a ser buscado (ex: "L3250", "EPSON")
            
        Returns:
            Lista de impressoras que correspondem ao padrão
        """
        if self.organized_data is None:
            self.organize_printer_data()
        
        import re
        
        matched_printers = []
        
        for printer in self.organized_data: # type: ignore
            # Verifica no nome completo
            if re.search(model_pattern, printer['full_name'], re.IGNORECASE):
                matched_printers.append(printer)
                continue
            
            # Verifica no nome de exibição
            if re.search(model_pattern, printer['display_name'], re.IGNORECASE):
                matched_printers.append(printer)
                continue
            
            # Verifica no modelo extraído
            model = self.extract_printer_model(printer['full_name'])
            if model and re.search(model_pattern, model, re.IGNORECASE):
                matched_printers.append(printer)
        
        return matched_printers