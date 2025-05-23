
class classproperty(object):
    """
    A decorator that allows a method to be accessed as a class-level property
    rather than on instances of the class.
    """

    def __init__(self, f):
        """
        Initializes the classproperty with the given function.

        Args:
            f (function): The function to be used as a class-level property.
        """
        self.f = f

    def __get__(self, obj, owner):
        """
        Retrieves the value of the class-level property.

        Args:
            obj: The instance of the class (ignored in this context).
            owner: The class that owns the property.

        Returns:
            The result of calling the decorated function with the class as an argument.
        """
        return self.f(owner)
