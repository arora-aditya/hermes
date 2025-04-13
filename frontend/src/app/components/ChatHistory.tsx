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
}

interface ChatHistoryProps {
    messages: Message[];
    streamingStatus?: StreamingStatus;
}

export function ChatHistory({ messages, streamingStatus }: ChatHistoryProps) {
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
                        {message.role === 'assistant' &&
                            index === messages.length - 1 &&
                            streamingStatus && (
                                <div className="pl-4 text-sm text-gray-500 animate-pulse">
                                    {streamingStatus.isSearching && (
                                        <div className="flex items-center space-x-2">
                                            <span className="inline-block">🔍</span>
                                            <span>Searching through documents...</span>
                                        </div>
                                    )}
                                    {streamingStatus.isThinking && (
                                        <div className="flex items-center space-x-2">
                                            <span className="inline-block">💭</span>
                                            <span>Thinking...</span>
                                        </div>
                                    )}
                                    {streamingStatus.isStreaming && message.content && (
                                        <div className="flex items-center space-x-2">
                                            <span className="inline-block">✍️</span>
                                            <span>Writing response...</span>
                                        </div>
                                    )}
                                </div>
                            )}
                    </div>
                );
            })}

            {streamingStatus && (
                <div className="pl-4 text-sm text-gray-500">
                    {streamingStatus.isSearching && (
                        <div className="flex items-center space-x-2 animate-pulse">
                            <span className="inline-block">🔍</span>
                            <span>Searching through documents...</span>
                        </div>
                    )}
                    {streamingStatus.isThinking && (
                        <div className="flex items-center space-x-2 animate-pulse">
                            <span className="inline-block">💭</span>
                            <span>Thinking...</span>
                        </div>
                    )}
                    {streamingStatus.isStreaming && (
                        <div className="flex items-center space-x-2 animate-pulse">
                            <span className="inline-block">✍️</span>
                            <span>Writing response...</span>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
} 