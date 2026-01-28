'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { RequiredDocument, DOCUMENT_STATUS_NAMES } from '@/lib/types'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import {
  CheckCircle,
  Clock,
  Circle,
  Upload,
  ExternalLink,
  Zap,
  ArrowLeft,
} from 'lucide-react'
import Link from 'next/link'
import { useParams } from 'next/navigation'

export default function CaseDocumentsPage() {
  const params = useParams()
  const caseId = params.id as string
  const queryClient = useQueryClient()
  const [uploadType, setUploadType] = useState<string | null>(null)

  const { data: documents, isLoading } = useQuery<RequiredDocument[]>({
    queryKey: ['case-documents', caseId],
    queryFn: () =>
      api.get(`/api/v1/documents/case/${caseId}`).then((res) => res.data),
  })

  const { data: caseData } = useQuery({
    queryKey: ['case', caseId],
    queryFn: () => api.get(`/api/v1/cases/${caseId}`).then((res) => res.data),
  })

  const uploadMutation = useMutation({
    mutationFn: async ({
      documentType,
      file,
    }: {
      documentType: string
      file: File
    }) => {
      const formData = new FormData()
      formData.append('file', file)
      return api.post(
        `/api/v1/documents/upload/${caseId}?document_type=${documentType}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['case-documents', caseId] })
      setUploadType(null)
    },
  })

  const handleFileUpload = (documentType: string, file: File) => {
    uploadMutation.mutate({ documentType, file })
  }

  const completedCount = documents?.filter((d) => d.status === 'completed').length || 0
  const totalCount = documents?.length || 0
  const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0

  const StatusIcon = ({ status }: { status: string }) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'in_progress':
        return <Clock className="h-5 w-5 text-yellow-500" />
      default:
        return <Circle className="h-5 w-5 text-gray-300" />
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* 헤더 */}
        <div className="flex items-center gap-4">
          <Link
            href="/cases"
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">서류 관리</h1>
            <p className="text-sm text-gray-500">
              {caseData?.client?.name} - {caseData?.case_number || '사건번호 미입력'}
            </p>
          </div>
        </div>

        {/* 진행률 */}
        <div className="card">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">서류 준비 현황</span>
            <span className="text-sm text-gray-500">
              {completedCount} / {totalCount} 완료 ({progressPercent}%)
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary-600 h-2 rounded-full transition-all"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* 서류 목록 */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">필요 서류 목록</h2>

          {isLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            </div>
          ) : (
            <div className="space-y-3">
              {documents?.map((doc) => (
                <div
                  key={doc.id}
                  className={`flex items-center justify-between p-4 rounded-lg border ${
                    doc.status === 'completed'
                      ? 'bg-green-50 border-green-200'
                      : 'bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <StatusIcon status={doc.status} />
                    <div>
                      <p className="font-medium text-gray-900">{doc.document_name}</p>
                      <p className="text-sm text-gray-500">
                        {DOCUMENT_STATUS_NAMES[doc.status]}
                        {doc.auto_available && (
                          <span className="ml-2 text-primary-600">
                            <Zap className="h-3 w-3 inline" /> 자동발급 가능
                          </span>
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {doc.status !== 'completed' && (
                      <>
                        {doc.issue_url && (
                          <a
                            href={doc.issue_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-secondary text-sm flex items-center gap-1"
                          >
                            <ExternalLink className="h-4 w-4" />
                            발급 링크
                          </a>
                        )}
                        <label className="btn btn-primary text-sm flex items-center gap-1 cursor-pointer">
                          <Upload className="h-4 w-4" />
                          업로드
                          <input
                            type="file"
                            className="hidden"
                            accept=".pdf,.jpg,.jpeg,.png"
                            onChange={(e) => {
                              const file = e.target.files?.[0]
                              if (file) {
                                handleFileUpload(doc.document_type, file)
                              }
                            }}
                          />
                        </label>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
