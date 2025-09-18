from typing import Dict, Any
from hamcrest import instance_of
import win32print


class PrinterPrint:
    """Classe para imprimir"""
    
    def __init__(self, PCA, logger_instance):
        self.logger = logger_instance.get_logger(__name__)
        self.printer_manager = PCA
    def print_blank_page(self, printer_name: str, copies: int = 1) -> Dict[str, Any]:
        """
        Imprime uma página em branco usando comando raw com formatação adequada
        
        Returns:
            Dict com informações sobre o resultado da impressão
        """
        result = {
            'success': False,
            'printer_name': printer_name,
            'error': None,
            'job_ids': [],
            'copies': copies
        }
        
        try:
            # Abre a impressora
            handle = self.printer_manager.open_printer(printer_name)
            if not handle:
                result['error'] = f"Não foi possível abrir a impressora '{printer_name}'"
                self.logger.error(result['error'])
                return result
            
            # Comandos PCL mais robustos para página em branco
            blank_page_data = (
                b"\x1B%-12345X"  # Início do trabalho PCL
                b"@PJL ENTER LANGUAGE=PCL\r\n"
                b"\x1B&l0O"      # Orientação retrato
                b"\x1B&l0E"      # Tamanho carta
                b"\x1B&l0L"      # Modo lógico
                b"\x1B*f0S"      # Velocidade normal
                b"\x1B*t0R"      # Resolução normal
                b"\x1B*r0F"      # Sem fonte específica
                b"\x1B&a0R"      # Posição inicial
                b"\x1B&k0G"      # Preto e branco
                b"\x1B*r0U"      # Sem underline
                b"\x0C"          # Form Feed (avançar página)
                b"\x1B%-12345X"  # Fim do trabalho PCL
            )
            
            for copy in range(copies):
                # CORREÇÃO: A tupla deve ter 3 strings, não pode ter None
                job_info = ("Página em Branco", "blank_page.pcl", "RAW")
                job_id = win32print.StartDocPrinter(handle, 1, job_info)
                win32print.StartPagePrinter(handle)
                win32print.WritePrinter(handle, blank_page_data)
                win32print.EndPagePrinter(handle)
                win32print.EndDocPrinter(handle)
                
                result['job_ids'].append(job_id)
                self.logger.info(f"Cópia {copy + 1} de página em branco enviada para '{printer_name}' (Job ID: {job_id})")
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Erro ao imprimir página em branco na impressora '{printer_name}': {e}", exc_info=True)
        
        finally:
            self.printer_manager.close_printer(printer_name)
        
        return result