from utils import LockApp
import win32print
from core import (
    PrinterListManager,
    PrinterStatusManager,
    AppLogger,
    PrinterAccessManager,
    PrinterJobManager,
)
import time


def main():
    singleton = LockApp()

    if singleton.is_already_running():
        return

    # Garante inicialização das singletons
    AppLogger()
    PrinterListManager()
    PrinterAccessManager()


if __name__ == "__main__":
    main()

    if not AppLogger.instance:
        raise ImportError("Instância do logger não inicializada")

    logger = AppLogger.instance.get_logger(__name__)

    # Cria instâncias de gerenciadores
    printer_status = PrinterStatusManager()
    printer_job = PrinterJobManager()

    try:
        # Obtém todas as impressoras locais e de rede conectadas
        printers = win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        )
        logger.info(f"Impressoras encontradas: {len(printers)}")

        for i, printer in enumerate(printers, start=1):
            printer_name = printer[2]
            logger.info(f"\n=== Testando impressora {i}: {printer_name} ===")

            # Status inicial da impressora
            status = printer_status.get_printer_status(printer_name)
            logger.info(f"Status inicial: {status['status']}")
            logger.info(f"Jobs encontrados: {status['job_count']}")
            logger.info(f"Online: {status['is_online']}")
            logger.info(f"Pronta: {status['is_ready']}")

            # Teste: Pausar impressora
            logger.info("\n--- Testando pausa da impressora ---")
            success = printer_status.modify_printer_status(printer_name, 'pause')
            if success:
                logger.info("Impressora pausada com sucesso")
                # Verifica status após pausa
                time.sleep(2)  # Aguarda um pouco para a mudança refletir
                status_after_pause = printer_status.get_printer_status(printer_name)
                logger.info(f"Status após pausa: {status_after_pause['status']}")
            else:
                logger.error("Falha ao pausar impressora")

            # Teste: Retomar impressora
            logger.info("\n--- Testando retomada da impressora ---")
            success = printer_status.modify_printer_status(printer_name, 'resume')
            if success:
                logger.info("Impressora retomada com sucesso")
                # Verifica status após retomada
                time.sleep(2)
                status_after_resume = printer_status.get_printer_status(printer_name)
                logger.info(f"Status após retomada: {status_after_resume['status']}")
            else:
                logger.error("Falha ao retomar impressora")

            logger.info(f"\n=== Teste da impressora {printer_name} concluído ===\n")

    except Exception as e:
        logger.error(f"Erro durante teste: {e}", exc_info=True)

    logger.info("Teste completo da modify_printer_status concluído")