import { useState, useCallback, KeyboardEvent, useRef } from 'react';
import { FileInfo } from '@/services/api';

type MessageContent =
    | { type: 'text'; content: string }
    | { type: 'mention'; file: FileInfo };

interface UseMentionsProps {
    onSearch: (query: string) => void;
}

interface UseMentionsReturn {
    messageContents: MessageContent[];
    isMentioning: boolean;
    mentionQuery: string;
    selectedIndex: number;
    inputValue: string;
    handleChange: (newValue: string) => void;
    handleMention: (file: FileInfo) => void;
    handleKeyDown: (e: KeyboardEvent<HTMLInputElement>, searchResults: FileInfo[]) => boolean;
    resetState: () => void;
    getMessageString: () => string;
}

export function useMentions({ onSearch }: UseMentionsProps): UseMentionsReturn {
    const [messageContents, setMessageContents] = useState<MessageContent[]>([{ type: 'text', content: '' }]);
    const [inputValue, setInputValue] = useState('');
    const [isMentioning, setIsMentioning] = useState(false);
    const [mentionQuery, setMentionQuery] = useState('');
    const [selectedIndex, setSelectedIndex] = useState(0);
    const lastMentionRef = useRef<{ filename: string, startIndex: number } | null>(null);

    const getDisplayString = useCallback(() => {
        const result = messageContents.map(content => {
            if (content.type === 'text') return content.content;
            return `@${content.file.filename}`;
        }).join('');
        console.log('getDisplayString result:', result);
        return result;
    }, [messageContents]);

    const getMessageString = useCallback(() => {
        return messageContents.map(content => {
            if (content.type === 'text') return content.content;
            return `<${content.file.filename}>`;
        }).join('');
    }, [messageContents]);

    const getApiString = useCallback(() => {
        return messageContents.map(content => {
            if (content.type === 'text') return content.content;
            return `@${content.file.id}`;
        }).join('');
    }, [messageContents]);

    const handleChange = useCallback((newValue: string) => {
        setInputValue(newValue);

        // Handle @ symbol for mentions
        if (newValue.endsWith('@')) {
            setIsMentioning(true);
            setMentionQuery('');
            onSearch('');
            lastMentionRef.current = null;
            setMessageContents(prev => {
                const lastItem = prev[prev.length - 1];
                if (lastItem.type === 'text') {
                    return [...prev.slice(0, -1), { type: 'text' as const, content: newValue }];
                }
                return [...prev, { type: 'text' as const, content: newValue }];
            });
            return;
        }

        // Handle mention query
        if (isMentioning) {
            const lastAtIndex = newValue.lastIndexOf('@');
            const query = newValue.slice(lastAtIndex + 1);

            if (query.includes(' ')) {
                setIsMentioning(false);
                setMentionQuery('');
            } else {
                setMentionQuery(query);
                onSearch(query);
            }
            setMessageContents(prev => {
                const withoutLastText = prev.slice(0, -1);
                return [...withoutLastText, { type: 'text' as const, content: newValue }];
            });
            return;
        }

        // For normal text input, update the last text content or add new one
        setMessageContents(prev => {
            const lastItem = prev[prev.length - 1];

            // If we have a last mention, we need to handle the text properly
            if (lastMentionRef.current) {
                const { filename, startIndex } = lastMentionRef.current;
                const mentionText = `@${filename}`;

                // If the text still contains the mention, we need to skip over it
                if (newValue.includes(mentionText)) {
                    const beforeMention = newValue.slice(0, startIndex);
                    const afterMention = newValue.slice(startIndex + mentionText.length);

                    if (lastItem && lastItem.type === 'text') {
                        return [...prev.slice(0, -1), { type: 'text' as const, content: beforeMention + afterMention }];
                    }
                }
            }

            if (lastItem && lastItem.type === 'text') {
                return [...prev.slice(0, -1), { type: 'text' as const, content: newValue }];
            }
            return [...prev, { type: 'text' as const, content: newValue }];
        });
    }, [isMentioning, onSearch]);

    const handleMention = useCallback((file: FileInfo) => {
        const lastAtIndex = inputValue.lastIndexOf('@');
        const beforeMention = lastAtIndex >= 0 ? inputValue.slice(0, lastAtIndex) : inputValue;
        const newInputValue = beforeMention + `@${file.filename} `;

        // Store the mention information for future text updates
        lastMentionRef.current = {
            filename: file.filename,
            startIndex: lastAtIndex
        };

        setInputValue(newInputValue);
        setMessageContents(prev => {
            const withoutLastText = prev.slice(0, -1);
            const lastItem = prev[prev.length - 1];
            const lastTextBeforeMention = lastItem.type === 'text'
                ? beforeMention
                : '';

            return [
                ...withoutLastText,
                { type: 'text' as const, content: lastTextBeforeMention },
                { type: 'mention' as const, file },
                { type: 'text' as const, content: ' ' }
            ];
        });

        setIsMentioning(false);
        setMentionQuery('');
        setSelectedIndex(0);
    }, [inputValue]);

    const handleKeyDown = useCallback((e: KeyboardEvent<HTMLInputElement>, searchResults: FileInfo[]): boolean => {
        // Always prevent default for tab to avoid navigation
        if (e.key === 'Tab') {
            e.preventDefault();
            if (isMentioning && searchResults.length > 0) {
                handleMention(searchResults[selectedIndex]);
                return true;
            }
            return false;
        }

        if (isMentioning && searchResults.length > 0) {
            switch (e.key) {
                case 'ArrowUp':
                    e.preventDefault();
                    setSelectedIndex(prev =>
                        prev > 0 ? prev - 1 : searchResults.length - 1
                    );
                    return true;
                case 'ArrowDown':
                    e.preventDefault();
                    setSelectedIndex(prev =>
                        prev < searchResults.length - 1 ? prev + 1 : 0
                    );
                    return true;
                case 'Enter':
                    e.preventDefault();
                    handleMention(searchResults[selectedIndex]);
                    return true;
                case 'Escape':
                    e.preventDefault();
                    setIsMentioning(false);
                    setMentionQuery('');
                    return true;
            }
        }
        return false;
    }, [handleMention, isMentioning, selectedIndex]);

    const resetState = useCallback(() => {
        setMessageContents([{ type: 'text', content: '' }]);
        setInputValue('');
        setIsMentioning(false);
        setMentionQuery('');
        setSelectedIndex(0);
    }, []);

    return {
        messageContents,
        isMentioning,
        mentionQuery,
        selectedIndex,
        inputValue,
        handleChange,
        handleMention,
        handleKeyDown,
        resetState,
        getMessageString
    };
} 