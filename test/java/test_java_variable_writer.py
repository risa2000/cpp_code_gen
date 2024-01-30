import unittest
import io

from code_generation.java.source_file import JavaSourceFile
from code_generation.java.variable_generator import JavaVariable


class TestJavaVariableStringIo(unittest.TestCase):
    """
    Test Java variable generation by writing to StringIO
    """

    def test_simple_case(self):
        writer = io.StringIO()
        java = JavaSourceFile(None, writer=writer)
        variable = JavaVariable(name="var1",
                                type="String",
                                is_class_member=False,
                                is_static=False,
                                is_final=True,
                                value='"Hello"')
        variable.render_to_string(java)
        self.assertEqual("final String var1 = \"Hello\";", writer.getvalue().strip())

    def test_is_static_final_raises(self):
        writer = io.StringIO()
        java = JavaSourceFile(None, writer=writer)
        variable = JavaVariable(name="var1", type="String", is_static=True, is_final=True)
        self.assertRaises(ValueError, variable.render_to_string, java)

    def test_is_static_render_to_string(self):
        writer = io.StringIO()
        java = JavaSourceFile(None, writer=writer)
        variable = JavaVariable(name="var1", type="String", is_static=True)
        variable.render_to_string(java)
        self.assertEqual("static String var1;", writer.getvalue().strip())

    def test_render_to_string_declaration(self):
        writer = io.StringIO()
        java = JavaSourceFile(None, writer=writer)
        variable = JavaVariable(name="var1", type="String")
        variable.render_to_string(java)
        self.assertEqual("String var1;", writer.getvalue().strip())


if __name__ == "__main__":
    unittest.main()
