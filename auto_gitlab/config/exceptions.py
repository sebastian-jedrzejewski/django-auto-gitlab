class IncorrectConfigFormatError(Exception):
    pass


class NoEnvironmentVariableError(Exception):
    pass


class GitlabConfigFileNotFoundError(Exception):
    pass


class GitlabConfigFileEmptyError(Exception):
    pass
