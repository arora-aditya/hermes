'use client';

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { KeyboardEvent, ChangeEvent, useRef } from "react";
import { Send } from "lucide-react";
import { FileInfo } from "@/services/api";
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandItem,
    CommandList,
} from "@/components/ui/command";
import { MentionedFile } from "./MentionedFile";
import { useMentions } from "@/hooks/useMention";

interface ChatInputProps {
    onSendMessage: (message: string) => void;
    disabled?: boolean;
    onSearch: (query: string) => void;
    searchResults: FileInfo[];
    isSearching: boolean;
}

export function ChatInput({ onSendMessage, disabled, onSearch, searchResults, isSearching }: ChatInputProps) {
    const inputRef = useRef<HTMLInputElement>(null);
    const {
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
    } = useMentions({ onSearch });

    const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
        handleChange(e.target.value);
    };

    const handleInputKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
        if (handleKeyDown(e, searchResults)) {
            e.preventDefault();
            return;
        }

        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleMentionSelect = (file: FileInfo) => {
        handleMention(file);
        requestAnimationFrame(() => {
            if (inputRef.current) {
                inputRef.current.focus();
            }
        });
    };

    const handleSend = () => {
        const messageString = getMessageString();
        if (messageString.trim()) {
            onSendMessage(messageString.trim());
            resetState();
        }
    };

    const renderMessageContents = () => {
        return messageContents.map((content, index) => {
            if (content.type === 'text') {
                return <span key={`text-${index}`}>{content.content}</span>;
            } else {
                const mentionText = `@${content.file.filename}`;
                const hiddenStyle = {
                    opacity: 0,
                    position: 'relative',
                    display: 'inline-block',
                    visibility: 'hidden',
                    height: '1em',
                    whiteSpace: 'pre',
                    pointerEvents: 'none',
                } as const;
                return (
                    <span key={`mention-${content.file.id}-${index}`} style={{ position: 'relative' }}>
                        <span style={hiddenStyle} aria-hidden="true">{mentionText}</span>
                        <span style={{ position: 'absolute', left: 0, top: 0 }}>
                            <MentionedFile file={content.file} />
                        </span>
                    </span>
                );
            }
        });
    };

    return (
        <div className="relative flex gap-2 p-4 border-t">
            {isMentioning && (
                <div className="absolute bottom-full left-0 w-full p-2 bg-background border rounded-md shadow-lg">
                    <Command className="rounded-lg border shadow-md">
                        <CommandList>
                            <CommandGroup>
                                {isSearching ? (
                                    <CommandItem disabled>Loading...</CommandItem>
                                ) : searchResults.length === 0 ? (
                                    <CommandEmpty>No files found</CommandEmpty>
                                ) : (
                                    searchResults.map((file, index) => (
                                        <CommandItem
                                            key={file.id}
                                            onSelect={() => handleMentionSelect(file)}
                                            className={`cursor-pointer ${index === selectedIndex ? "bg-accent" : ""}`}
                                        >
                                            @{file.filename}
                                        </CommandItem>
                                    ))
                                )}
                            </CommandGroup>
                        </CommandList>
                    </Command>
                </div>
            )}
            <div className="flex-1 relative">
                <div
                    className="absolute inset-0 pointer-events-none px-3 py-2 whitespace-pre-wrap"
                    style={{
                        fontSize: '0.875rem',
                        lineHeight: '1.25rem',
                        fontFamily: 'inherit'
                    }}
                >
                    {renderMessageContents()}
                </div>
                <Input
                    ref={inputRef}
                    value={inputValue}
                    onChange={handleInputChange}
                    onKeyDown={handleInputKeyDown}
                    placeholder="Type a message... Use @ to mention files"
                    disabled={disabled}
                    className="flex-1 bg-transparent !px-3 !py-2"
                    style={{
                        fontSize: '0.875rem',
                        lineHeight: '1.25rem',
                        fontFamily: 'inherit',
                        WebkitTextFillColor: 'transparent',
                        caretColor: 'currentColor'
                    }}
                />
            </div>
            <Button
                onClick={handleSend}
                disabled={disabled || !getMessageString().trim()}
                size="icon"
            >
                <Send className="h-4 w-4" />
            </Button>
        </div>
    );
} 