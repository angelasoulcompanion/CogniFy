/**
 * CogniFy Markdown Formatting Utilities
 * Shared formatters for AI-generated content
 * Created with love by Angela & David - 21 February 2026
 */

import React from 'react'

/**
 * Format inline markdown (bold text)
 */
export function formatInlineMarkdown(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return parts.map((part, idx) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={idx} className="text-white font-medium">
          {part.slice(2, -2)}
        </strong>
      )
    }
    return part
  })
}

/**
 * Format answer text with structured markdown rendering
 * Supports: headers (##, ###), bold headers, bullets, numbered lists, paragraphs
 */
export function formatAnswer(answer: string): React.ReactNode {
  const lines = answer.split('\n')
  const elements: React.ReactNode[] = []

  lines.forEach((line, idx) => {
    const trimmed = line.trim()

    if (!trimmed) {
      elements.push(<div key={idx} className="h-2" />)
      return
    }

    if (trimmed.startsWith('## ')) {
      elements.push(
        <h3 key={idx} className="text-lg font-semibold text-white mt-4 mb-2">
          {trimmed.replace('## ', '')}
        </h3>
      )
    } else if (trimmed.startsWith('### ')) {
      elements.push(
        <h4 key={idx} className="text-base font-medium text-primary-300 mt-3 mb-1">
          {trimmed.replace('### ', '')}
        </h4>
      )
    } else if (trimmed.match(/^\*\*[^*]+\*\*:?$/)) {
      const headerText = trimmed.replace(/\*\*/g, '').replace(/:$/, '')
      elements.push(
        <h4 key={idx} className="text-base font-medium text-primary-300 mt-3 mb-1">
          {headerText}
        </h4>
      )
    } else if (trimmed.startsWith('- ') || trimmed.startsWith('• ')) {
      const bulletText = trimmed.replace(/^[-•]\s*/, '')
      elements.push(
        <div key={idx} className="flex items-start gap-2 ml-2 my-1">
          <span className="text-primary-400 mt-1">•</span>
          <span className="text-secondary-200">{formatInlineMarkdown(bulletText)}</span>
        </div>
      )
    } else if (trimmed.match(/^\d+\.\s/)) {
      const [num, ...rest] = trimmed.split(/\.\s/)
      elements.push(
        <div key={idx} className="flex items-start gap-2 ml-2 my-1">
          <span className="text-primary-400 font-medium min-w-[1.5rem]">{num}.</span>
          <span className="text-secondary-200">{formatInlineMarkdown(rest.join('. '))}</span>
        </div>
      )
    } else {
      elements.push(
        <p key={idx} className="text-secondary-200 my-1">
          {formatInlineMarkdown(trimmed)}
        </p>
      )
    }
  })

  return elements
}
