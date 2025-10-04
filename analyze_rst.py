from docutils.core import publish_parts


def main():
    """
    Main function to read, parse, and print the AST of a reStructuredText file
    in a pseudo-XML format.
    """
    filepath = "cpython/Doc/library/os.rst"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return

    # Use docutils to parse the content and output a pseudo-XML representation.
    # report_level=4 suppresses errors about unknown directives (e.g. 'function').
    # output_encoding='unicode' ensures the output is a string.
    settings_overrides = {"report_level": 4, "output_encoding": "unicode"}
    parts = publish_parts(
        source=content,
        writer_name="pseudoxml",
        settings_overrides=settings_overrides,
    )

    # The 'whole' key contains the entire document as pseudo-XML.
    print(parts["whole"])


if __name__ == "__main__":
    main()
