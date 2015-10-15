class UnknownRepoException(BaseException):
    pass

class CircularDepsException(BaseException):
    pass

class MissingRecipeException(BaseException):
    pass

class DownloadFailException(BaseException):
    pass

class BuildFailureException(BaseException):
    pass
