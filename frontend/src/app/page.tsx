'use client';

import { FileList } from './components/FileList';
import { FileUploadModal } from './components/FileUploadModal';
import { useFiles } from '@/hooks/useFiles';

export default function Home() {
  const { files, selectedFiles, loading, toggleFileSelection, handleIndex, fetchFiles } = useFiles();

  return (
    <div className="flex min-h-screen">
      <FileList
        files={files}
        selectedFiles={selectedFiles}
        loading={loading}
        toggleFileSelection={toggleFileSelection}
        handleIndex={handleIndex}
      />
      <div className="flex-1 p-4">
        <div className="flex justify-end">
          <FileUploadModal onUploadComplete={fetchFiles} />
        </div>
        {/* Main content area */}
        <div className="mt-16">
          <h1 className="text-2xl font-bold">Welcome to Hermes</h1>
          <p className="mt-2 text-gray-600">
            Select files from the sidebar to index them, or upload new files using the button in the top right.
          </p>
        </div>
      </div>
    </div>
  );
}
