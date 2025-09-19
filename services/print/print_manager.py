from typing import Dict, Any
import time
import pythoncom
import win32api

from .docx_manager import DocxManager


class PrinterPrint:
    """Classe para imprimir documentos DOCX"""

    def __init__(self, PCA, logger_instance):
        self.logger = logger_instance.get_logger(__name__)
        self.access_manager = PCA
        self.docx_manager = DocxManager(logger_instance)

    def print_blank_page(self, printer_name: str, copies: int = 1) -> Dict[str, Any]:
        """
        Imprime uma página em branco usando documento DOCX
        """
        result = {
            'success': False,
            'printer_name': printer_name,
            'error': None,
            'copies': copies,
            'temp_file': None
        }

        temp_file_path = None
        try:
            temp_file_path = self.docx_manager.create_blank_docx()
            result['temp_file'] = temp_file_path

            pythoncom.CoInitialize()

            # Imprime o arquivo temporário
            self._print_docx_file(temp_file_path, printer_name, copies)

            result['success'] = True
            self.logger.info(f"Página em branco enviada para {printer_name}")

        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Erro ao imprimir página em branco em {printer_name}: {e}", exc_info=True)

        finally:
            if temp_file_path:
                self.docx_manager.delete_docx(temp_file_path)

            try:
                pythoncom.CoUninitialize()
            except:
                pass

        return result

    def _print_docx_file(self, file_path: str, printer_name: str, copies: int) -> None:
        """Envia DOCX para impressão no Windows"""
        try:
            for copy in range(copies):
                win32api.ShellExecute(
                    0,
                    "print",
                    file_path,
                    f'"{printer_name}"',
                    ".",
                    0
                )
                self.logger.info(f"Cópia {copy + 1} enviada para {printer_name}")
                time.sleep(2)

        except Exception as e:
            self.logger.error(f"Erro ao imprimir DOCX: {e}", exc_info=True)
            raise
