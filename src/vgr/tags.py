"""
Application tags
"""

#pylint: disable=protected-access
def control_statement(func):
    """
    Used with statement handlers to
    indicate the function works with control statements,
    not a "simple" statement. This alters the way
    the statement is processed prior to calling the
    handler.
    Notably, the handler will need to bind operations
    itself and decide the behavior of echo.
    """
    func._is_control_statement = True
    return func
#pylint: enable=protected-access
