from cerberus import Validator


class ConfigValidator(Validator):
    """Cerberus validator with additional validation rules."""

    def _validate_isolated_user_required(self, constraint, field, value):
        """
        Custom validation rule to ensure isolated_user is present when isolated is True.

        The rule's arguments are validated against this schema:
        {'type': 'boolean'}
        """
        if constraint and value is True:
            # Check if isolated_user is present and not empty
            isolated_user = self.document.get("isolated_user")
            if not isolated_user or (
                isinstance(isolated_user, str) and isolated_user.strip() == ""
            ):
                self._error(field, "isolated_user is required when isolated is True")
