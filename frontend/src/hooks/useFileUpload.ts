import { useState } from 'react';
import { apiService, UploadResponse } from '@/services/api';
import { toast } from 'sonner';

export interface FileUploadState {
    isUploading: boolean;
    progress: number;
}

export const useFileUpload = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [uploadState, setUploadState] = useState<FileUploadState>({
        isUploading: false,
        progress: 0,
    });

    const handleUpload = async (files: FileList | null) => {
        if (!files || files.length === 0) {
            toast.error('Please select at least one file');
            return;
        }

        setUploadState({ isUploading: true, progress: 0 });

        try {
            const fileArray = Array.from(files);
            const responses = await apiService.uploadMultipleFiles(fileArray);

            const successCount = responses.filter(r => r.success).length;
            const failureCount = responses.length - successCount;

            if (failureCount === 0) {
                toast.success(`Successfully uploaded ${successCount} file${successCount > 1 ? 's' : ''}`);
            } else {
                toast.error(`Failed to upload ${failureCount} file${failureCount > 1 ? 's' : ''}`);
            }

            setIsOpen(false);
        } catch (error) {
            console.error('Upload error:', error);
            toast.error('Failed to upload files');
        } finally {
            setUploadState({ isUploading: false, progress: 0 });
        }
    };

    return {
        isOpen,
        setIsOpen,
        uploadState,
        handleUpload,
    };
}; 