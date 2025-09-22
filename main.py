from utils import LockApp
from core import ( PrinterListManager, PrinterStatusManager, AppLogger, PrinterAccessManager, PrinterJobManager)

def main():
    singleton = LockApp()

    if singleton.is_already_running():
        raise RuntimeError("Aplicativo já está em execução")

    # Garante inicialização das singletons
    AppLogger()
    PrinterListManager()
    PrinterAccessManager()

def test():
    access_manager = PrinterAccessManager.instance
    printer_list = PrinterListManager.instance

    if not AppLogger.instance or not printer_list:
        raise ImportError("Instância do logger não inicializada")

    logger = AppLogger.instance.get_logger(__name__)

    # Cria instâncias de gerenciadores
    printer_status = PrinterStatusManager(access_manager)
    printer_job = PrinterJobManager()

    # Obtém lista de impressoras
    printers = printer_list.list_name_printers()

    if not printers:
        logger.error("Nenhuma impressora encontrada no sistema")
        return
    
    logger.info("Impressoras disponíveis: %d", len(printers))
    for i, printer in enumerate(printers, 1):
        logger.debug("Impressora %d: %s", i, printer)
    
    # Testa a primeira impressora
    printer_name = printers[0]
    logger.info("Testando verificação de papel na impressora: '%s'", printer_name)
    
    jobs = printer_job.list_jobs(printer_name)
    if len(jobs) > 0:
        printer_job.cancel_all_jobs(printer_name)
    
    
    try:
        # Verifica status do papel
        paper_status = printer_status.check_paper_status(printer_name, force_update=True)
        
        # Exibe resultados de forma clara usando logger
        logger.info("STATUS DO PAPEL - %s", printer_name)
        logger.info("• Papel disponível: %s", "SIM" if paper_status.get('paper_available') else "NÃO")
        logger.info("• Papel esgotado: %s", "SIM" if paper_status.get('paper_out') else "NÃO")
        logger.info("• Papel encravado: %s", "SIM" if paper_status.get('paper_jam') else "NÃO")
        logger.info("• Papel baixo: %s", "SIM" if paper_status.get('paper_low') else "NÃO")
        
        # Verifica se há erro
        if 'error' in paper_status:
            logger.warning("Erro na verificação: %s", paper_status['error'])
        
        # Resumo do status
        if paper_status.get('paper_available'):
            if paper_status.get('paper_low'):
                logger.warning("Papel disponível, mas quantidade baixa")
            else:
                logger.info("Papel disponível e em bom estado")
        else:
            if paper_status.get('paper_out'):
                logger.error("PAPEL ESGOTADO - Inserir novo papel")
            if paper_status.get('paper_jam'):
                logger.error("PAPEL ENCRAVADO - Verificar impressora")
            if paper_status.get('error'):
                logger.error("Erro na verificação: %s", paper_status['error'])
        
        # Log detalhado para debug
        logger.debug("Estado completo do papel: %s", paper_status)
        
    except Exception as e:
        logger.error("Erro durante a verificação de papel: %s", e, exc_info=True)

if __name__ == "__main__":
    try:
        main()
        test()
    except Exception as e:
        logger = AppLogger.instance.get_logger(__name__) if AppLogger.instance else None
        if logger:
            logger.critical("Erro fatal: %s", e, exc_info=True)
        else:
            print(f"Erro fatal: {e}")