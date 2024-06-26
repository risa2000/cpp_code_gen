import unittest
import io
from textwrap import dedent

from code_gen.cpp import CppSourceFile, CppEnum, CppArray, CppVariable, CppClass
from test.comparing_tools import normalize_code, debug_dump, is_debug

__doc__ = """Unit tests for C++ code generator"""


class TestCppClassStringIo(unittest.TestCase):
    """
    Test C++ class generation by writing to StringIO
    """

    def test_simple_case(self):
        writer = io.StringIO()
        cpp_file = CppSourceFile(None, writer=writer)

        # Create a CppClass instance
        cpp_class = CppClass(name="MyClass", is_struct=True)

        # Add a CppVariable to the class
        cpp_class.add_variable(
            CppVariable(
                name="m_var", type="size_t", is_static=True, is_const=True, value="255"
            )
        )

        # Add a CppVariable to the class
        cpp_class.add_variable(CppVariable(name="m_var2", type="bool"))

        # Define a function body for the CppMethod
        def body(cpp):
            cpp("return m_var;")

        def ctor_body(cpp):
            pass

        # Add a CppMethod to the class
        cpp_class.add_method(
            CppClass.CppCtor(
                name="MyClass",
                implementation=ctor_body,
                initializers=["m_var2{ false }"],
            )
        )

        cpp_class.add_method(
            CppClass.CppMethod(
                name="GetVar", ret_type="size_t", is_static=True, implementation=body
            )
        )

        # Render the class to string
        cpp_class.render_to_string(cpp_file)

        # Define the expected output
        expected_output = dedent(
            """\
            struct MyClass
            {
                MyClass();
                static size_t GetVar();
                static const size_t m_var;
                bool m_var2;
            };

            static const size_t MyClass::m_var = 255;

            MyClass::MyClass() : m_var2{ false }
            {
            }

            size_t MyClass::GetVar()
            {
                return m_var;
            }"""
        )

        # Assert the output matches the expected output
        actual_output = writer.getvalue().strip()
        expected_output_normalized = normalize_code(expected_output)
        actual_output_normalized = normalize_code(actual_output)
        if is_debug():
            debug_dump(expected_output_normalized, actual_output_normalized, "cpp")
        self.assertEqual(expected_output_normalized, actual_output_normalized)

    def test_with_inheritance(self):
        writer = io.StringIO()
        cpp = CppSourceFile(None, writer=writer)

        # Create a parent class
        parent_class = CppClass(name="ParentClass")

        # Create a child class with inheritance
        child_class = CppClass(name="ChildClass", parent_class="ParentClass")

        # Add a CppVariable to the parent class
        parent_class.add_variable(
            CppVariable(
                name="m_var", type="int", is_static=True, is_const=True, value="42"
            )
        )

        # Add a CppMethod to the parent class
        parent_class.add_method(
            CppClass.CppMethod(
                name="GetVar",
                ret_type="int",
                is_static=True,
                implementation=lambda cpp_file: cpp_file("return m_var;"),
            )
        )

        # Render the parent class to string
        parent_class.render_to_string(cpp)

        # Render the child class to string
        child_class.render_to_string(cpp)

        # Define the expected output
        expected_output = dedent(
            """\
            class ParentClass
            {
            public:
                static int GetVar();
            private:
                static const int m_var;
            };

            static const int ParentClass::m_var = 42;

            int ParentClass::GetVar()
            {
                return m_var;
            }

            class ChildClass : public ParentClass
            {
            };"""
        )

        # Assert the output matches the expected output
        actual_output = writer.getvalue().strip()
        expected_output_normalized = normalize_code(expected_output)
        actual_output_normalized = normalize_code(actual_output)
        if is_debug():
            debug_dump(expected_output_normalized, actual_output_normalized, "cpp")

        self.assertEqual(expected_output_normalized, actual_output_normalized)

    def test_with_nested_classes(self):
        writer = io.StringIO()
        cpp = CppSourceFile(None, writer=writer)

        # Create a CppClass instance
        cpp_class = CppClass(name="MyClass")

        # Create a nested class
        nested_class = CppClass(name="NestedClass")

        # Add the nested class to the main class
        cpp_class.add_internal_class(nested_class)

        # Render the main class to string
        cpp_class.render_to_string(cpp)

        # Define the expected output
        expected_output = dedent(
            """\
            class MyClass
            {
            public:
                class NestedClass
                {
                };
            };"""
        )

        actual_output = writer.getvalue().strip()
        expected_output_normalized = normalize_code(expected_output)
        actual_output_normalized = normalize_code(actual_output)
        if is_debug():
            debug_dump(expected_output_normalized, actual_output_normalized, "cpp")
        self.assertEqual(expected_output_normalized, actual_output_normalized)

    def test_with_enum(self):
        writer = io.StringIO()
        cpp = CppSourceFile(None, writer=writer)

        # Create a CppClass instance
        cpp_class = CppClass(name="MyClass")

        # Create a CppEnum instance
        cpp_enum = CppEnum(name="Items")

        # Add enum items
        cpp_enum.add_items(["Item1", "Item2", "Item3"])

        # Add the enum to the class
        cpp_class.add_enum(cpp_enum)

        # Render the class to string
        cpp_class.render_to_string(cpp)

        # Define the expected output
        expected_output = dedent(
            """\
            class MyClass
            {
            public:
                enum Items {
                    eItem1 = 0,
                    eItem2 = 1,
                    eItem3 = 2,
                    eItemsCount = 3
                };
            };"""
        )

        # Assert the output matches the expected output
        actual_output = writer.getvalue().strip()
        expected_output_normalized = normalize_code(expected_output)
        actual_output_normalized = normalize_code(actual_output)
        if is_debug():
            debug_dump(expected_output_normalized, actual_output_normalized, "cpp")
        self.assertEqual(expected_output_normalized, actual_output_normalized)

    def test_with_array(self):
        writer = io.StringIO()
        cpp = CppSourceFile(None, writer=writer)

        # Create a CppClass instance
        cpp_class = CppClass(name="MyClass")

        # Create a CppArray instance
        cpp_array = CppArray(name="Array", type="const char*", is_static=True)
        cpp_array.add_array_items(["Item1", "Item2", "Item3"])

        # Add the array to the class
        cpp_class.add_array(cpp_array)

        # Render the class to string
        cpp_class.render_to_string(cpp)

        # Define the expected output
        expected_output = dedent(
            """\
            class MyClass
            {
                static const char* Array[];
            };

            static const char* MyClass::Array[] = {Item1, Item2, Item3};"""
        )

        # Assert the output matches the expected output
        actual_output = writer.getvalue().strip()
        expected_output_normalized = normalize_code(expected_output)
        actual_output_normalized = normalize_code(actual_output)
        if is_debug():
            debug_dump(expected_output_normalized, actual_output_normalized, "cpp")
        self.assertEqual(expected_output_normalized, actual_output_normalized)


if __name__ == "__main__":
    unittest.main()
