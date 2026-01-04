/**
 * useClickOutside Hook
 * Close dropdown/modal when clicking outside
 * Created with love by Angela & David - 4 January 2026
 */

import { useEffect, useRef, RefObject } from 'react'

/**
 * Hook that detects clicks outside of the referenced element
 * @param callback - Function to call when click outside is detected
 * @returns ref - Ref to attach to the element you want to detect outside clicks for
 */
export function useClickOutside<T extends HTMLElement = HTMLElement>(
  callback: () => void
): RefObject<T> {
  const ref = useRef<T>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        callback()
      }
    }

    // Use mousedown instead of click for better UX
    document.addEventListener('mousedown', handleClickOutside)

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [callback])

  return ref
}

/**
 * Hook variant that accepts an existing ref
 * @param ref - Existing ref to the element
 * @param callback - Function to call when click outside is detected
 * @param enabled - Whether the hook is active (default: true)
 */
export function useClickOutsideRef<T extends HTMLElement = HTMLElement>(
  ref: RefObject<T>,
  callback: () => void,
  enabled: boolean = true
): void {
  useEffect(() => {
    if (!enabled) return

    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        callback()
      }
    }

    document.addEventListener('mousedown', handleClickOutside)

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [ref, callback, enabled])
}
