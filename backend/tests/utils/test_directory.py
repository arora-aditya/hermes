import unittest
from datetime import datetime
from typing import List

from models.document import Document
from utils.docs.directory import build_directory_tree


class MockDocument:
    def __init__(
        self, id: int, filename: str, path_array: List[str], is_ingested: bool = False
    ):
        self.id = id
        self.filename = filename
        self.path_array = path_array
        self.is_ingested = is_ingested
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


class TestDirectoryTree(unittest.TestCase):
    def test_empty_documents(self):
        """Test that an empty document list returns an empty tree"""
        result = build_directory_tree([])
        self.assertEqual(result, [])

    def test_single_file_no_directory(self):
        """Test a single file with no directory structure"""
        doc = MockDocument(1, "test.pdf", ["test.pdf"])
        result = build_directory_tree([doc])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].type, "file")
        self.assertEqual(result[0].name, "test.pdf")
        self.assertEqual(result[0].document.id, 1)

    def test_single_file_in_directory(self):
        """Test a single file within a directory"""
        doc = MockDocument(1, "test.pdf", ["docs", "test.pdf"])
        result = build_directory_tree([doc])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].type, "directory")
        self.assertEqual(result[0].name, "docs")
        self.assertEqual(len(result[0].children), 1)
        self.assertEqual(result[0].children[0].type, "file")
        self.assertEqual(result[0].children[0].name, "test.pdf")
        self.assertEqual(result[0].children[0].document.id, 1)

    def test_multiple_files_same_directory(self):
        """Test multiple files in the same directory"""
        docs = [
            MockDocument(1, "test1.pdf", ["docs", "test1.pdf"]),
            MockDocument(2, "test2.pdf", ["docs", "test2.pdf"]),
        ]
        result = build_directory_tree(docs)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].type, "directory")
        self.assertEqual(result[0].name, "docs")
        self.assertEqual(len(result[0].children), 2)
        self.assertEqual(result[0].children[0].name, "test1.pdf")
        self.assertEqual(result[0].children[1].name, "test2.pdf")

    def test_nested_directories(self):
        """Test files in nested directory structure"""
        docs = [
            MockDocument(1, "test1.pdf", ["docs", "2024", "test1.pdf"]),
            MockDocument(2, "test2.pdf", ["docs", "2024", "test2.pdf"]),
            MockDocument(3, "test3.pdf", ["docs", "2023", "test3.pdf"]),
        ]
        result = build_directory_tree(docs)

        self.assertEqual(len(result), 1)  # Root level has one directory
        self.assertEqual(result[0].name, "docs")
        self.assertEqual(len(result[0].children), 2)  # "docs" has two subdirectories

        # Check 2024 directory
        dir_2024 = next(d for d in result[0].children if d.name == "2024")
        self.assertEqual(len(dir_2024.children), 2)

        # Check 2023 directory
        dir_2023 = next(d for d in result[0].children if d.name == "2023")
        self.assertEqual(len(dir_2023.children), 1)

    def test_gic_document_structure(self):
        """Test the specific GIC document structure we're debugging"""
        doc = MockDocument(
            id=29,
            filename="CIBC GIC - 1.pdf",
            path_array=["GICs", "CIBC GIC - 1.pdf"],
            is_ingested=True,
        )
        result = build_directory_tree([doc])

        self.assertEqual(len(result), 1)  # Should have one root directory
        self.assertEqual(result[0].type, "directory")
        self.assertEqual(result[0].name, "GICs")
        self.assertEqual(
            len(result[0].children), 1
        )  # GICs directory should have one file

        file_node = result[0].children[0]
        self.assertEqual(file_node.type, "file")
        self.assertEqual(file_node.name, "CIBC GIC - 1.pdf")
        self.assertEqual(file_node.document.id, 29)
        self.assertEqual(file_node.document.filename, "CIBC GIC - 1.pdf")
        self.assertTrue(file_node.document.is_ingested)


if __name__ == "__main__":
    unittest.main()
