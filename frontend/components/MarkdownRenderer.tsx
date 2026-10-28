"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";

type MarkdownRendererProps = {
  content: string;
};

export default function MarkdownRenderer({
  content,
}: MarkdownRendererProps) {
  return (
    <div className="markdown-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          h1: ({ children }) => (
            <h1 className="mb-4 mt-6 text-2xl font-semibold text-white first:mt-0">
              {children}
            </h1>
          ),

          h2: ({ children }) => (
            <h2 className="mb-3 mt-5 text-xl font-semibold text-white">
              {children}
            </h2>
          ),

          h3: ({ children }) => (
            <h3 className="mb-2 mt-4 text-lg font-semibold text-white">
              {children}
            </h3>
          ),

          p: ({ children }) => (
            <p className="mb-3 leading-7 last:mb-0">
              {children}
            </p>
          ),

          ul: ({ children }) => (
            <ul className="mb-4 ml-5 list-disc space-y-1">
              {children}
            </ul>
          ),

          ol: ({ children }) => (
            <ol className="mb-4 ml-5 list-decimal space-y-1">
              {children}
            </ol>
          ),

          li: ({ children }) => (
            <li className="pl-1 leading-7">
              {children}
            </li>
          ),

          strong: ({ children }) => (
            <strong className="font-semibold text-white">
              {children}
            </strong>
          ),

          blockquote: ({ children }) => (
            <blockquote className="my-4 border-l-4 border-[var(--accent)] pl-4 text-[var(--text-secondary)]">
              {children}
            </blockquote>
          ),

          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[var(--accent)] underline underline-offset-2 hover:opacity-80"
            >
              {children}
            </a>
          ),

          table: ({ children }) => (
            <div className="my-5 w-full overflow-x-auto rounded-xl border border-[var(--border)]">
              <table className="w-full min-w-[600px] border-collapse text-sm">
                {children}
              </table>
            </div>
          ),

          thead: ({ children }) => (
            <thead className="bg-[var(--surface)]">
              {children}
            </thead>
          ),

          th: ({ children }) => (
            <th className="border-b border-[var(--border)] px-4 py-3 text-left font-semibold text-white">
              {children}
            </th>
          ),

          td: ({ children }) => (
            <td className="border-b border-[var(--border)] px-4 py-3 align-top">
              {children}
            </td>
          ),

          tr: ({ children }) => (
            <tr className="transition hover:bg-[var(--surface)]">
              {children}
            </tr>
          ),

          code: ({ className, children }) => {
            const isCodeBlock = Boolean(className);

            if (!isCodeBlock) {
              return (
                <code className="rounded-md bg-[var(--surface)] px-1.5 py-0.5 font-mono text-[0.9em] text-[var(--accent)]">
                  {children}
                </code>
              );
            }

            return (
              <code className={className}>
                {children}
              </code>
            );
          },

          pre: ({ children }) => (
            <pre className="my-5 overflow-x-auto rounded-xl border border-[var(--border)] bg-[#111111] p-4 text-sm leading-6">
              {children}
            </pre>
          ),

          hr: () => (
            <hr className="my-6 border-[var(--border)]" />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}