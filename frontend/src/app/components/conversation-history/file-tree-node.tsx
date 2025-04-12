'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight, Folder, File } from 'lucide-react';
import { Checkbox } from '@/components/ui/checkbox';
import { DirectoryTreeNode } from '@/services/api';

interface FileTreeNodeProps {
    node: DirectoryTreeNode;
    selectedFiles: Set<number>;
    toggleFileSelection: (document_id: number) => void;
    level?: number;
}

export const FileTreeNode: React.FC<FileTreeNodeProps> = ({
    node,
    selectedFiles,
    toggleFileSelection,
    level = 0
}) => {
    const [isOpen, setIsOpen] = useState(true);
    const baseIndent = 1;
    const paddingLeft = `${(level + baseIndent) * 1}rem`;

    if (node.type === 'directory') {
        return (
            <div>
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className="flex items-center space-x-2 px-4 py-1 w-full hover:bg-gray-100 rounded-md"
                    style={{ paddingLeft }}
                >
                    {isOpen ? (
                        <ChevronDown className="w-4 h-4" />
                    ) : (
                        <ChevronRight className="w-4 h-4" />
                    )}
                    <Folder className="w-4 h-4 text-gray-500" />
                    <span className="text-sm font-medium">{node.name}</span>
                </button>
                {isOpen && node.children && node.children.length > 0 && (
                    <div className="space-y-1">
                        {node.children.map((child, index) => (
                            <FileTreeNode
                                key={`${child.name}-${index}`}
                                node={child}
                                selectedFiles={selectedFiles}
                                toggleFileSelection={toggleFileSelection}
                                level={level + 1}
                            />
                        ))}
                    </div>
                )}
            </div>
        );
    }

    if (node.type === 'file' && node.document) {
        const fileLevel = node.path.length > 1 ? level : 0;
        const actualPaddingLeft = `${(fileLevel + baseIndent) * 1}rem`;

        return (
            <div
                className="flex items-center space-x-2 px-4 py-1 hover:bg-gray-100 rounded-md"
                style={{ paddingLeft: actualPaddingLeft }}
            >
                <Checkbox
                    checked={selectedFiles.has(node.document.id)}
                    onCheckedChange={() => toggleFileSelection(node.document.id)}
                />
                <File className="w-4 h-4 text-gray-500" />
                <span className="text-sm truncate" title={node.name}>
                    {node.name}
                </span>
            </div>
        );
    }

    return null;
}; 