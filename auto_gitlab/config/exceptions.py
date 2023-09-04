class IncorrectConfigFormatError(Exception):
    pass


class NoEnvironmentVariableError(Exception):
    pass


class GitlabConfigFileNotFound(Exception):
    pass


class GitlabConfigFileEmpty(Exception):
    pass
