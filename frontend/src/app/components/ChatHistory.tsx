import { ChatMessage } from "./ChatMessage";

interface Message {
    message_id: number;
    content: string;
    role: 'user' | 'assistant';
}

interface StreamingStatus {
    isSearching: boolean;
    isThinking: boolean;
    isStreaming: boolean;
    searchResultCount?: number;
}

interface ChatHistoryProps {
    messages: Message[];
    streamingStatus?: StreamingStatus;
}

export function ChatHistory({ messages, streamingStatus }: ChatHistoryProps) {
    // Function to determine which status message to show
    const getStatusMessage = (status: StreamingStatus) => {
        if (status.isSearching) {
            return (
                <div className="flex items-center space-x-2 animate-pulse">
                    <span className="inline-block">🔍</span>
                    <span>Searching through documents...</span>
                </div>
            );
        }

        if (status.isThinking) {
            return (
                <div className="flex flex-col space-y-2">
                    {status.searchResultCount !== undefined && (
                        <div className="flex items-center space-x-2">
                            <span className="inline-block">📄</span>
                            <span>Found {status.searchResultCount} relevant {status.searchResultCount === 1 ? 'document' : 'documents'}</span>
                        </div>
                    )}
                    <div className="flex items-center space-x-2 animate-pulse">
                        <span className="inline-block">💭</span>
                        <span>Thinking...</span>
                    </div>
                </div>
            );
        }

        if (status.isStreaming) {
            return (
                <div className="flex flex-col space-y-2">
                    {status.searchResultCount !== undefined && (
                        <div className="flex items-center space-x-2">
                            <span className="inline-block">📄</span>
                            <span>Using {status.searchResultCount} relevant {status.searchResultCount === 1 ? 'document' : 'documents'}</span>
                        </div>
                    )}
                    <div className="flex items-center space-x-2 animate-pulse">
                        <span className="inline-block">✍️</span>
                        <span>Writing response...</span>
                    </div>
                </div>
            );
        }

        return null;
    };

    return (
        <div className="inset-0 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent">
            {messages.map((message, index) => {
                // Don't show empty assistant messages while streaming
                if (message.role === 'assistant' &&
                    index === messages.length - 1 &&
                    streamingStatus &&
                    (streamingStatus.isSearching || streamingStatus.isThinking) &&
                    !message.content) {
                    return null;
                }

                return (
                    <div key={message.message_id}>
                        <ChatMessage
                            content={message.content}
                            role={message.role}
                        />
                    </div>
                );
            })}

            {/* Single streaming status display */}
            {streamingStatus && (
                <div className="pl-4 text-sm text-gray-500">
                    {getStatusMessage(streamingStatus)}
                </div>
            )}
        </div>
    );
} 