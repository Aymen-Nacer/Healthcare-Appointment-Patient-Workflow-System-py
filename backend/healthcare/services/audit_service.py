from healthcare.models import AuditLog


def log_audit(action, performed_by_user_id, entity_name, entity_id, metadata=None):
    AuditLog.objects.create(
        action=action,
        performed_by_user_id=performed_by_user_id,
        entity_name=entity_name,
        entity_id=entity_id,
        metadata=metadata,
    )
