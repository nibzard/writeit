"""
Example extraction from docstrings and test files
"""

import ast
import re
from pathlib import Path
from typing import List

from ..models import CodeExample


class ExampleExtractor:
    """Extract usage examples from docstrings and test files"""

    def extract_from_tests(self, test_file: Path) -> List[CodeExample]:
        """Extract real usage examples from test files"""
        examples = []

        try:
            with open(test_file, "r", encoding="utf-8") as f:
                source_code = f.read()

            tree = ast.parse(source_code)

            # Extract examples from test functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    function_examples = self._extract_from_test_function(
                        node, test_file
                    )
                    examples.extend(function_examples)

        except Exception as e:
            print(f"Error extracting examples from {test_file}: {e}")

        return examples

    def extract_from_docstrings(self, docstring: str) -> List[CodeExample]:
        """Extract code examples from docstring"""
        examples = []

        # Extract doctest examples
        doctest_examples = self._extract_doctest_examples(docstring)
        examples.extend(doctest_examples)

        # Extract code blocks
        code_blocks = self._extract_code_blocks(docstring)
        examples.extend(code_blocks)

        return examples

    def _extract_from_test_function(
        self, node: ast.FunctionDef, test_file: Path
    ) -> List[CodeExample]:
        """Extract examples from test function"""
        examples = []

        # Get function docstring
        docstring = ast.get_docstring(node)
        if docstring:
            description = self._extract_test_description(docstring)
        else:
            description = f"Test function: {node.name}"

        # Extract function body as example
        function_body = []
        for stmt in node.body:
            if isinstance(stmt, (ast.Expr, ast.Assign, ast.Call, ast.Return)):
                try:
                    code_line = ast.unparse(stmt)
                    function_body.append(code_line)
                except Exception:
                    continue

        if function_body:
            example_code = "\n".join(function_body)

            # Clean up the example
            example_code = self._clean_test_example(example_code)

            if example_code.strip():
                examples.append(
                    CodeExample(
                        code=example_code,
                        description=description,
                        language="python",
                        source_file=test_file,
                        line_number=node.lineno,
                    )
                )

        return examples

    def _extract_doctest_examples(self, docstring: str) -> List[CodeExample]:
        """Extract doctest examples from docstring"""
        examples = []

        lines = docstring.split("\n")
        in_example = False
        example_lines = []
        start_line = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            if stripped.startswith(">>>") or stripped.startswith("..."):
                if not in_example:
                    in_example = True
                    example_lines = []
                    start_line = i
                example_lines.append(line)
            elif in_example and stripped == "":
                continue
            elif in_example:
                # End of example
                if example_lines:
                    example_code = "\n".join(example_lines)

                    # Try to extract description from preceding lines
                    desc_start = max(0, start_line - 3)
                    description_lines = lines[desc_start:start_line]
                    description = " ".join(
                        line.strip() for line in description_lines if line.strip()
                    )

                    if not description:
                        description = "Example usage"

                    examples.append(
                        CodeExample(
                            code=example_code,
                            description=description,
                            language="python",
                        )
                    )

                in_example = False
                example_lines = []

        # Handle example at end of docstring
        if in_example and example_lines:
            example_code = "\n".join(example_lines)
            examples.append(
                CodeExample(
                    code=example_code,
                    description=description or "Example usage",
                    language="python",
                )
            )

        return examples

    def _extract_code_blocks(self, docstring: str) -> List[CodeExample]:
        """Extract code blocks from docstring (markdown format)"""
        examples = []

        # Extract markdown code blocks
        code_block_pattern = r"```(\w+)?\n(.*?)\n```"
        matches = re.finditer(code_block_pattern, docstring, re.DOTALL)

        for match in matches:
            language = match.group(1) or "python"
            code = match.group(2)

            # Extract description from preceding text
            preceding_text = docstring[: match.start()]
            description_lines = []
            for line in reversed(preceding_text.split("\n")):
                if line.strip():
                    description_lines.append(line.strip())
                    if len(description_lines) >= 2:
                        break

            description = " ".join(reversed(description_lines))
            if not description:
                description = "Code example"

            examples.append(
                CodeExample(code=code, description=description, language=language)
            )

        return examples

    def _extract_test_description(self, docstring: str) -> str:
        """Extract test description from docstring"""
        lines = docstring.split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith(":"):
                return line
        return "Test example"

    def _clean_test_example(self, code: str) -> str:
        """Clean up test example for documentation"""
        lines = code.split("\n")
        cleaned_lines = []

        for line in lines:
            # Remove test assertions unless they're informative
            if line.strip().startswith("assert "):
                # Keep simple assertions that show expected usage
                if " == " in line and not any(
                    skip in line for skip in ["None", "True", "False"]
                ):
                    cleaned_lines.append(line)
            # Remove test setup/teardown
            elif any(skip in line for skip in ["self.", "@pytest", "unittest."]):
                continue
            else:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def validate_examples(self, examples: List[CodeExample]) -> List[CodeExample]:
        """Validate that examples are syntactically correct"""
        valid_examples = []

        for example in examples:
            if self._validate_example_syntax(example):
                valid_examples.append(example)
            else:
                print(
                    f"Warning: Invalid example syntax in: {example.description[:50]}..."
                )

        return valid_examples

    def _validate_example_syntax(self, example: CodeExample) -> bool:
        """Validate that example code has correct syntax"""
        if example.language != "python":
            return True  # Skip validation for non-Python examples

        try:
            ast.parse(example.code)
            return True
        except SyntaxError:
            return False

    def extract_from_directory(
        self, directory: Path, file_pattern: str = "*.py"
    ) -> List[CodeExample]:
        """Extract examples from all files in a directory"""
        all_examples = []

        for file_path in directory.rglob(file_pattern):
            if file_path.is_file():
                if file_path.name.startswith("test_"):
                    examples = self.extract_from_tests(file_path)
                else:
                    # Extract from regular Python files
                    examples = self._extract_from_python_file(file_path)

                all_examples.extend(examples)

        return all_examples

    def _extract_from_python_file(self, file_path: Path) -> List[CodeExample]:
        """Extract examples from regular Python file"""
        examples = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()

            tree = ast.parse(source_code)

            # Extract docstring examples from all functions and classes
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        docstring_examples = self.extract_from_docstrings(docstring)
                        examples.extend(docstring_examples)

        except Exception as e:
            print(f"Error extracting examples from {file_path}: {e}")

        return examples
