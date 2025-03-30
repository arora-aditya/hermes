'use client';

import { FileList } from './components/FileList';
import { FileUploadModal } from './components/FileUploadModal';
import { useFiles } from '@/hooks/useFiles';
import { ChatHistory } from './components/ChatHistory';
import { ChatInput } from './components/ChatInput';
import { useState } from 'react';

interface Message {
  content: string;
  role: 'user' | 'assistant';
}

export default function Home() {
  const { files, selectedFiles, loading, toggleFileSelection, handleIndex, fetchFiles } = useFiles();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async (content: string) => {
    // Add user message immediately
    const userMessage: Message = { content, role: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // TODO: Implement actual API call to backend
      // For now, just simulate a response
      setTimeout(() => {
        const assistantMessage: Message = {
          content: "This is a simulated response. Backend integration pending.",
          role: 'assistant'
        };
        setMessages(prev => [...prev, assistantMessage]);
        setIsLoading(false);
      }, 1000);
    } catch (error) {
      console.error('Failed to send message:', error);
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      <FileList
        files={files}
        selectedFiles={selectedFiles}
        loading={loading}
        toggleFileSelection={toggleFileSelection}
        handleIndex={handleIndex}
      />
      <div className="flex-1 flex flex-col">
        <div className="flex justify-end p-4">
          <FileUploadModal onUploadComplete={fetchFiles} />
        </div>
        <div className="flex-1 flex flex-col">
          <ChatHistory messages={messages} />
          <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
        </div>
      </div>
    </div>
  );
}
