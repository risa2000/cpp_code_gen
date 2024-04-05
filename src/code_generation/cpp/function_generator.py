from code_generation.cpp.language_element import CppLanguageElement, CppDeclaration, CppImplementation
from textwrap import dedent


class CppFunction(CppLanguageElement):
    """
    The Python class that generates string representation for C++ function (not method!)
    Parameters are passed as plain strings('int a', 'void p = NULL' etc.)
    Available properties:
    ret_type - string, return value for the method ('void', 'int'). Could not be set for constructors
    is_constexpr - boolean, const method prefix
    documentation - string, '/// Example doxygen'
    implementation - reference to a function that receives 'self' and C++ code generator handle
    (see code_generator.cpp) and generates method body without braces
    Ex.
    #Python code
    def functionBody(self, cpp): cpp('return 42;')
    f1 = CppFunction(name = 'GetAnswer',
                     ret_type = 'int',
                     documentation = '// Generated code',
                     implementation = functionBody)

    // Generated code
    int GetAnswer()
    {
        return 42;
    }
    """

    PROPERTIES = CppLanguageElement.PROPERTIES | \
        {
            "ret_type",
            "is_constexpr",
            "arguments",
            "implementation",
            "documentation",
        }

    def __init__(self, **properties):
        # arguments are plain strings
        # e.g. 'int* a', 'const string& s', 'size_t sz = 10'
        self.ret_type = None
        self.is_constexpr = False
        self.arguments = []
        self.implementation = None
        self.documentation = None
        self.init_properties(properties)

    def _sanity_check(self):
        """
        Check whether attributes compose a correct C++ code
        """
        if self.is_constexpr and self.implementation is None:
            raise ValueError(f"Constexpr function {self.name} must have implementation")

    def _constexpr(self):
        """
        Before function name, declaration only
        Constexpr functions can't be const, virtual or pure virtual
        """
        return "constexpr" if self.is_constexpr else ""

    def args(self):
        """
        @return: string arguments
        """
        return ", ".join(self.arguments)

    def add_argument(self, argument):
        """
        @param: argument string representation of the C++ function argument ('int a', 'void p = nullptr' etc.)
        """
        self.arguments.append(argument)

    def body(self, cpp):
        """
        The method calls Python function that creates C++ method body if handle exists
        """
        if self.implementation is not None:
            self.implementation(self, cpp)

    def declaration(self):
        """
        @return: CppDeclaration wrapper, that could be used
        for declaration rendering using render_to_string(cpp) interface
        """
        return CppDeclaration(self)

    def definition(self):
        """
        @return: CppImplementation wrapper, that could be used
        for definition rendering using render_to_string(cpp) interface
        """
        return CppImplementation(self)

    def render_to_string(self, cpp):
        """
        By function method is rendered as a declaration together with implementation
        void f()
        {
            ...
        }
        """
        # check all properties for the consistency
        self._sanity_check()
        if self.documentation:
            cpp(dedent(self.documentation))
        with cpp.block(
                f"{self._constexpr()}"
                f"{self.ret_type} "
                f"{self.name}"
                f"({self.args()})"
        ):
            self.implementation(cpp)

    def render_to_string_declaration(self, cpp):
        """
        Special case for a function declaration string representation.
        Generates just a function signature terminated by ';'
        Example:
        int GetX();
        """
        # check all properties for the consistency
        if self.is_constexpr:
            if self.documentation:
                cpp(dedent(self.documentation))
            self.render_to_string(cpp)
        else:
            cpp(
                f"{self._constexpr()} "
                f"{self.ret_type} "
                f"{self.name}"
                f"({self.args()});"
            )

    def render_to_string_implementation(self, cpp):
        """
        Special case for a function implementation string representation.
        Generates function string in the form
        Example:
        int GetX() const
        {
        ...
        }
        Generates method body if `self.implementation` property exists
        """
        if self.implementation is None:
            raise RuntimeError(f"No implementation handle for the function {self.name}")

        # check all properties for the consistency
        if self.documentation and not self.is_constexpr:
            cpp(dedent(self.documentation))
        with cpp.block(
                f"{self._constexpr()} "
                f"{self.ret_type} "
                f"{self.name}"
                f"({self.args()})"
        ):
            self.implementation(cpp)
