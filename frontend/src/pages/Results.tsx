import { useEffect, useState } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import { Activity, AlertTriangle, X, Download } from 'lucide-react'
import NearbyLocator from '../components/NearbyLocator'
import PageHeader from '../components/PageHeader'
import { openProfessionalReport } from '../utils/report'

export default function Results() {
  const location = useLocation()
  const navigate = useNavigate()
  
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error] = useState<string | null>(null)
  
  useEffect(() => {
    // Try to get result from location state
    if (location.state && location.state.consultationResult) {
      setResult(location.state.consultationResult)
      setLoading(false)
    } else {
      // Look for stored result in localStorage
      const stored = localStorage.getItem('oncoagent_result')
      if (stored) {
        try {
          setResult(JSON.parse(stored))
          setLoading(false)
        } catch (e) {
          // Invalid JSON
        }
      }
    }
    
    // Auto-clear after 5 minutes
    const timer = setTimeout(() => {
      navigate('/')
    }, 300000)

    return () => clearTimeout(timer)
  }, [location, navigate])

  const formatRiskLevel = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'high': return 'text-danger-600'
      case 'medium': return 'text-warning-600'
      case 'low': return 'text-green-600'
      default: return 'text-slate-600'
    }
  }
  
  const getRiskColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'high': return 'bg-danger-50'
      case 'medium': return 'bg-warning-50'
      case 'low': return 'bg-green-50'
      default: return 'bg-slate-50'
    }
  }
  
  if (loading) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <div className="text-center">
          <Activity className="w-12 h-12 text-primary-500 animate-spin mb-4" />
          <p className="text-lg text-slate-600">Loading results...</p>
        </div>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <div className="card text-center p-8 max-w-2xl">
          <X className="w-16 h-16 text-danger-500 mb-4" />
          <h2 className="text-xl font-semibold text-danger-600 mb-4">Error Loading Results</h2>
          <p className="text-sm text-danger-700">{error}</p>
          <button 
            onClick={() => navigate('/')}
            className="mt-6 btn-primary px-6 py-2"
          >
            Return Home
          </button>
        </div>
      </div>
    )
  }
  
  if (!result) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <div className="card text-center p-8 max-w-2xl">
          <Activity className="w-16 h-16 text-slate-400 mb-4" />
          <h2 className="text-xl font-semibold text-slate-600 mb-4">No Results Available</h2>
          <p className="text-sm text-slate-500 mb-6">
            No consultation results found. Please run a full consultation first.
          </p>
          <div className="flex justify-center gap-3">
            <Link to="/consultation" className="btn-primary px-4 py-2">
              Start Consultation
            </Link>
            <Link to="/" className="btn-secondary px-4 py-2">
              Go Home
            </Link>
          </div>
        </div>
      </div>
    )
  }
  
  return (
    <div className="max-w-6xl mx-auto px-4 py-4">
      <PageHeader
        eyebrow="Synthesis Report"
        title={<>Consultation <span className="gradient-text">Results</span></>}
        subtitle="The five agents have spoken — here is the fused, evidence-backed clinical picture."
      >
        <button
          onClick={() => openProfessionalReport(result)}
          className="btn-primary px-5 py-2.5"
        >
          <Download className="w-4 h-4" />
          Download Clinical Report
        </button>
        <button
          onClick={() => navigate('/')}
          className="btn-secondary px-5 py-2.5"
        >
          ← Back Home
        </button>
        <button
          onClick={() => {
            localStorage.removeItem('oncoagent_result')
            navigate('/')
          }}
          className="btn-danger px-5 py-2.5"
        >
          Clear Results
        </button>
      </PageHeader>

      {/* Header Info */}
      <div className="grid md:grid-cols-3 gap-4 mb-6">
        <div className="kpi-tile">
          <div className={`text-4xl font-bold gradient-text font-display ${formatRiskLevel(result.risk_level)}`}>
            {result.overall_risk}%
          </div>
          <div className="text-sm text-slate-400 mt-1">Overall Risk</div>
        </div>
        <div className="kpi-tile">
          <div className="text-4xl font-bold gradient-text font-display">
            {result.confidence_score || result.confidence || 0}%
          </div>
          <div className="text-sm text-slate-400 mt-1">Confidence</div>
        </div>
        <div className="kpi-tile">
          <div className="text-4xl font-bold gradient-text font-display">
            {result.agent_agreement || 0}%
          </div>
          <div className="text-sm text-slate-400 mt-1">Agent Consensus</div>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Left Column: Visualizations */}
        <div className="space-y-6">
          {/* Risk Gauge */}
          <div className="card">
            <h3 className="text-lg font-semibold text-slate-800 mb-3">Overall Risk Assessment</h3>
            <div className="relative h-12 w-full bg-slate-200 rounded-lg overflow-hidden">
              <div className="absolute inset-0 flex items-center justify-center text-white font-bold">
                {result.overall_risk}% Risk
              </div>
              <div 
                className={`absolute left-0 top-0 h-full ${getRiskColor(result.risk_level)}`} 
                style={{ width: `${result.overall_risk}%` }}
              />
            </div>
          </div>
          
          {/* Agent Status */}
          <div className="card">
            <h3 className="text-lg font-semibold text-slate-800 mb-3">Agent Status</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span>Imaging Agent</span>
                <span className="font-medium">{result.imaging_result?.has_tumor ? 'Tumor Detected' : 'Clear'}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span>Symptom Agent</span>
                <span className="font-medium">{result.symptom_result?.risk_level}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span>Literature Agent</span>
                <span className="font-medium">{result.literature_result?.papers?.length || 0} Papers</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span>Advisory Agent</span>
                <span className="font-medium">Recommendations Ready</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span>Synthesis Agent</span>
                <span className="font-medium">Report Generated</span>
              </div>
            </div>
          </div>
          
          {/* Literature Summary */}
          {result.literature_result?.papers && result.literature_result.papers.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-slate-800 mb-3">Key Literature Findings</h3>
              <div className="space-y-2">
                {result.literature_result.papers.slice(0, 3).map((paper: any, index: number) => (
                  <div key={index} className="p-3 bg-slate-50 rounded">
                    <h4 className="font-medium text-slate-800 mb-1">{paper.title}</h4>
                    <p className="text-xs text-slate-600">PMID: {paper.pmid} • {paper.journal}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        
        {/* Right Column: Detailed Report */}
        <div className="space-y-6">
          {/* Executive Summary */}
          {result.summary && (
            <div className="card">
              <h3 className="text-lg font-semibold text-slate-800 mb-3">Executive Summary</h3>
              <p className="text-sm text-slate-700 leading-relaxed">{result.summary}</p>
            </div>
          )}
          
          {/* Critical Alerts */}
          {result.critical_alerts && result.critical_alerts.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-slate-800 mb-3">Critical Alerts</h3>
              <ul className="space-y-2 pl-5">
                {result.critical_alerts.map((alert: string, index: number) => (
                  <li key={index} className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-danger-500 mt-0.5" />
                    <span className="text-sm text-danger-700">{alert}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {/* Recommended Actions */}
          {result.recommended_next_steps && result.recommended_next_steps.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-slate-800 mb-3">Recommended Actions</h3>
              <ol className="list-decimal list-inside pl-5 space-y-2 text-sm text-slate-700">
                {result.recommended_next_steps.map((step: string, index: number) => (
                  <li key={index}>{step}</li>
                ))}
              </ol>
            </div>
          )}
          
          {/* Specialist Recommendations */}
          {result.doctors_to_consult && result.doctors_to_consult.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-slate-800 mb-3">Specialist Recommendations</h3>
              <div className="space-y-3">
                {result.doctors_to_consult.map((doc: any, index: number) => (
                  <div key={index} className="p-3 bg-slate-50 rounded border-l-4 border-primary-500">
                    <h4 className="font-medium text-slate-800">{doc.name}</h4>
                    <p className="text-xs text-slate-600">{doc.department}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Medications (Informational) */}
          {result.medications_info && result.medications_info.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-slate-800 mb-3">Medication Information</h3>
              <p className="text-xs text-slate-600 italic">
                {result.medications_info.map((med: any) => `${med.name}: ${med.what_it_does}`).join('. ')}
              </p>
              <p className="text-xs text-slate-600 italic mt-2">
                {result.medications_info.map((m: any) => m.simple_tip).join('. ')}
              </p>
              <p className="text-xs text-slate-600 italic mt-2">
                <strong>Important:</strong> This information is for educational purposes only. Always consult your doctor before taking any medication.
              </p>
            </div>
          )}
        </div>
      </div>
      
      {/* Nearby healthcare */}
      <div className="card mt-6">
        <NearbyLocator specialty={result.doctors_to_consult?.[0]?.name} />
      </div>

      {/* Footer Disclaimer */}
      <div className="mt-8 pt-6 border-t border-slate-200 text-center text-xs text-slate-400">
        <p>
          <strong>IMPORTANT DISCLAIMER:</strong> This AI system is for informational and educational purposes only. 
          It is NOT a substitute for professional medical advice, diagnosis, or treatment. 
          Always seek the advice of your physician or other qualified health provider with any questions you may have 
          regarding a medical condition. Do not disregard professional medical advice or delay in seeking it because of 
          content generated by this system.
        </p>
      </div>
    </div>
  )
}