'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Client, PaginatedResponse } from '@/lib/types'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Plus, Search, Edit, Trash2 } from 'lucide-react'
import Link from 'next/link'

export default function ClientsPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingClient, setEditingClient] = useState<Client | null>(null)

  const { data, isLoading } = useQuery<PaginatedResponse<Client>>({
    queryKey: ['clients', { search }],
    queryFn: () =>
      api
        .get('/api/v1/clients', { params: { search: search || undefined } })
        .then((res) => res.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/api/v1/clients/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
    },
  })

  const handleDelete = async (client: Client) => {
    if (confirm(`"${client.name}" 의뢰인을 삭제하시겠습니까?`)) {
      deleteMutation.mutate(client.id)
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">의뢰인 관리</h1>
          <button
            onClick={() => {
              setEditingClient(null)
              setShowModal(true)
            }}
            className="btn btn-primary flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            새 의뢰인
          </button>
        </div>

        {/* 검색 */}
        <div className="card">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="이름 또는 연락처로 검색..."
              className="input pl-10"
            />
          </div>
        </div>

        {/* 의뢰인 목록 */}
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
                    <th className="pb-3 font-medium">이름</th>
                    <th className="pb-3 font-medium">연락처</th>
                    <th className="pb-3 font-medium">이메일</th>
                    <th className="pb-3 font-medium">주소</th>
                    <th className="pb-3 font-medium">등록일</th>
                    <th className="pb-3 font-medium">관리</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((client) => (
                    <tr key={client.id} className="border-b last:border-0">
                      <td className="py-3">
                        <Link
                          href={`/clients/${client.id}`}
                          className="text-primary-600 hover:underline font-medium"
                        >
                          {client.name}
                        </Link>
                      </td>
                      <td className="py-3 text-sm">{client.phone || '-'}</td>
                      <td className="py-3 text-sm">{client.email || '-'}</td>
                      <td className="py-3 text-sm truncate max-w-[200px]">
                        {client.address || '-'}
                      </td>
                      <td className="py-3 text-sm text-gray-500">
                        {new Date(client.created_at).toLocaleDateString('ko-KR')}
                      </td>
                      <td className="py-3">
                        <div className="flex gap-2">
                          <button
                            onClick={() => {
                              setEditingClient(client)
                              setShowModal(true)
                            }}
                            className="p-1 text-gray-500 hover:text-primary-600"
                            title="수정"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(client)}
                            className="p-1 text-gray-500 hover:text-red-600"
                            title="삭제"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">
              {search ? '검색 결과가 없습니다' : '등록된 의뢰인이 없습니다'}
            </p>
          )}
        </div>

        {/* 의뢰인 등록/수정 모달 */}
        {showModal && (
          <ClientModal
            client={editingClient}
            onClose={() => setShowModal(false)}
            onSuccess={() => {
              setShowModal(false)
              queryClient.invalidateQueries({ queryKey: ['clients'] })
            }}
          />
        )}
      </div>
    </DashboardLayout>
  )
}

function ClientModal({
  client,
  onClose,
  onSuccess,
}: {
  client: Client | null
  onClose: () => void
  onSuccess: () => void
}) {
  const [formData, setFormData] = useState({
    name: client?.name || '',
    phone: client?.phone || '',
    email: client?.email || '',
    address: client?.address || '',
    memo: client?.memo || '',
    resident_number: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      if (client) {
        await api.put(`/api/v1/clients/${client.id}`, formData)
      } else {
        await api.post('/api/v1/clients', formData)
      }
      onSuccess()
    } catch (err: any) {
      const detail = err.response?.data?.detail
      if (Array.isArray(detail)) {
        // 유효성 검증 오류 배열 처리
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
      <div className="bg-white rounded-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-xl font-bold mb-4">
            {client ? '의뢰인 수정' : '새 의뢰인 등록'}
          </h2>

          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">이름 *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                className="input"
                required
              />
            </div>

            <div>
              <label className="label">주민등록번호</label>
              <input
                type="text"
                value={formData.resident_number}
                onChange={(e) =>
                  setFormData({ ...formData, resident_number: e.target.value })
                }
                className="input"
                placeholder="000000-0000000"
              />
              <p className="mt-1 text-xs text-gray-500">
                암호화하여 안전하게 저장됩니다
              </p>
            </div>

            <div>
              <label className="label">연락처</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) =>
                  setFormData({ ...formData, phone: e.target.value })
                }
                className="input"
                placeholder="010-0000-0000"
              />
            </div>

            <div>
              <label className="label">이메일</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
                className="input"
              />
            </div>

            <div>
              <label className="label">주소</label>
              <input
                type="text"
                value={formData.address}
                onChange={(e) =>
                  setFormData({ ...formData, address: e.target.value })
                }
                className="input"
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
                {loading ? '저장 중...' : '저장'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
