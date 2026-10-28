VALID_SEVERITIES = ("Low", "Medium", "High")
VALID_STATUSES = ("Open", "Under Investigation", "Resolved")

def validate_incident(record):
    if not record.get("title"):
        return "Incident title is required."
    if len(record["title"]) > 100:
        return "Title must be 100 characters or fewer."
    if len(record.get("description", "")) > 500:
        return "Description must be 500 characters or fewer."
    if not record.get("category"):
        return "Choose an incident category."
    if record.get("severity") not in VALID_SEVERITIES:
        return "Choose a valid severity."
    if not record.get("reporter"):
        return "Reporter name is required."
    if len(record["reporter"]) > 100:
        return "Reporter name must be 100 characters or fewer."
    return None
