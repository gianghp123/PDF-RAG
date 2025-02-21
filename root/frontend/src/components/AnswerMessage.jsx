"use client";
import Markdown from "react-markdown";

export default function AnswerMessage({ answer }) {
  return (
    <div>
      {answer ? (
        <Markdown
          components={{
            h3: ({ node, ...props }) => (
              <h3 className="text-xl font-bold mt-6 mb-4" {...props} />
            ),
            h2: ({ node, ...props }) => (
              <h3 className="text-2xl font-bold mt-6 mb-4" {...props} />
            ),
            h1: ({ node, ...props }) => (
              <h3 className="text-3xl font-bold mt-6 mb-4" {...props} />
            ),
            ul: ({ node, ...props }) => (
              <ul className="list-disc pl-6 mb-4 space-y-1" {...props} />
            ),
            ol: ({ node, ...props }) => (
              <ol className="list-decimal pl-6 mb-4 space-y-1" {...props} />
            ),
            strong: ({ node, ...props }) => (
              <strong className="font-bold" {...props} />
            ),
            p: ({ node, ...props }) => <p className="font-thin" {...props} />,
          }}
        >
          {answer}
        </Markdown>
      ) : (
        <div className="h-[50px] self-start bg-gray-100 animate-pulse rounded-full"/>
      )}
    </div>
  );
}
