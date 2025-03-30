'use client';

import { FileList } from './components/FileList';
import { FileUploadModal } from './components/FileUploadModal';

export default function Home() {
  return (
    <main className="flex min-h-screen">
      <FileList />
      <div className="flex-1 p-4">
        <div className="flex justify-end">
          <FileUploadModal />
        </div>
        {/* Main content area */}
        <div className="mt-16">
          <h1 className="text-2xl font-bold">Welcome to Hermes</h1>
          <p className="mt-2 text-gray-600">
            Select files from the sidebar to index them, or upload new files using the button in the top right.
          </p>
        </div>
      </div>
    </main>
  );
}
