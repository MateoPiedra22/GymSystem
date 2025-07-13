'use client'

import { useState } from 'react'
import { Search, X } from 'lucide-react'
import { cn } from '@/app/utils/cn'
import { Input } from './Input'
import { Button } from './Button'

interface SearchBarProps {
  placeholder?: string
  onSearch: (query: string) => void
  onClear?: () => void
  className?: string
  autoFocus?: boolean
  debounceMs?: number
}

export function SearchBar({
  placeholder = "Buscar...",
  onSearch,
  onClear,
  className,
  autoFocus = false,
  debounceMs = 300
}: SearchBarProps) {
  const [query, setQuery] = useState('')
  const [timeoutId, setTimeoutId] = useState<NodeJS.Timeout | null>(null)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setQuery(value)

    // Clear previous timeout
    if (timeoutId) {
      clearTimeout(timeoutId)
    }

    // Set new timeout for debounced search
    const newTimeoutId = setTimeout(() => {
      onSearch(value)
    }, debounceMs)

    setTimeoutId(newTimeoutId)
  }

  const handleClear = () => {
    setQuery('')
    onSearch('')
    if (onClear) {
      onClear()
    }
    if (timeoutId) {
      clearTimeout(timeoutId)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (timeoutId) {
      clearTimeout(timeoutId)
    }
    onSearch(query)
  }

  return (
    <form onSubmit={handleSubmit} className={cn("relative flex items-center", className)}>
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="text"
          placeholder={placeholder}
          value={query}
          onChange={handleInputChange}
          autoFocus={autoFocus}
          className="pl-10 pr-10"
        />
        {query && (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={handleClear}
            className="absolute right-1 top-1/2 h-8 w-8 -translate-y-1/2"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>
    </form>
  )
} 