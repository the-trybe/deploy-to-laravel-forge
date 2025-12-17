import os
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

    def _normalize_coerce_relative_path(self, value):
        """
        Coerce function to convert absolute paths to relative paths.
        
        - Strips leading slashes to make absolute paths relative
        - Expands ~ to remove home directory prefix
        - Normalizes the path
        """
        if not value or not isinstance(value, str):
            return value
        
        # Expand ~ if present
        if value.startswith("~"):
            # Just remove the ~ and following slash
            value = value.lstrip("~/").lstrip("~")
        
        # Remove leading slashes to make it relative
        value = value.lstrip("/")
        
        # Normalize the path (remove redundant separators and up-level references)
        value = os.path.normpath(value)
        
        # If normpath resulted in ".", keep it as is, otherwise ensure it's not empty
        if value == "" or value == "/":
            value = "."
            
        return value
