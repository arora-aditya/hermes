import { useState, useEffect } from 'react';
import { DirectoryTreeResponse, apiService } from '@/services/api';
import { toast } from 'sonner';

export const useFiles = (userId: number) => {
    const [files, setFiles] = useState<DirectoryTreeResponse>({ children: [] });
    const [selectedFiles, setSelectedFiles] = useState<Set<number>>(new Set());
    const [loading, setLoading] = useState(true);

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

    return {
        files,
        selectedFiles,
        loading,
        toggleFileSelection,
        handleIndex,
        fetchFiles,
    };
}; 