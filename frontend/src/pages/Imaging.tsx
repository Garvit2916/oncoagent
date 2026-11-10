import { useState } from 'react'
import { Upload, X, CheckCircle, Download } from 'lucide-react'
import { apiClient } from '../services/api'
import PageHeader from '../components/PageHeader'
import { openProfessionalReport } from '../utils/report'

export default function Imaging() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [organHint, setOrganHint] = useState<'liver' | 'lung' | 'brain' | 'pancreas' | 'colon' | 'breast'>('lung')
  
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setPreview(URL.createObjectURL(file))
      setResult(null)
      setError(null)
    }
  }
  
  const removeFile = () => {
    setSelectedFile(null)
    if (preview) URL.revokeObjectURL(preview)
    setPreview(null)
    setResult(null)
  }
  
  const handleAnalyze = async () => {
    if (!selectedFile) return
    
    setIsAnalyzing(true)
    setError(null)
    
    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('organ_hint', organHint)
      
      const response = await apiClient.post('/api/v1/imaging', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed')
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-4">
      <PageHeader
        eyebrow="Diagnostic Imaging"
        title={<>Medical <span className="gradient-text">Image Analysis</span></>}
        subtitle="YOLOv8 organ detection and Attention U-Net lesion segmentation on your uploaded scan of any of the six supported organs."
      />
      
      <div className="card mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Upload Medical Scan</h2>
        <p className="text-sm text-slate-600 mb-4">Supported formats: PNG, JPG, DICOM, NIfTI (.nii/.nii.gz)</p>
        
        {/* File Upload */}
        <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center mb-4">
          <Upload className="w-12 h-12 text-slate-400 mx-auto mb-2" />
          <p className="text-sm text-slate-600 mb-2">
            <label className="cursor-pointer text-primary-600 hover:underline">
              Click to upload
              <input type="file" className="hidden" accept=".png,.jpg,.jpeg,.bmp,.nii,.nii.gz" onChange={handleFileSelect} />
            </label>
            {' '}or drag and drop
          </p>
          <p className="text-xs text-slate-500">CT, MRI, or X-ray images</p>
        </div>
        
        {/* Preview */}
        {preview && (
          <div className="relative mb-4">
            <img src={preview} alt="Preview" className="w-full max-h-64 object-contain rounded-lg border border-slate-200" />
            <button 
              onClick={removeFile}
              className="absolute top-2 right-2 w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-md hover:bg-slate-100"
            >
              <X className="w-5 h-5 text-slate-600" />
            </button>
          </div>
        )}
        
        {/* Organ Hint */}
        <select 
          value={organHint}
          onChange={(e) => setOrganHint(e.target.value as any)}
          className="input-field mb-4"
        >
          <option value="lung">Lung</option>
          <option value="brain">Brain</option>
          <option value="liver">Liver</option>
          <option value="pancreas">Pancreas</option>
          <option value="colon">Colon</option>
          <option value="breast">Breast</option>
        </select>
        
        {/* Analyze Button */}
        <button
          onClick={handleAnalyze}
          disabled={!selectedFile || isAnalyzing}
          className="w-full btn-primary text-lg py-3"
        >
          {isAnalyzing ? 'Analyzing Scan...' : 'Analyze Image'}
        </button>
      </div>
      
      {/* Results */}
      {result && (
        <div className="card border-primary-200">
          <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
            <div className="flex items-center gap-3">
              <CheckCircle className="w-6 h-6 text-primary-600" />
              <h2 className="text-xl font-semibold text-slate-800">Analysis Results</h2>
            </div>
            <button
              onClick={() => openProfessionalReport(result)}
              className="btn-primary px-4 py-2.5"
            >
              <Download className="w-4 h-4" />
              Download Clinical Report (PDF)
            </button>
          </div>
          
          <div className="grid md:grid-cols-2 gap-6">
            {/* Original Image */}
            {result.mask_base64 && (
              <div>
                <h3 className="text-sm font-medium text-slate-600 mb-2">Segmentation Mask</h3>
                <img 
                  src={`data:image/png;base64,${result.mask_base64}`}
                  alt="Segmentation Mask"
                  className="w-full rounded-lg border border-slate-200"
                />
              </div>
            )}
            
            {/* Results Summary */}
            <div className="space-y-3">
              <div className="bg-slate-50 p-3 rounded-lg">
                <div className="text-sm text-slate-500 mb-1">Organ Detected</div>
                <div className="font-medium text-slate-800">{result.organ}</div>
              </div>
              
              <div className="bg-slate-50 p-3 rounded-lg">
                <div className="text-sm text-slate-500 mb-1">Tumor Confidence</div>
                <div className="font-medium text-slate-800">
                  {((result.tumor_confidence ?? result.confidence ?? 0) * 100).toFixed(1)}%
                </div>
              </div>
              
              <div className="bg-slate-50 p-3 rounded-lg">
                <div className="text-sm text-slate-500 mb-1">Has Tumor</div>
                <div className={`font-medium ${result.has_tumor ? 'text-danger-600' : 'text-green-600'}`}>
                  {result.has_tumor ? 'Yes' : 'No'}
                </div>
              </div>
              
              {result.tumor_volume_ratio && (
                <div className="bg-slate-50 p-3 rounded-lg">
                  <div className="text-sm text-slate-500 mb-1">Tumor Volume Ratio</div>
                  <div className="font-medium text-slate-800">{(result.tumor_volume_ratio * 100).toFixed(2)}%</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* Error */}
      {error && (
        <div className="card bg-danger-50 border-danger-200">
          <div className="text-danger-700">{error}</div>
        </div>
      )}
    </div>
  )
}