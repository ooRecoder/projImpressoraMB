from utils import LockApp
import win32print
from core import PrinterListManager, PrinterStatusManager, AppLogger

def main():
    singleton = LockApp()
    
    if singleton.is_already_running():
        return

    AppLogger()
    PrinterListManager()
    

if __name__ == "__main__":
    # Inicializa o logger
    
    main()
    
    if not AppLogger.instance:
        raise ImportError("Instancia do logger não inicializada")
    logger = AppLogger.instance.get_logger(__name__)
    
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