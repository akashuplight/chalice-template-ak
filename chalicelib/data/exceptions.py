class ValidationError(Exception):
    def __init__(self, prop_name, value):
        super().__init__(f'Invalid value for {prop_name or "property"}: {value}')
