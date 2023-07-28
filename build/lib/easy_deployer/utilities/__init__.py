from typing import TypedDict

class ERROR_CODE(TypedDict):
    invalid_path: int
    missing_gitignore_file: int
    repository_not_found: int
    token_file_not_found: int
    token_is_none: int
    command_not_found: int
    double_quotes_not_allowed: int

ERROR_CODES: ERROR_CODE = {
    "invalid_path": 1,
    "missing_gitignore_file": 2,
    "repository_not_found": 3,
    "token_file_not_found": 4,
    "token_is_none": 5,
    "command_not_found": 6,
    "double_quotes_not_allowed": 7
}