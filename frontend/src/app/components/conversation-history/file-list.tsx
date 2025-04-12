'use client';

import { DirectoryTreeResponse } from '@/services/api';
import { FileTreeNode } from './file-tree-node';

interface FileListProps {
    files: DirectoryTreeResponse;
    selectedFiles: Set<number>;
    loading: boolean;
    toggleFileSelection: (document_id: number) => void;
    handleIndex: () => Promise<void>;
}

export const FileList: React.FC<FileListProps> = ({
    files,
    selectedFiles,
    loading,
    toggleFileSelection,
    handleIndex,
}) => {
    if (loading) {
        return <div className="text-sm text-gray-500 px-4 py-2">Loading files...</div>;
    }

    return (
        <div className="space-y-2">
            {files.children.map((node, index) => (
                <FileTreeNode
                    key={`${node.name}-${index}`}
                    node={node}
                    selectedFiles={selectedFiles}
                    toggleFileSelection={toggleFileSelection}
                />
            ))}
            <button
                onClick={handleIndex}
                disabled={selectedFiles.size === 0}
                className={`w-full mt-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${selectedFiles.size === 0
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
                    }`}
            >
                Index Files
            </button>
        </div>
    );
}; 