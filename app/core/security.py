from pydantic import field_validator

    @field_validator('ALLOWED_IPS', 'BLOCKED_IPS', 'ALLOWED_COUNTRIES')
    @classmethod
    def validate_ip_lists(cls, v):
        # (Lógica original aquí, si existe)
        return v 