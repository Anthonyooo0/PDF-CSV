import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { Upload, FileText, Send, Download, Loader2, FileSpreadsheet, Image as ImageIcon, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface UploadResponse {
  file_id: string
  filename: string
  csv_path: string
  message: string
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  files?: FileInfo[]
  action_log?: string[]
}

interface FileInfo {
  file_id: string
  filename: string
  type: string
}

interface PreviewData {
  columns: string[]
  rows: Record<string, any>[]
  total_rows: number
  total_columns: number
}

function App() {
  const [fileId, setFileId] = useState<string | null>(null)
  const [filename, setFilename] = useState<string | null>(null)
  const [uploadMessage, setUploadMessage] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [previewData, setPreviewData] = useState<PreviewData | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Please select a PDF file')
      return
    }

    setIsUploading(true)
    setError(null)
    setUploadMessage(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${API_URL}/api/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Upload failed')
      }

      const data: UploadResponse = await response.json()
      setFileId(data.file_id)
      setFilename(data.filename)
      setUploadMessage(data.message)
      setMessages([])

      const previewResponse = await fetch(`${API_URL}/api/preview/${data.file_id}`)
      if (previewResponse.ok) {
        const preview: PreviewData = await previewResponse.json()
        setPreviewData(preview)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload file')
    } finally {
      setIsUploading(false)
    }
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !fileId || isSending) return

    const userMessage: ChatMessage = {
      role: 'user',
      content: inputMessage,
    }

    setMessages((prev) => [...prev, userMessage])
    setInputMessage('')
    setIsSending(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          file_id: fileId,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Chat request failed')
      }

      const data = await response.json()
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: data.response,
        files: data.files || [],
        action_log: data.action_log || [],
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message')
    } finally {
      setIsSending(false)
    }
  }

  const handleDownload = (fileId: string) => {
    window.open(`${API_URL}/api/download/${fileId}`, '_blank')
  }

  return (
    <div className="min-h-screen bg-bg p-4">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-8 pt-8"
        >
          <h1 className="text-4xl font-heading font-bold text-text mb-2">
            PDF to CSV + AI Analysis
          </h1>
          <p className="text-lg text-muted">
            Upload a PDF, extract tables, and analyze with AI
          </p>
        </motion.div>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4"
          >
            <Alert variant="destructive" className="bg-surface border-red-500/50">
              <XCircle className="h-4 w-4" />
              <AlertDescription className="text-red-400">{error}</AlertDescription>
            </Alert>
          </motion.div>
        )}

        {!fileId ? (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <Card className="max-w-2xl mx-auto border-2 border-dashed border-surface">
              <CardHeader>
                <CardTitle>Upload PDF</CardTitle>
                <CardDescription>
                  Upload a PDF with tables to extract and analyze data
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="border-2 border-dashed border-surface rounded-lg p-8 text-center hover:border-accent transition-colors cursor-pointer bg-surface">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf"
                    onChange={handleFileSelect}
                    className="hidden"
                    disabled={isUploading}
                  />
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className="flex flex-col items-center"
                  >
                    {isUploading ? (
                      <>
                        <Loader2 className="w-12 h-12 text-accent animate-spin mb-4" />
                        <p className="text-lg font-medium text-text">
                          Processing PDF...
                        </p>
                        <p className="text-sm text-muted mt-2">
                          Extracting tables from your PDF
                        </p>
                      </>
                    ) : (
                      <>
                        <Upload className="w-12 h-12 text-muted mb-4" />
                        <p className="text-lg font-heading font-medium text-text mb-2">
                          Drop your PDF here or click to browse
                        </p>
                        <p className="text-sm text-muted">
                          Supports both digital PDFs and scanned documents
                        </p>
                      </>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Extracted Data</CardTitle>
                      <CardDescription>{filename}</CardDescription>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setFileId(null)
                        setFilename(null)
                        setUploadMessage(null)
                        setPreviewData(null)
                        setMessages([])
                      }}
                      className="border-surface hover:bg-surface hover:text-accent"
                    >
                      New PDF
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {uploadMessage && (
                    <Alert className="mb-4 bg-bg border-accent/50">
                      <FileText className="h-4 w-4 text-accent" />
                      <AlertDescription className="text-text">{uploadMessage}</AlertDescription>
                    </Alert>
                  )}

                  {previewData && (
                    <div>
                      <div className="flex gap-2 mb-4">
                        <Badge variant="secondary" className="bg-accent/20 text-accent border-accent/50">
                          {previewData.total_rows} rows
                        </Badge>
                        <Badge variant="secondary" className="bg-accent/20 text-accent border-accent/50">
                          {previewData.total_columns} columns
                        </Badge>
                      </div>

                      <ScrollArea className="h-96 w-full border border-surface rounded-md">
                        <div className="p-4">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b border-surface">
                                {previewData.columns.map((col, i) => (
                                  <th
                                    key={i}
                                    className="text-left p-2 font-semibold text-accent bg-surface"
                                  >
                                    {col}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {previewData.rows.map((row, i) => (
                                <tr key={i} className="border-b border-surface hover:bg-surface/50">
                                  {previewData.columns.map((col, j) => (
                                    <td key={j} className="p-2 text-text">
                                      {row[col]?.toString() || ''}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </ScrollArea>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
            >
              <Card className="flex flex-col">
                <CardHeader>
                  <CardTitle>AI Analysis</CardTitle>
                  <CardDescription>
                    Ask the AI to clean, analyze, or transform your data
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex-1 flex flex-col">
                  <ScrollArea className="flex-1 h-96 mb-4 border border-surface rounded-md p-4 bg-bg">
                    {messages.length === 0 ? (
                      <div className="text-center text-muted py-8">
                        <p className="mb-4">Ask the AI to help with your data!</p>
                        <div className="text-sm text-left max-w-md mx-auto space-y-2">
                          <p className="font-semibold text-text">Example requests:</p>
                          <ul className="list-disc list-inside space-y-1">
                            <li>Clean the data and remove duplicates</li>
                            <li>Summarize totals by month</li>
                            <li>Find outliers in the price column</li>
                            <li>Create a bar chart of sales by region</li>
                            <li>Export cleaned data as Excel</li>
                          </ul>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {messages.map((msg, i) => (
                          <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.3 }}
                            className={`${
                              msg.role === 'user'
                                ? 'bg-accent ml-8'
                                : 'bg-surface mr-8 border border-surface'
                            } p-4 rounded-lg`}
                          >
                            <p className="font-semibold mb-2 text-text">
                              {msg.role === 'user' ? 'You' : 'AI Assistant'}
                            </p>
                            <p className={`text-sm whitespace-pre-wrap ${msg.role === 'user' ? 'text-white' : 'text-text'}`}>
                              {msg.content}
                            </p>

                            {msg.action_log && msg.action_log.length > 0 && (
                              <div className="mt-3 pt-3 border-t border-surface">
                                <p className="text-xs font-semibold mb-1 text-muted">
                                  Actions taken:
                                </p>
                                <ul className="text-xs space-y-1 text-muted">
                                  {msg.action_log.map((log, j) => (
                                    <li key={j}>• {log}</li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {msg.files && msg.files.length > 0 && (
                              <div className="mt-3 pt-3 border-t border-surface">
                                <p className="text-xs font-semibold mb-2 text-muted">
                                  Generated files:
                                </p>
                                <div className="space-y-2">
                                  {msg.files.map((file, j) => (
                                    <Button
                                      key={j}
                                      variant="outline"
                                      size="sm"
                                      onClick={() =>
                                        handleDownload(file.file_id)
                                      }
                                      className="w-full justify-start bg-accent/10 hover:bg-accent/20 text-accent border-accent/50"
                                    >
                                      {file.type.includes('csv') ? (
                                        <FileSpreadsheet className="w-4 h-4 mr-2" />
                                      ) : file.type.includes('excel') ||
                                        file.type.includes('spreadsheet') ? (
                                        <FileSpreadsheet className="w-4 h-4 mr-2" />
                                      ) : (
                                        <ImageIcon className="w-4 h-4 mr-2" />
                                      )}
                                      <Download className="w-3 h-3 mr-2" />
                                      {file.filename}
                                    </Button>
                                  ))}
                                </div>
                              </div>
                            )}
                          </motion.div>
                        ))}
                      </div>
                    )}
                  </ScrollArea>

                  <div className="flex gap-2">
                    <Input
                      placeholder="Ask the AI to analyze your data..."
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault()
                          handleSendMessage()
                        }
                      }}
                      disabled={isSending}
                      className="bg-surface border-surface text-text focus:ring-accent"
                    />
                    <Button
                      onClick={handleSendMessage}
                      disabled={!inputMessage.trim() || isSending}
                      className="bg-accent hover:bg-accent/90 text-white"
                    >
                      {isSending ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Send className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
