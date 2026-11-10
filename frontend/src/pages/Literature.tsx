import { useState } from 'react'
import { BookOpen, Search, Globe } from 'lucide-react'
import { apiClient } from '../services/api'
import PageHeader from '../components/PageHeader'

export default function Literature() {
  const [query, setQuery] = useState('lung cancer diagnosis treatment')
  const [maxResults, setMaxResults] = useState(5)
  const [isSearching, setIsSearching] = useState(false)
  const [papers, setPapers] = useState([])
  const [error, setError] = useState<string | null>(null)
  
  const handleSearch = async () => {
    if (!query.trim()) return
    
    setIsSearching(true)
    setError(null)
    
    try {
      const response = await apiClient.post('/api/v1/literature', { query, max_results: maxResults })
      setPapers(response.data.papers || [])
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Search failed')
    } finally {
      setIsSearching(false)
    }
  }
  
  const handlePubMedSearch = async () => {
    setIsSearching(true)
    setError(null)
    
    try {
      const response = await apiClient.post('/api/v1/literature/pubmed', { 
        query: "lung cancer screening early detection",
        max_results: maxResults 
      })
      setPapers(response.data.papers || [])
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Search failed')
    } finally {
      setIsSearching(false)
    }
  }
  
  return (
    <div className="max-w-6xl mx-auto px-4 py-4">
      <PageHeader
        eyebrow="Evidence Engine"
        title={<>Medical <span className="gradient-text">Literature Search</span></>}
        subtitle="Live PubMed + Crossref retrieval grounds every clinical finding in real, citable published evidence."
      />
      
      <div className="card mb-6">
        <div className="flex gap-4 mb-4">
          <div className="flex-1">
            <label className="label">Search Query</label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., lung cancer treatment advances..."
              className="input-field"
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
          </div>
          <div>
            <label className="label">Max Results</label>
            <select 
              value={maxResults} 
              onChange={(e) => setMaxResults(Number(e.target.value))}
              className="input-field"
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={15}>15</option>
              <option value={20}>20</option>
            </select>
          </div>
        </div>
        
        <div className="flex gap-2 mb-4">
          <button
            onClick={handleSearch}
            disabled={isSearching || !query.trim()}
            className="btn-primary flex items-center gap-2"
          >
            <Search className="w-4 h-4" />
            Search
          </button>
          <button
            onClick={handlePubMedSearch}
            disabled={isSearching}
            className="btn-secondary flex items-center gap-2"
          >
            <Globe className="w-4 h-4" />
            PubMed Search
          </button>
        </div>
      </div>
      
      {error && (
        <div className="card bg-danger-50 border-danger-200 mb-6">
          <div className="text-danger-700">{error}</div>
        </div>
      )}
      
      {papers.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-slate-800">Search Results</h2>
            <span className="text-sm text-slate-500 bg-slate-100 px-3 py-1 rounded-full">
              {papers.length} papers found
            </span>
          </div>
          
          {papers.map((paper: any, index: number) => (
            <div key={index} className="card hover:shadow-md transition-shadow">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="text-primary-600 font-semibold text-sm">#{index + 1}</span>
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-slate-800 mb-2">{paper.title}</h3>
                  <div className="grid md:grid-cols-2 gap-2 text-sm text-slate-600 mb-3">
                    <div><strong>Authors:</strong> {paper.authors}</div>
                    <div><strong>Journal:</strong> {paper.journal}</div>
                    <div><strong>Published:</strong> {paper.pub_date}</div>
                    <div><strong>PMID:</strong> {paper.pmid}</div>
                  </div>
                  <p className="text-sm text-slate-700 mb-3 line-clamp-3">{paper.abstract}</p>
                  <a
                    href={paper.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700 font-medium"
                  >
                    <BookOpen className="w-4 h-4" />
                    View on PubMed
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {papers.length === 0 && !isSearching && (
        <div className="card text-center py-12">
          <BookOpen className="w-16 h-16 text-slate-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-600 mb-2">No papers found</h3>
          <p className="text-sm text-slate-500">Search medical literature to retrieve relevant papers</p>
        </div>
      )}
    </div>
  )
}