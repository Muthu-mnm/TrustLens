import React, { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { UploadCloud, File, FileText, Image as ImageIcon, Trash2, AlertCircle } from 'lucide-react'

export default function FileDropzone({ files = [], onFilesChange, disabled = false }) {
  const [errorMessage, setErrorMessage] = useState(null)

  const onDrop = useCallback(
    (acceptedFiles, rejectedFiles) => {
      setErrorMessage(null)

      if (rejectedFiles && rejectedFiles.length > 0) {
        const rejection = rejectedFiles[0]
        const firstError = rejection.errors[0]
        if (firstError?.code === 'file-too-large') {
          setErrorMessage(`File "${rejection.file.name}" exceeds the maximum allowed size of 20MB.`)
        } else if (firstError?.code === 'file-invalid-type') {
          setErrorMessage(`File "${rejection.file.name}" has an unsupported format. Please upload PDF, PNG, JPG, or TIFF.`)
        } else {
          setErrorMessage(firstError?.message || 'Some files could not be accepted.')
        }
      }

      if (acceptedFiles && acceptedFiles.length > 0) {
        // Prevent exact duplicates by filename + size
        const existingSignatures = new Set(files.map((f) => `${f.name}_${f.size}`))
        const newUnique = acceptedFiles.filter(
          (f) => !existingSignatures.has(`${f.name}_${f.size}`)
        )

        onFilesChange([...files, ...newUnique])
      }
    },
    [files, onFilesChange]
  )

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    disabled,
    maxSize: 20 * 1024 * 1024, // 20 MB
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/tiff': ['.tiff', '.tif'],
    },
  })

  const removeFile = (indexToRemove) => {
    onFilesChange(files.filter((_, idx) => idx !== indexToRemove))
  }

  const formatFileSize = (bytes) => {
    if (!bytes || bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getFileIcon = (file) => {
    const type = file.type || ''
    const name = file.name || ''
    if (type.includes('pdf') || name.endsWith('.pdf')) {
      return <FileText className="w-5 h-5 text-red-500 flex-shrink-0" />
    }
    if (
      type.includes('image') ||
      name.endsWith('.png') ||
      name.endsWith('.jpg') ||
      name.endsWith('.jpeg') ||
      name.endsWith('.tiff')
    ) {
      return <ImageIcon className="w-5 h-5 text-blue-500 flex-shrink-0" />
    }
    return <File className="w-5 h-5 text-slate-500 flex-shrink-0" />
  }

  return (
    <div className="space-y-4">
      {/* Drop Area */}
      <div
        {...getRootProps()}
        className={`relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-200 select-none ${
          disabled
            ? 'opacity-60 cursor-not-allowed bg-slate-100 border-slate-300'
            : isDragActive && !isDragReject
            ? 'border-blue-600 bg-blue-50/80 ring-4 ring-blue-100 scale-[1.01]'
            : isDragReject
            ? 'border-rose-500 bg-rose-50/80 ring-4 ring-rose-100'
            : 'border-slate-300 hover:border-blue-500 bg-white hover:bg-slate-50/60 shadow-sm'
        }`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center justify-center space-y-3">
          <div
            className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-colors ${
              isDragActive
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
                : 'bg-blue-50 text-blue-700'
            }`}
          >
            <UploadCloud className="w-7 h-7" />
          </div>

          <div className="space-y-1">
            <p className="text-sm font-semibold text-slate-800">
              {isDragActive
                ? 'Drop the files here...'
                : 'Drag and drop files here, or click to browse'}
            </p>
            <p className="text-xs text-slate-500">
              Supported formats: <strong className="font-semibold text-slate-700">PDF, JPG, PNG, TIFF</strong> (Max 20MB per file)
            </p>
          </div>

          <span className="inline-flex items-center px-3 py-1 rounded-full text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
            Multi-file upload enabled
          </span>
        </div>
      </div>

      {/* Error message */}
      {errorMessage && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* File List */}
      {files && files.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-600 px-1">
            <span>Selected Documents ({files.length})</span>
            <span>
              Total Size:{' '}
              {formatFileSize(files.reduce((acc, f) => acc + (f.size || 0), 0))}
            </span>
          </div>

          <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl bg-white overflow-hidden shadow-sm">
            {files.map((file, idx) => (
              <div
                key={`${file.name}_${idx}`}
                className="p-3 flex items-center justify-between gap-3 hover:bg-slate-50/80 transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
                    {getFileIcon(file)}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-slate-800 truncate">
                      {file.name}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-slate-400">
                      <span>{formatFileSize(file.size)}</span>
                      <span>•</span>
                      <span className="uppercase">{file.name.split('.').pop()}</span>
                    </div>
                  </div>
                </div>

                {!disabled && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation()
                      removeFile(idx)
                    }}
                    title="Remove file"
                    className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors flex-shrink-0"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
