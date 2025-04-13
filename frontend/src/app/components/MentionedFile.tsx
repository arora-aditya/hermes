'use client';

import { FileInfo } from "@/services/api";

interface MentionedFileProps {
    file: FileInfo;
}

export function MentionedFile({ file }: MentionedFileProps) {
    return (
        <span className="font-mono text-[0.875rem] leading-[1.25rem] bg-accent/20 text-accent-foreground">
            @{file.filename}
        </span>
    );
} 