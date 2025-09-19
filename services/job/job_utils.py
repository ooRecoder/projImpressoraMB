from typing import Dict, List
from datetime import datetime

def detect_job_changes(old_jobs: Dict[int, Dict], new_jobs: Dict[int, Dict]) -> List[Dict]:
    changes = []
    now = datetime.now().isoformat()

    for job_id, job in new_jobs.items():
        if job_id not in old_jobs:
            changes.append({"type": "JOB_ADDED", "job_id": job_id, "job_info": job, "timestamp": now})

    for job_id in old_jobs:
        if job_id not in new_jobs:
            changes.append({"type": "JOB_REMOVED", "job_id": job_id, "timestamp": now})

    for job_id, new_job in new_jobs.items():
        if job_id in old_jobs:
            old_job = old_jobs[job_id]
            if old_job["status_code"] != new_job["status_code"] or old_job["pages_printed"] != new_job["pages_printed"]:
                changes.append({
                    "type": "JOB_UPDATED",
                    "job_id": job_id,
                    "old_status": old_job["status"],
                    "new_status": new_job["status"],
                    "old_status_code": old_job["status_code"],
                    "new_status_code": new_job["status_code"],
                    "old_pages_printed": old_job["pages_printed"],
                    "new_pages_printed": new_job["pages_printed"],
                    "job_info": new_job,
                    "timestamp": now
                })
    return changes
