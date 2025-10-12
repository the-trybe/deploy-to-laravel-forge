from cerberus import Validator


class ConfigValidator(Validator):
    """Cerberus validator with additional validation rules."""

    def _validate_isolation_user_required(self, constraint, field, value):
        """
        Custom validation rule to ensure isolation_user is present when website_isolation is True.
        
        The rule's arguments are validated against this schema:
        {'type': 'boolean'}
        """
        if constraint and value is True:
            # Check if isolation_user is present and not empty
            isolation_user = self.document.get('isolation_user')
            if not isolation_user or (isinstance(isolation_user, str) and isolation_user.strip() == ''):
                self._error(field, "isolation_user is required when website_isolation is True")

