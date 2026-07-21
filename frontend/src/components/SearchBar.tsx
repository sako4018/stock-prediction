import { useState } from 'react'

interface SearchBarProps {
  onSearch: (ticker: string) => void
}

export default function SearchBar({ onSearch }: SearchBarProps) {
  const [input, setInput] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim()) {
      onSearch(input.trim().toUpperCase())
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Search ticker (AAPL, TSLA, GOOGL...)"
        className="bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-stock-blue transition-colors w-64"
      />
      <button
        type="submit"
        className="bg-stock-blue hover:bg-blue-600 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
      >
        Search
      </button>
    </form>
  )
}
