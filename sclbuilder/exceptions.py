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

class IncompleteMetadataException(BaseException):
    pass

class UnknownPluginException(BaseException):
    pass
