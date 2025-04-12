from typing import Dict, List, Optional

from models.document import Document
from schemas.document import DirectoryNode, DocumentResponse


def build_directory_tree(
    documents: List[Document], base_path: Optional[List[str]] = None
) -> List[DirectoryNode]:
    """
    Build a directory tree from a list of documents.

    Args:
        documents: List[Document] objects
        base_path: Optional base path to filter documents

    Returns:
        List[DirectoryNode] representing the directory tree
    """
    # Initialize tree structure
    tree: Dict[str, Dict] = {}

    # Filter documents by base path if provided
    if base_path:
        documents = [
            doc
            for doc in documents
            if len(doc.path_array) >= len(base_path)
            and doc.path_array[: len(base_path)] == base_path
        ]

    # Process each document
    for doc in documents:
        current_path = doc.path_array
        current_dict = tree

        # Create directory nodes for each level
        for i, path_part in enumerate(current_path):
            is_last = i == len(current_path) - 1

            if is_last:
                # Create file node
                current_dict[path_part] = {
                    "type": "file",
                    "name": path_part,
                    "path": current_path[: i + 1],
                    "children": None,
                    "document": doc,
                }
            else:
                # Create or get directory node
                if path_part not in current_dict:
                    current_dict[path_part] = {
                        "type": "directory",
                        "name": path_part,
                        "path": current_path[: i + 1],
                        "children": {},
                        "document": None,
                    }
                current_dict = current_dict[path_part]["children"]

    def convert_to_node(data: Dict, is_root: bool = False) -> List[DirectoryNode]:
        """Convert dictionary structure to DirectoryNode objects"""
        nodes = []
        for name, node_data in data.items():
            if node_data["type"] == "file":
                nodes.append(
                    DirectoryNode(
                        type="file",
                        name=name,
                        path=node_data["path"],
                        children=None,
                        document=DocumentResponse.model_validate(node_data["document"]),
                    )
                )
            else:
                children = (
                    convert_to_node(node_data["children"])
                    if node_data["children"]
                    else []
                )
                nodes.append(
                    DirectoryNode(
                        type="directory",
                        name=name,
                        path=node_data["path"],
                        children=children,
                        document=None,
                    )
                )
        return sorted(nodes, key=lambda x: (x.type == "file", x.name))

    return convert_to_node(tree)
