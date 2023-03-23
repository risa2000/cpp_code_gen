import argparse
import sys

from code_generation.core.code_file import CodeFile
from code_generation.cpp.variable_generator import CppVariable
from code_generation.java.java_file import JavaFile
from code_generation.html.html_file import HtmlFile
from code_generation.html.html_element import HtmlElement


def cpp_example():
    """
    Generated C++ code:
    int i = 0;
    static constexpr int const& x = 42;
    extern char* name;
    """
    cpp = CodeFile('example.cpp')
    cpp('int i = 0;')

    # Create a new variable 'x'
    x_variable = CppVariable(
        name='x',
        type='int const&',
        is_static=True,
        is_constexpr=True,
        initialization_value='42')
    x_variable.render_to_string(cpp)

    # Create a new variable 'name'
    name_variable = CppVariable(
        name='name',
        type='char*',
        is_extern=True)
    name_variable.render_to_string(cpp)


def java_example():
    """
    :return:
    """
    java = JavaFile('example.java')
    with java.block('class A', ';'):
        java.access('public')
        java('int m_classMember1;')
        java('double m_classMember2;')


def html_example():
    html = HtmlFile('example.html')
    with html.block('html'):
        with html.block('head', lang='en'):
            html('<meta charset="utf-8" />')


def html_example2():
    html = HtmlFile('example2.html')
    with html.block('html'):
        with html.block('head', lang='en'):
            HtmlElement(name='meta', self_closing=True, charset='utf-8').render_to_string(html)
            HtmlElement(name='meta', self_closing=True, viewport='width=device-width, initial-scale=1').render_to_string(html)
        with html.block('body'):
            # with semantic
            with html.block('div', id='container'):
                with html.block('div', id='header'):
                    html('Header')
                with html.block('div', id='content'):
                    html('Content')
            # using content parameter
            HtmlElement(name='div', self_closing=False).render_to_string(html, content='Footer 1')
            HtmlElement(name='footer', self_closing=False, id='real-footer').render_to_string(html, content='Footer 2')


def html_example3():
    html = HtmlFile('example2.html')
    HtmlElement(name='footer', self_closing=False, id='real-footer').render_to_string(html, content='Footer 2')


def main():
    parser = argparse.ArgumentParser(description='Command-line params')
    parser.add_argument('--language',
                        help='Programming language to show example for',
                        choices=["C++", "Java", "HTML"],
                        default="Java",
                        required=False)
    args = parser.parse_args()

    if args.language == 'C++':
        cpp_example()
    elif args.language == 'Java':
        java_example()
    elif args.language == 'HTML':
        html_example3()
    return 0


if __name__ == '__main__':
    sys.exit(main())
