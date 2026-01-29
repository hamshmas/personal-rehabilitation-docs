'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import {
  Case,
  Client,
  PaginatedResponse,
  CourtType,
  COURT_NAMES,
  CASE_STATUS_NAMES,
} from '@/lib/types'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Plus, Filter, FileText } from 'lucide-react'
import Link from 'next/link'

export default function CasesPage() {
  const queryClient = useQueryClient()
  const [courtFilter, setCourtFilter] = useState<CourtType | ''>('')
  const [statusFilter, setStatusFilter] = useState('')
  const [showModal, setShowModal] = useState(false)

  const { data, isLoading } = useQuery<PaginatedResponse<Case>>({
    queryKey: ['cases', { court_type: courtFilter, status: statusFilter }],
    queryFn: () =>
      api
        .get('/api/v1/cases', {
          params: {
            court_type: courtFilter || undefined,
            status: statusFilter || undefined,
          },
        })
        .then((res) => res.data),
  })

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">사건 관리</h1>
          <button
            onClick={() => setShowModal(true)}
            className="btn btn-primary flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            새 사건
          </button>
        </div>

        {/* 필터 */}
        <div className="card flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <span className="text-sm text-gray-500">필터:</span>
          </div>
          <select
            value={courtFilter}
            onChange={(e) => setCourtFilter(e.target.value as CourtType | '')}
            className="input w-auto"
          >
            <option value="">전체 법원</option>
            {Object.entries(COURT_NAMES).map(([value, name]) => (
              <option key={value} value={value}>
                {name}
              </option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input w-auto"
          >
            <option value="">전체 상태</option>
            {Object.entries(CASE_STATUS_NAMES).map(([value, name]) => (
              <option key={value} value={value}>
                {name}
              </option>
            ))}
          </select>
        </div>

        {/* 사건 목록 */}
        <div className="card">
          {isLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            </div>
          ) : data?.items.length ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-sm text-gray-500 border-b">
                    <th className="pb-3 font-medium">의뢰인</th>
                    <th className="pb-3 font-medium">법원</th>
                    <th className="pb-3 font-medium">사건번호</th>
                    <th className="pb-3 font-medium">상태</th>
                    <th className="pb-3 font-medium">등록일</th>
                    <th className="pb-3 font-medium">서류</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((caseItem) => (
                    <tr key={caseItem.id} className="border-b last:border-0">
                      <td className="py-3">
                        <Link
                          href={`/cases/${caseItem.id}`}
                          className="text-primary-600 hover:underline font-medium"
                        >
                          {caseItem.client?.name || '-'}
                        </Link>
                      </td>
                      <td className="py-3 text-sm">
                        {COURT_NAMES[caseItem.court_type]}
                      </td>
                      <td className="py-3 text-sm">
                        {caseItem.case_number || '-'}
                      </td>
                      <td className="py-3">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${
                            caseItem.status === 'completed'
                              ? 'bg-green-100 text-green-700'
                              : caseItem.status === 'document_preparation'
                              ? 'bg-yellow-100 text-yellow-700'
                              : caseItem.status === 'rejected'
                              ? 'bg-red-100 text-red-700'
                              : 'bg-blue-100 text-blue-700'
                          }`}
                        >
                          {CASE_STATUS_NAMES[caseItem.status]}
                        </span>
                      </td>
                      <td className="py-3 text-sm text-gray-500">
                        {new Date(caseItem.created_at).toLocaleDateString('ko-KR')}
                      </td>
                      <td className="py-3">
                        <Link
                          href={`/cases/${caseItem.id}/documents`}
                          className="flex items-center gap-1 text-gray-500 hover:text-primary-600"
                        >
                          <FileText className="h-4 w-4" />
                          <span className="text-sm">서류</span>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">등록된 사건이 없습니다</p>
          )}
        </div>

        {/* 사건 등록 모달 */}
        {showModal && (
          <CaseModal
            onClose={() => setShowModal(false)}
            onSuccess={() => {
              setShowModal(false)
              queryClient.invalidateQueries({ queryKey: ['cases'] })
            }}
          />
        )}
      </div>
    </DashboardLayout>
  )
}

function CaseModal({
  onClose,
  onSuccess,
}: {
  onClose: () => void
  onSuccess: () => void
}) {
  const [formData, setFormData] = useState({
    client_id: '',
    court_type: 'daegu' as CourtType,
    case_number: '',
    memo: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const { data: clientsData } = useQuery<PaginatedResponse<Client>>({
    queryKey: ['clients', { limit: 100 }],
    queryFn: () => api.get('/api/v1/clients?limit=100').then((res) => res.data),
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      await api.post('/api/v1/cases', {
        ...formData,
        client_id: parseInt(formData.client_id),
      })
      onSuccess()
    } catch (err: any) {
      const detail = err.response?.data?.detail
      if (Array.isArray(detail)) {
        setError(detail.map((e: any) => e.msg || e.message || JSON.stringify(e)).join(', '))
      } else if (typeof detail === 'object') {
        setError(JSON.stringify(detail))
      } else {
        setError(detail || '저장에 실패했습니다')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-lg w-full">
        <div className="p-6">
          <h2 className="text-xl font-bold mb-4">새 사건 등록</h2>

          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">의뢰인 *</label>
              <select
                value={formData.client_id}
                onChange={(e) =>
                  setFormData({ ...formData, client_id: e.target.value })
                }
                className="input"
                required
              >
                <option value="">선택하세요</option>
                {clientsData?.items.map((client) => (
                  <option key={client.id} value={client.id}>
                    {client.name} {client.phone && `(${client.phone})`}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">관할 법원 *</label>
              <select
                value={formData.court_type}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    court_type: e.target.value as CourtType,
                  })
                }
                className="input"
                required
              >
                {Object.entries(COURT_NAMES).map(([value, name]) => (
                  <option key={value} value={value}>
                    {name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">사건번호</label>
              <input
                type="text"
                value={formData.case_number}
                onChange={(e) =>
                  setFormData({ ...formData, case_number: e.target.value })
                }
                className="input"
                placeholder="2024개회0000"
              />
            </div>

            <div>
              <label className="label">메모</label>
              <textarea
                value={formData.memo}
                onChange={(e) =>
                  setFormData({ ...formData, memo: e.target.value })
                }
                className="input"
                rows={3}
              />
            </div>

            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 btn btn-secondary"
              >
                취소
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 btn btn-primary disabled:opacity-50"
              >
                {loading ? '등록 중...' : '등록'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
