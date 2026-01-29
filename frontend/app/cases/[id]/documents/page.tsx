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
  Loader2,
} from 'lucide-react'
import Link from 'next/link'
import { useParams } from 'next/navigation'

// 자동 발급 지원 서류
const AUTO_ISSUE_TYPES = [
  'health_insurance_cert',
  'pension_cert',
  'resident_register',
  'resident_abstract',
  'income_cert',
  'local_tax_cert',
]

export default function CaseDocumentsPage() {
  const params = useParams()
  const caseId = params.id as string
  const queryClient = useQueryClient()
  const [uploadType, setUploadType] = useState<string | null>(null)
  const [issuingType, setIssuingType] = useState<string | null>(null)
  const [issueError, setIssueError] = useState<string | null>(null)
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [pendingDocType, setPendingDocType] = useState<string | null>(null)

  const { data: documents, isLoading } = useQuery<RequiredDocument[]>({
    queryKey: ['case-documents', caseId],
    queryFn: () =>
      api.get(`/api/v1/documents/case/${caseId}`).then((res) => res.data),
  })

  const { data: caseData } = useQuery({
    queryKey: ['case', caseId],
    queryFn: () => api.get(`/api/v1/cases/${caseId}`).then((res) => res.data),
  })

  // 의뢰인 인증서 상태 조회
  const { data: certStatus } = useQuery({
    queryKey: ['client-certificate', caseData?.client_id],
    queryFn: () =>
      caseData?.client_id
        ? api.get(`/api/v1/clients/${caseData.client_id}/certificate`).then((res) => res.data)
        : null,
    enabled: !!caseData?.client_id,
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

  // 자동 발급 mutation
  const autoIssueMutation = useMutation({
    mutationFn: async ({ documentType, useCertificate }: { documentType: string; useCertificate: boolean }) => {
      setIssuingType(documentType)
      setIssueError(null)
      return api.post(`/api/v1/documents/auto-issue/${caseId}/${documentType}`, {
        cert_type: useCertificate ? 'CERT' : 'KAKAO',
        use_certificate: useCertificate,
      })
    },
    onSuccess: (response) => {
      if (response.data.success) {
        queryClient.invalidateQueries({ queryKey: ['case-documents', caseId] })
        alert(`${response.data.message}`)
      } else {
        setIssueError(response.data.message)
      }
      setIssuingType(null)
      setShowAuthModal(false)
      setPendingDocType(null)
    },
    onError: (error: any) => {
      setIssueError(error.response?.data?.detail || '자동 발급 실패')
      setIssuingType(null)
      setShowAuthModal(false)
      setPendingDocType(null)
    },
  })

  const handleAutoIssue = (documentType: string) => {
    // 인증서가 등록되어 있으면 인증 방식 선택 모달 표시
    if (certStatus?.has_certificate && !certStatus?.is_expired) {
      setPendingDocType(documentType)
      setShowAuthModal(true)
    } else {
      // 인증서 없으면 바로 카카오 인증으로 진행
      if (confirm('카카오 인증을 통해 서류를 자동 발급하시겠습니까?')) {
        autoIssueMutation.mutate({ documentType, useCertificate: false })
      }
    }
  }

  const handleAuthMethodSelect = (useCertificate: boolean) => {
    if (pendingDocType) {
      autoIssueMutation.mutate({ documentType: pendingDocType, useCertificate })
    }
  }

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

        {/* 에러 메시지 */}
        {issueError && (
          <div className="card bg-red-50 border-red-200">
            <p className="text-red-700 text-sm">{issueError}</p>
          </div>
        )}

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
                        {/* 자동발급 버튼 */}
                        {AUTO_ISSUE_TYPES.includes(doc.document_type) && (
                          <button
                            onClick={() => handleAutoIssue(doc.document_type)}
                            disabled={issuingType === doc.document_type}
                            className="btn btn-secondary text-sm flex items-center gap-1 bg-yellow-50 border-yellow-300 text-yellow-700 hover:bg-yellow-100"
                          >
                            {issuingType === doc.document_type ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Zap className="h-4 w-4" />
                            )}
                            자동발급
                          </button>
                        )}
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

        {/* 인증 방식 선택 모달 */}
        {showAuthModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-md w-full p-6">
              <h3 className="text-lg font-bold mb-4">인증 방식 선택</h3>
              <p className="text-sm text-gray-600 mb-4">
                서류 자동 발급에 사용할 인증 방식을 선택하세요.
              </p>

              <div className="space-y-3">
                <button
                  onClick={() => handleAuthMethodSelect(true)}
                  disabled={issuingType !== null}
                  className="w-full p-4 border-2 border-green-200 rounded-lg hover:bg-green-50 text-left transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                      <Zap className="h-5 w-5 text-green-600" />
                    </div>
                    <div>
                      <p className="font-medium text-green-800">공동인증서</p>
                      <p className="text-sm text-gray-500">등록된 인증서로 즉시 발급</p>
                    </div>
                  </div>
                </button>

                <button
                  onClick={() => handleAuthMethodSelect(false)}
                  disabled={issuingType !== null}
                  className="w-full p-4 border-2 border-yellow-200 rounded-lg hover:bg-yellow-50 text-left transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center">
                      <Zap className="h-5 w-5 text-yellow-600" />
                    </div>
                    <div>
                      <p className="font-medium text-yellow-800">카카오 인증</p>
                      <p className="text-sm text-gray-500">의뢰인 휴대폰에서 인증 승인 필요</p>
                    </div>
                  </div>
                </button>
              </div>

              <button
                onClick={() => {
                  setShowAuthModal(false)
                  setPendingDocType(null)
                }}
                className="mt-4 w-full btn btn-secondary"
              >
                취소
              </button>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
