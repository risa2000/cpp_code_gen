from textwrap import dedent

from .language_element import CppLanguageElement
from .function_generator import CppFunction
from .scope_generator import CppClassScope


class CppClass(CppClassScope):
    """
    The Python class that generates string representation for C++ class or struct.
    Usually contains a number of child elements - internal classes, enums, methods and variables.
    Available properties:
    is_struct - boolean, use 'struct' keyword for class declaration, 'class' otherwise
    documentation - string, '/// Example doxygen'

    Example of usage:

    # Python code
    cpp_class = CppClass(name = 'MyClass', is_struct = True)
    cpp_class.add_variable(CppVariable(name = "m_var",
        type = 'size_t',
        is_static = True,
        is_const = True,
        value = 255))

    def handle(cpp): cpp('return m_var;')

    cpp_class.add_method(CppFunction(name = "GetVar",
        ret_type = 'size_t',
        is_static = True,
        implementation = handle))

    // Generated C++ declaration
    struct MyClass
    {
        static const size_t m_var;
        static size_t GetVar();
    }

    // Generated C++ definition
    const size_t MyClass::m_var = 255;

    size_t MyClass::GetVar()
    {
        return m_var;
    }
    """

    PROPERTIES = CppClassScope.PROPERTIES | {
        "is_struct",
        "parent_class",
    }

    class CppMethod(CppFunction):
        """
        The Python class that generates string representation for C++ method
        Parameters are passed as plain strings('int a', 'void p = NULL' etc.)
        Available properties:
        ret_type - string, return value for the method ('void', 'int'). Could not be set for constructors
        is_static - boolean, static method prefix
        is_const - boolean, const method prefix, could not be static
        is_virtual - boolean, virtual method postfix, could not be static
        is_pure_virtual - boolean, ' = 0' method postfix, could not be static
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
        int MyClass::GetAnswer()
        {
            return 42;
        }
        """

        PROPERTIES = CppFunction.PROPERTIES | {
            "ret_type",
            "is_static",
            "is_constexpr",
            "is_virtual",
            "is_inline",
            "is_pure_virtual",
            "is_const",
            "is_override",
            "is_final",
            "arguments",
            "implementation",
            "documentation",
        }

        def __init__(self, **properties):
            # arguments are plain strings
            # e.g. 'int* a', 'const string& s', 'size_t sz = 10'
            super().__init__()
            self.ret_type = None
            self.is_static = False
            self.is_constexpr = False
            self.is_virtual = False
            self.is_inline = False
            self.is_pure_virtual = False
            self.is_const = False
            self.is_override = False
            self.is_final = False
            self.arguments = []
            self.implementation = None
            self.documentation = None
            self.init_properties(properties)

        def add_argument(self, argument):
            """
            @param: argument string representation of the C++ function argument ('int a', 'void p = NULL' etc)
            """
            self.arguments.append(argument)

        def args(self):
            """
            @return: string arguments
            """
            return ", ".join(self.arguments)

        def body(self, cpp):
            """
            The method calls Python function that creates C++ method body if handle exists
            """
            if self.implementation is not None:
                self.implementation(cpp)

        def short_header_declaration_to_string(self):
            header = [
                f"{self._static()}",
                f"{self._modifiers_front()}",
                f"{self._ret_type(local_scope=True)}",
                f"{self.name}({self.args()})",
                f"{self._modifiers_back()}",
                f"{self._pure()}",
            ]
            return " ".join(h for h in header if h)

        def short_header_implementation_to_string(self):
            return self.short_header_declaration_to_string()

        def full_header_implementation_to_string(self):
            header = [
                f"{self._ret_type(local_scope=False)}",
                f"{self.fully_qualified_name()}({self.args()})",
                f"{self._const()}",
            ]
            return " ".join(h for h in header if h)

        def render_to_string(self, cpp):
            """
            By default, method is rendered as a declaration together with implementation,
            like the method is implemented within the C++ class body, e.g.
            class A
            {
                void f()
                {
                ...
                }
            }
            """
            # check all properties for the consistency
            self._sanity_check()
            if self.documentation:
                cpp(dedent(self.documentation))

            if self.implementation is None:
                raise RuntimeError(
                    f"No implementation handle for the method {self.name}"
                )

            with cpp.block(self.short_header_implementation_to_string()) as block:
                self.implementation(block)

        def render_to_string_declaration(self, cpp):
            """
            Special case for a method declaration string representation.
            Generates just a function signature terminated by ';'
            Example:
            int GetX() const;
            """
            # check all properties for the consistency
            self._sanity_check()
            if self.is_constexpr:
                if self.documentation:
                    cpp(dedent(self.documentation))
                self.render_to_string(cpp)
            else:
                cpp(f"{self.short_header_declaration_to_string()};")

        def render_to_string_implementation(self, cpp):
            """
            Special case for a method implementation string representation.
            Generates method string in the form
            Example:
            int MyClass::GetX() const
            {
            ...
            }
            Generates method body if `self.implementation` property exists
            """
            # check all properties for the consistency
            self._sanity_check()

            if self.implementation is None:
                raise RuntimeError(
                    f"No implementation handle for the method {self.name}"
                )

            if self.is_pure_virtual:
                raise RuntimeError(
                    f"Pure virtual method {self.name} could not be implemented"
                )

            if self.documentation and not self.is_constexpr:
                cpp(dedent(self.documentation))
            with cpp.block(self.full_header_implementation_to_string()) as block:
                self.implementation(block)

        def _sanity_check(self):
            """
            Check whether attributes compose a correct C++ code
            """
            if self.is_inline and (self.is_virtual or self.is_pure_virtual):
                raise ValueError(f"Inline method {self.name} could not be virtual")
            if self.is_constexpr and (self.is_virtual or self.is_pure_virtual):
                raise ValueError(f"Constexpr method {self.name} could not be virtual")
            if self.is_const and self.is_static:
                raise ValueError(f"Static method {self.name} could not be const")
            if self.is_const and self.is_virtual:
                raise ValueError(f"Virtual method {self.name} could not be const")
            if self.is_const and self.is_pure_virtual:
                raise ValueError(f"Pure virtual method {self.name} could not be const")
            if self.is_override and not self.is_virtual:
                raise ValueError(f"Override method {self.name} should be virtual")
            if self.is_inline and (self.is_virtual or self.is_pure_virtual):
                raise ValueError(f"Inline method {self.name} could not be virtual")
            if self.is_final and not self.is_virtual:
                raise ValueError(f"Final method {self.name} should be virtual")
            if self.is_static and self.is_virtual:
                raise ValueError(f"Static method {self.name} could not be virtual")
            if self.is_pure_virtual and not self.is_virtual:
                raise ValueError(
                    f"Pure virtual method {self.name} is also a virtual method"
                )
            if not self.ref_to_parent:
                raise ValueError(
                    f"Method {self.name} object must be a child of CppClass"
                )
            if self.is_constexpr and self.implementation is None:
                raise ValueError(
                    f'Method {self.name} object must be initialized when "constexpr"'
                )
            if self.is_pure_virtual and self.implementation is not None:
                raise ValueError(
                    f"Pure virtual method {self.name} could not be implemented"
                )

        def _modifiers_front(self):
            modifiers = [
                self._constexpr(),
                self._virtual(),
                self._inline(),
            ]
            return " ".join(m for m in modifiers if m)

        def _modifiers_back(self):
            modifiers = [
                self._const(),
                self._override(),
                self._final(),
            ]
            return " ".join(m for m in modifiers if m)

        def _static(self):
            """
            Before function name, declaration only
            Static functions can't be const, virtual or pure virtual
            """
            return "static" if self.is_static else ""

        def _constexpr(self):
            """
            Before function name, declaration only
            Constexpr functions can't be const, virtual or pure virtual
            """
            return "constexpr" if self.is_constexpr else ""

        def _virtual(self):
            """
            Before function name, could be in declaration or definition
            Virtual functions can't be static or constexpr
            """
            return "virtual" if self.is_virtual else ""

        def _inline(self):
            """
            Before function name, could be in declaration or definition
            Inline functions can't be static, virtual or constexpr
            """
            return "inline" if self.is_inline else ""

        def _ret_type(self, local_scope):
            """
            Return type, could be in declaration or definition
            """
            if self.ret_type:
                return CppLanguageElement.resolved_name(self.ret_type, local_scope)
            return ""

        def _pure(self):
            """
            After function name, declaration only
            Pure virtual functions must be virtual
            """
            return " = 0" if self.is_pure_virtual else ""

        def _const(self):
            """
            After function name, could be in declaration or definition
            Const functions can't be static, virtual or constexpr
            """
            return "const" if self.is_const else ""

        def _override(self):
            """
            After function name, could be in declaration or definition
            Override functions must be virtual
            """
            return "override" if self.is_override else ""

        def _final(self):
            """
            After function name, could be in declaration or definition
            Final functions must be virtual
            """
            return "final" if self.is_final else ""

    class CppCtor(CppMethod):
        """Constructor method."""

        PROPERTIES = CppLanguageElement.PROPERTIES | {
            "arguments",
            "initializers",
            "implementation",
            "documentation",
        }

        def __init__(self, **properties):
            # arguments are plain strings
            # e.g. 'int* a', 'const string& s', 'size_t sz = 10'
            super().__init__()
            self.arguments = []
            self.initializers = []
            self.implementation = None
            self.documentation = None
            self.init_properties(properties)

        def _sanity_check(self):
            """
            Check whether attributes compose a correct C++ code
            """
            PROHIBITED_ATTRS = [
                "ret_type",
                "static",
                "constexpr",
                "virtual",
                "inline",
                "pure_virtual",
                "const",
                "override",
                "final",
            ]

            for attr in PROHIBITED_ATTRS:
                attr_val = getattr(self, attr, None) or getattr(
                    self, f"is_{attr}", None
                )
                if attr_val:
                    raise ValueError(f"{self.name} ctor cannot be declared with {attr}")

        def short_header_declaration_to_string(self):
            return f"{self.name}({self.args()})"

        def short_header_implementation_to_string(self):
            header = [
                f"{self.name}({self.args()})",
                f"{self._member_initializers()}",
            ]
            return " ".join(h for h in header if h)

        def full_header_implementation_to_string(self):
            header = [
                f"{self.fully_qualified_name()}({self.args()})",
                f"{self._member_initializers()}",
            ]
            return " ".join(h for h in header if h)

        def _member_initializers(self):
            """Return member initializer list for ctor implementation."""
            if not self.initializers:
                return None

            initializers = (
                self.initializers()
                if callable(self.initializers)
                else self.initializers
            )

            out_list = []
            started = False
            for member_initializer in initializers:
                if not started:
                    out_list.append(f": {member_initializer}")
                    started = True
                else:
                    out_list.append(member_initializer)
            return ", ".join(out_list)

    def __init__(self, **properties):
        super().__init__()
        self.is_struct = False
        self.parent_class = None
        self.init_properties(properties)

    def inherits(self):
        """
        @return: string representation of the inheritance
        """
        if self._parent_class():
            return f" : public {self._parent_class()}"

    # group generated sections
    def anything_public_to_declare(self):
        return any(
            [
                self.scoped_enums,
                self.internal_class_elements,
                self.methods,
            ]
        )

    def anything_private_to_declare(self):
        return any(
            [
                self.variable_members,
                self.array_members,
            ]
        )

    def class_interface(self, cpp):
        """
        Generates section that generally used as an 'open interface'
        Generates string representation for enums, internal classes and methods
        Should be placed in 'public:' section
        """
        if not self.anything_public_to_declare():
            return

        if not self.is_struct:
            cpp.label("public")

        self.render_enum_declaration(cpp)
        self.render_internal_classes_declaration(cpp)
        self.render_methods_declaration(cpp)

    def private_class_members(self, cpp):
        """
        Generates section of class member variables.
        Should be placed in 'private:' section
        """
        if not self.anything_private_to_declare():
            return

        # private is default class scope so be explict only when there was a public one before
        if not self.is_struct and self.anything_public_to_declare():
            cpp.label("private")

        self.render_variables_declaration(cpp)
        self.render_array_declaration(cpp)

    def render_to_string(self, cpp):
        """
        Render to string both declaration and definition.
        A rare case enough, because the only code generator handle is used.
        Typically class declaration is rendered to *.h file, and definition to *.cpp
        """
        self.render_to_string_declaration(cpp)
        self.render_to_string_implementation(cpp)

    def render_to_string_declaration(self, cpp):
        """
        Render to string class declaration.
        Typically handle to header should be passed as 'cpp' param
        """
        if self.documentation:
            cpp(dedent(self.documentation))

        render_str = f"{self._class_type()} {self.name}"
        if self._parent_class():
            render_str += self.inherits()

        with cpp.block(render_str, postfix=";") as block:
            # in case of struct all members meant to be public
            self.class_interface(block)
            self.private_class_members(block)
            self.render_internal_scopes_declarations(block)
            self.render_postfix_lines(block)

    def render_to_string_implementation(self, cpp):
        """
        Render to string class definition.
        Typically handle to *.cpp file should be passed as 'cpp' param
        """
        self.render_static_members_implementation(cpp)
        self.render_methods_implementation(cpp)
        self.render_internal_classes_implementation(cpp)
        self.render_internal_scopes_implementation(cpp)

    ########################################
    # PRIVATE METHODS
    def _class_type(self):
        """
        @return: 'class' or 'struct' keyword
        """
        return "struct" if self.is_struct else "class"

    def _parent_class(self):
        """
        @return: parent class object
        """
        return self.parent_class if self.parent_class else ""
