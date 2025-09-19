from services import PrinterJobMonitor, PrinterJobHistory, PrinterJobManager, PrinterPrint
class BasePrinter:
    def __init__(self, print_name, access_manager, logger_instance) -> None:
        self.printer_name = print_name
        self.logger = logger_instance.get_logger(__name__)
        self.access_manager = access_manager
        self.job_manager = PrinterJobManager()
        self.job_monitor = PrinterJobMonitor()
        self.job_history = PrinterJobHistory()
        self.print_manager = PrinterPrint(access_manager, logger_instance)
    def get_job(self, job_id:int):
        return self.job_manager.get_job(self.printer_name, job_id)
    def list_jobs(self):
        return self.job_manager.list_jobs(self.printer_name)
    def cancel_job(self, job_id: int):
        return self.job_manager.cancel_job(self.printer_name, job_id)
    def cancel_all_jobs(self):
        return self.job_manager.cancel_all_jobs(self.printer_name)
    def pause_job(self, job_id: int):
        return self.job_manager.pause_job(self.printer_name, job_id)
    def resume_job(self, job_id: int):
        return self.job_manager.resume_job(self.printer_name, job_id)
    def restart_job(self, job_id: int):
        return self.job_manager.restart_job(self.printer_name, job_id)
    def test_printer_connection(self):
        return
    def getMonitorJob(self):
        return self.job_monitor
    def get_history_jobs(self, hour_back: int = 24):
        return self.job_history.get_job_history(self.printer_name, hour_back)
    def print_blank_page(self, copies: int = 1):
        return self.print_manager.print_blank_page(self.printer_name, copies)
    