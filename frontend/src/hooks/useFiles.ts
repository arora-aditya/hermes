import { useState, useEffect } from 'react';
import { DirectoryTreeResponse, apiService, DirectoryTreeNode, FileInfo, PrefixSearchResponse } from '@/services/api';
import { toast } from 'sonner';

export interface PrefixSearchState {
    results: FileInfo[];
    loading: boolean;
    error: string | null;
}

export const useFiles = (userId: number) => {
    const [files, setFiles] = useState<DirectoryTreeResponse>({ children: [] });
    const [selectedFiles, setSelectedFiles] = useState<Set<number>>(new Set());
    const [loading, setLoading] = useState(true);
    const [prefixSearch, setPrefixSearch] = useState<PrefixSearchState>({
        results: [],
        loading: false,
        error: null
    });

    useEffect(() => {
        fetchFiles();
    }, []);

    const fetchFiles = async () => {
        try {
            const response = await apiService.listFiles(userId);
            setFiles({ children: response.children });
        } catch (error) {
            console.error('Error fetching files:', error);
            toast.error('Failed to fetch files');
        } finally {
            setLoading(false);
        }
    };

    const moveFile = async (documentId: number, newPath: string) => {
        try {
            await apiService.moveFile(userId, documentId, newPath);
            toast.success('File moved successfully');
            await fetchFiles(); // Refresh the file list
        } catch (error) {
            console.error('Error moving file:', error);
            toast.error('Failed to move file');
        }
    };

    const toggleFileSelection = (document_id: number) => {
        setSelectedFiles(prev => {
            const newSelected = new Set(prev);
            if (newSelected.has(document_id)) {
                newSelected.delete(document_id);
            } else {
                newSelected.add(document_id);
            }
            return newSelected;
        });
    };

    const handleIndex = async () => {
        try {
            await apiService.ingestFiles(userId, Array.from(selectedFiles));
            setSelectedFiles(new Set());
            toast.success('Files indexed successfully');
            // Refresh the file list to get updated ingestion status
            await fetchFiles();
        } catch (error) {
            console.error('Indexing error:', error);
            toast.error('Failed to index files');
        }
    };

    const deleteFile = async (documentId: number) => {
        try {
            await apiService.deleteFile(userId, documentId);
            // Remove the file from local state
            setFiles(prevFiles => {
                const removeFileFromTree = (nodes: DirectoryTreeNode[]): DirectoryTreeNode[] => {
                    return nodes.reduce<DirectoryTreeNode[]>((acc, node) => {
                        if (node.type === 'directory') {
                            return [...acc, {
                                ...node,
                                children: removeFileFromTree(node.children || [])
                            }];
                        } else if (node.type === 'file' && node.document?.id !== documentId) {
                            return [...acc, node];
                        }
                        return acc;
                    }, []);
                };

                return {
                    children: removeFileFromTree(prevFiles.children)
                };
            });

            // Also remove from selected files if it was selected
            setSelectedFiles(prev => {
                const newSelected = new Set(prev);
                newSelected.delete(documentId);
                return newSelected;
            });

            toast.success('File deleted successfully');
        } catch (error) {
            console.error('Error deleting file:', error);
            toast.error('Failed to delete file');
        }
    };

    const searchFilesByPrefix = async (query: string, similarityThreshold?: number) => {
        if (!query.trim()) {
            setPrefixSearch({ results: [], loading: false, error: null });
            return;
        }

        setPrefixSearch(prev => ({ ...prev, loading: true, error: null }));
        try {
            const response = await apiService.prefixSearch(userId, query, similarityThreshold);
            setPrefixSearch({
                results: response.documents,
                loading: false,
                error: null
            });
        } catch (error) {
            console.error('Error searching files:', error);
            setPrefixSearch(prev => ({
                ...prev,
                loading: false,
                error: 'Failed to search files'
            }));
        }
    };

    return {
        files,
        selectedFiles,
        loading,
        prefixSearch,
        toggleFileSelection,
        handleIndex,
        fetchFiles,
        moveFile,
        deleteFile,
        searchFilesByPrefix,
    };
}; 