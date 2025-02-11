class DynamoDbValidators:

    @staticmethod
    def is_valid_iso8601_string(date_string:str) -> bool:
        try:
            parser.isoparse(date_string)
            return True
        except ValueError:
            return False

if __name__ == "__main__":
    pass