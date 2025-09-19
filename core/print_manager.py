from typing import Dict, Any, List, Optional
import tempfile
import os
import time
from datetime import datetime, timedelta
from docx import Document
import pythoncom
import win32api
import win32print

class PrinterPrint:
    """Classe para imprimir documentos DOCX e monitorar jobs de impressão"""
    
    def __init__(self, PCA, logger_instance):
        self.logger = logger_instance.get_logger(__name__)
        self.access_manager = PCA
        from .printer_job_manager import PrinterJobManager
        self.job_manager = PrinterJobManager()
    
    def create_blank_docx(self) -> str:
        """
        Cria um documento DOCX em branco temporário
        
        Returns:
            Caminho do arquivo temporário criado
        """
        try:
            # Cria documento em branco
            doc = Document()
            
            # Adiciona uma página em branco (documento vazio já é uma página em branco)
            doc.add_paragraph(" ")  # Parágrafo vazio
            
            # Salva em arquivo temporário
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f"blank_page_{int(time.time())}.docx")
            
            doc.save(temp_file)
            self.logger.info(f"Documento em branco criado: {temp_file}")
            
            return temp_file
            
        except Exception as e:
            self.logger.error(f"Erro ao criar documento em branco: {e}", exc_info=True)
            raise
    
    def print_blank_page(self, printer_name: str, copies: int = 1, timeout_seconds: int = 30) -> Dict[str, Any]:
        """
        Imprime uma página em branco usando documento DOCX e monitora o status
        
        Args:
            printer_name: Nome da impressora
            copies: Número de cópias
            timeout_seconds: Tempo máximo para aguardar conclusão
            
        Returns:
            Dict com informações detalhadas sobre a impressão
        """
        result = {
            'success': False,
            'printer_name': printer_name,
            'error': None,
            'job_ids': [],
            'copies': copies,
            'job_statuses': [],
            'completed': False,
            'timeout_reached': False,
            'temp_file': None,
            'paper_out_error': False  # Nova flag para indicar erro de falta de papel
        }
        
        temp_file_path = None
        
        try:
            # Cria documento DOCX em branco
            temp_file_path = self.create_blank_docx()
            result['temp_file'] = temp_file_path
            
            # Inicializa COM para operações com Word (se necessário)
            pythoncom.CoInitialize()
            
            # Usa o comando de impressão do Windows para o arquivo DOCX
            job_ids = self._print_docx_file(temp_file_path, printer_name, copies)
            
            if job_ids:
                result['job_ids'] = job_ids
                result['success'] = True
                
                # Monitorar status dos jobs com callback para verificar erros
                monitor_result = self._monitor_jobs_with_paper_check(printer_name, job_ids, timeout_seconds)
                
                # Atualiza resultado com informações do monitoramento
                result.update(monitor_result)
                
            else:
                result['error'] = "Nenhum job de impressão foi criado"
                self.logger.error(result['error'])
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Erro ao imprimir página em branco na impressora '{printer_name}': {e}", exc_info=True)
        
        finally:
            # Limpeza do arquivo temporário
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    self.logger.info(f"Arquivo temporário removido: {temp_file_path}")
                except Exception as e:
                    self.logger.warning(f"Erro ao remover arquivo temporário: {e}")
            
            # Finaliza COM
            try:
                pythoncom.CoUninitialize()
            except:
                pass
        
        return result

    def _monitor_jobs_with_paper_check(self, printer_name: str, job_ids: List[int], timeout_seconds: int) -> Dict[str, Any]:
        """
        Monitora jobs específicos verificando especificamente por erro de falta de papel
        
        Args:
            printer_name: Nome da impressora
            job_ids: Lista de IDs de jobs para monitorar
            timeout_seconds: Tempo máximo de monitoramento
            
        Returns:
            Dict com resultados do monitoramento
        """
        result = {
            'completed': False,
            'timeout_reached': False,
            'paper_out_error': False,
            'job_statuses': [],
            'final_error': None
        }
        
        start_time = time.time()
        paper_error_detected = False
        
        # Função callback para processar mudanças nos jobs
        def job_callback(job_change):
            nonlocal paper_error_detected
            
            if job_change['type'] == 'JOB_UPDATED':
                job_info = job_change['job_info']
                status_code = job_info['status_code']
                
                # Verifica se há erro de falta de papel (código de status 5 + verificação específica)
                if status_code == 5:  # JOB_STATUS_ERROR
                    error_message = job_info.get('status', '').lower()
                    if any(paper_error in error_message for paper_error in ['paper', 'papel', 'out of paper', 'sem papel']):
                        paper_error_detected = True
                        self.logger.warning(f"Erro de falta de papel detectado no job {job_info['job_id']}")
        
        # Inicia monitoramento específico para os jobs
        self.job_manager.monitor_jobs(
            printer_name=printer_name,
            callback=job_callback,
            interval=2,  # Verifica a cada 2 segundos
            specific_job_ids=job_ids,
            monitor_all=False  # Monitora apenas os jobs específicos
        )
        
        try:
            while time.time() - start_time < timeout_seconds:
                # Verifica status atual de todos os jobs monitorados
                current_statuses = []
                all_completed = True
                any_error = False
                
                for job_id in job_ids:
                    job_info = self.job_manager.get_job(printer_name, job_id)
                    if job_info:
                        current_statuses.append(job_info)
                        
                        # Verifica se job está completo (status 4) ou com erro (status 5)
                        status_code = job_info['status_code']
                        if status_code not in [4, 5]:  # 4 = JOB_STATUS_COMPLETE, 5 = JOB_STATUS_ERROR
                            all_completed = False
                        elif status_code == 5:
                            any_error = True
                
                result['job_statuses'] = current_statuses
                
                # Se todos os jobs completaram ou há erro de papel, para o monitoramento
                if all_completed or paper_error_detected:
                    result['completed'] = all_completed
                    result['paper_out_error'] = paper_error_detected
                    if any_error and not paper_error_detected:
                        result['final_error'] = "Erro de impressão detectado"
                    break
                
                time.sleep(1)  # Aguarda 1 segundo entre verificações
                
            else:
                result['timeout_reached'] = True
                result['final_error'] = f"Timeout de {timeout_seconds} segundos atingido"
                
        finally:
            # Para o monitoramento
            self.job_manager.stop_monitoring()
        
        return result
    
    def _print_docx_file(self, file_path: str, printer_name: str, copies: int) -> List[int]:
        """
        Imprime um arquivo DOCX usando o comando de impressão do Windows
        
        Args:
            file_path: Caminho do arquivo DOCX
            printer_name: Nome da impressora
            copies: Número de cópias
            
        Returns:
            Lista de IDs de jobs criados
        """
        job_ids = []
        
        try:
            # Usa o comando de impressão nativo do Windows
            for copy in range(copies):
                # Comando para imprimir o arquivo
                win32api.ShellExecute(
                    0,              # hwnd
                    "print",        # operation
                    file_path,      # file
                    f'"{printer_name}"',  # parameters (printer name)
                    ".",            # directory
                    0               # show command
                )
                
                self.logger.info(f"Cópia {copy + 1} enviada para impressora '{printer_name}'")
                
                # Pequena pausa entre cópias
                time.sleep(3)
            
            # Para obter os job IDs, precisamos verificar os jobs recém-criados
            time.sleep(2)  # Aguarda um pouco para os jobs aparecerem
            
            # Obtém jobs atuais usando o job_manager
            current_jobs = self.job_manager.list_jobs(printer_name)
            job_ids = [job['job_id'] for job in current_jobs]
            
        except Exception as e:
            self.logger.error(f"Erro ao imprimir arquivo DOCX: {e}", exc_info=True)
            raise
        
        return job_ids
    