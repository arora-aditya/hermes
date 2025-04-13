'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight, Folder, File, Trash } from 'lucide-react';
import { Checkbox } from '@/components/ui/checkbox';
import { DirectoryTreeNode } from '@/services/api';

interface FileTreeNodeProps {
    node: DirectoryTreeNode;
    selectedFiles: Set<number>;
    toggleFileSelection: (document_id: number) => void;
    level?: number;
    onMoveFile: (documentId: number, newPath: string) => Promise<void>;
    onDeleteFile: (documentId: number) => Promise<void>;
}

export const FileTreeNode: React.FC<FileTreeNodeProps> = ({
    node,
    selectedFiles,
    toggleFileSelection,
    level = 0,
    onMoveFile,
    onDeleteFile
}) => {
    const [isOpen, setIsOpen] = useState(true);
    const baseIndent = 1;
    const paddingLeft = `${(level + baseIndent) * 1}rem`;

    const handleDragStart = (e: React.DragEvent, node: DirectoryTreeNode) => {
        if (node.type === 'file' && node.document) {
            e.dataTransfer.setData('documentId', node.document.id.toString());
            e.dataTransfer.setData('fileName', node.name);
            e.dataTransfer.effectAllowed = 'move';
        }
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        e.dataTransfer.dropEffect = 'move';
    };

    const handleDrop = async (e: React.DragEvent, targetNode: DirectoryTreeNode) => {
        e.preventDefault();
        e.stopPropagation();

        const documentId = parseInt(e.dataTransfer.getData('documentId'));
        if (!documentId) return;

        let newPath = '';
        if (targetNode.type === 'directory') {
            newPath = targetNode.path.join('/');
        } else if (targetNode.type === 'file' && targetNode.path.length > 1) {
            // If dropping on a file, use its parent directory
            newPath = targetNode.path.slice(0, -1).join('/');
        }

        await onMoveFile(documentId, newPath);
    };

    if (node.type === 'directory') {
        return (
            <div
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, node)}
            >
                <div
                    onClick={() => setIsOpen(!isOpen)}
                    className="flex items-center gap-2 px-4 py-1 w-full hover:bg-gray-100 rounded-md cursor-pointer"
                    style={{ paddingLeft }}
                >
                    <div className="flex items-center gap-2 min-w-fit">
                        {isOpen ? (
                            <ChevronDown className="w-4 h-4" />
                        ) : (
                            <ChevronRight className="w-4 h-4" />
                        )}
                        <Folder className="w-4 h-4 text-gray-500" />
                    </div>
                    <span className="text-sm font-medium truncate">{node.name}</span>
                </div>
                {isOpen && node.children && node.children.length > 0 && (
                    <div className="flex flex-col">
                        {node.children.map((child, index) => (
                            <FileTreeNode
                                key={`${child.name}-${index}`}
                                node={child}
                                selectedFiles={selectedFiles}
                                toggleFileSelection={toggleFileSelection}
                                level={level + 1}
                                onMoveFile={onMoveFile}
                                onDeleteFile={onDeleteFile}
                            />
                        ))}
                    </div>
                )}
            </div>
        );
    }

    // Handle file nodes
    if (node.type === 'file') {
        const document = node.document;
        if (!document) return null;

        const fileLevel = node.path.length > 1 ? level : 0;
        const actualPaddingLeft = `${(fileLevel + baseIndent) * 1}rem`;

        return (
            <div
                className="group/file flex items-center gap-2 px-4 py-1 hover:bg-gray-100 rounded-md cursor-move relative"
                style={{ paddingLeft: actualPaddingLeft }}
                draggable
                onDragStart={(e) => handleDragStart(e, node)}
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, node)}
            >
                <Checkbox
                    checked={selectedFiles.has(document.id)}
                    onCheckedChange={() => toggleFileSelection(document.id)}
                    className="min-w-fit"
                />
                <File className="w-4 h-4 text-gray-500 min-w-fit" />
                <span className="text-sm truncate">{node.name}</span>
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onDeleteFile(document.id);
                    }}
                    className="opacity-0 group-hover/file:opacity-100 p-1 hover:text-red-600 transition-colors ml-auto"
                    title="Delete file"
                >
                    <Trash className="w-4 h-4" />
                </button>
            </div>
        );
    }

    return null;
}; 