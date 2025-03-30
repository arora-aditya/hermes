import { useState, useEffect } from 'react';
import { FileInfo, apiService } from '@/services/api';
import { toast } from 'sonner';

export const useFiles = () => {
    const [files, setFiles] = useState<FileInfo[]>([]);
    const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchFiles();
    }, []);

    const fetchFiles = async () => {
        try {
            const files = await apiService.listFiles();
            setFiles(files);
        } catch (error) {
            console.error('Error fetching files:', error);
            toast.error('Failed to fetch files');
        } finally {
            setLoading(false);
        }
    };

    const toggleFileSelection = (path: string) => {
        setSelectedFiles(prev => {
            const newSelected = new Set(prev);
            if (newSelected.has(path)) {
                newSelected.delete(path);
            } else {
                newSelected.add(path);
            }
            return newSelected;
        });
    };

    const handleIndex = async () => {
        try {
            await apiService.ingestFiles(Array.from(selectedFiles));
            setSelectedFiles(new Set());
            toast.success('Files indexed successfully');
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
    };
}; 