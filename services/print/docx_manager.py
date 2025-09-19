from docx import Document
import tempfile
import os
import time
from typing import Optional

class DocxManager:
    """Gerencia criação e remoção de arquivos DOCX temporários"""

    def __init__(self, logger_instance):
        self.logger = logger_instance.get_logger(__name__)
    def create_blank_docx(self) -> str:
        """Cria um documento DOCX em branco temporário"""
        try:
            doc = Document()
            doc.add_paragraph(" ")  # adiciona parágrafo vazio

            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f"blank_page_{int(time.time())}.docx")

            doc.save(temp_file)
            self.logger.info(f"Documento em branco criado: {temp_file}")
            return temp_file

        except Exception as e:
            self.logger.error(f"Erro ao criar documento em branco: {e}", exc_info=True)
            raise
    def delete_docx(self, file_path: str) -> bool:
        """Remove arquivo DOCX temporário"""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info(f"Arquivo temporário removido: {file_path}")
                return True
            return False
        except Exception as e:
            self.logger.warning(f"Erro ao remover arquivo temporário {file_path}: {e}")
            return False
