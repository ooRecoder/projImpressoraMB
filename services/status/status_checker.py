import win32print
from typing import Dict
from core import AppLogger, PrinterStatus


class PrinterStatusChecker:
    """Consulta status geral da impressora"""

    def __init__(self, access_manager):
        self.logger = AppLogger.instance.get_logger(__name__)  # type: ignore
        self.access_manager = access_manager
    def get_printer_status(self, printer_name: str) -> Dict:
        handle = self.access_manager.open_printer(printer_name)  # type: ignore
        if not handle:
            return {
                "status": PrinterStatus.UNKNOWN,
                "details": "Impressora não disponível",
                "is_online": False,
                "is_ready": False,
            }

        try:
            printer_info = win32print.GetPrinter(handle, 2)
            status_list = self.access_manager._decode_status(printer_info["Status"])  # type: ignore
            attributes_list = self.access_manager._decode_attributes(printer_info["Attributes"])  # type: ignore

            return {
                "status": status_list,
                "status_code": printer_info["Status"],
                "is_online": not bool(printer_info["Status"] & win32print.PRINTER_STATUS_OFFLINE),
                "is_ready": printer_info["Status"] == 0,
                "attributes": attributes_list,
                "printer_name": printer_name,
                "server_name": printer_info["pServerName"],
                "share_name": printer_info["pShareName"],
                "port_name": printer_info["pPortName"],
                "driver_name": printer_info["pDriverName"],
                "location": printer_info["pLocation"],
                "comment": printer_info["pComment"],
            }
        except Exception as e:
            self.logger.error(f"Erro ao obter status da impressora {printer_name}: {e}", exc_info=True)
            return {
                "status": [PrinterStatus.ERROR.name],
                "details": f"Erro ao obter status: {e}",
                "is_online": False,
                "is_ready": False,
            }
        finally:
            self.access_manager.close_printer(printer_name)  # type: ignore

