from typing import Dict
def format_job_info(job, access_manager) -> Dict:
    return {
        "job_id": job["JobId"],
        "document_name": job["pDocument"],
        "status": access_manager._decode_job_status(job["Status"]),  # type: ignore
        "status_code": job["Status"],
        "pages_printed": job["PagesPrinted"],
        "total_pages": job["TotalPages"],
        "submitted_time": job["Submitted"].isoformat() if job["Submitted"] else None,
        "user_name": job["pUserName"],
        "machine_name": job["pMachineName"],
        "data_type": job["pDatatype"],
        "priority": job["Priority"]
    }
