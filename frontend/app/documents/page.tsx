'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Case, CASE_STATUS_NAMES, COURT_NAMES } from '@/lib/types'
import { FileText, CheckCircle, Clock, AlertCircle } from 'lucide-react'
import Link from 'next/link'

interface CaseWithDocStatus extends Case {
  document_status?: {
    total: number
    completed: number
  }
}

export default function DocumentsPage() {
  const { data: cases, isLoading } = useQuery<CaseWithDocStatus[]>({
    queryKey: ['cases-with-docs'],
    queryFn: async () => {
      const res = await api.get('/api/v1/cases')
      return res.data.items || res.data
    },
  })

  const getProgressColor = (completed: number, total: number) => {
    if (total === 0) return 'bg-gray-200'
    const percent = (completed / total) * 100
    if (percent === 100) return 'bg-green-500'
    if (percent >= 50) return 'bg-yellow-500'
    return 'bg-red-400'
  }

  const getStatusIcon = (completed: number, total: number) => {
    if (total === 0) return <AlertCircle className="h-5 w-5 text-gray-400" />
    const percent = (completed / total) * 100
    if (percent === 100) return <CheckCircle className="h-5 w-5 text-green-500" />
    if (percent >= 50) return <Clock className="h-5 w-5 text-yellow-500" />
    return <AlertCircle className="h-5 w-5 text-red-400" />
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">서류 관리</h1>
        </div>

        <div className="card">
          <p className="text-sm text-gray-600 mb-4">
            사건을 선택하여 해당 사건의 서류를 관리하세요.
          </p>

          {isLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            </div>
          ) : cases?.length ? (
            <div className="space-y-3">
              {cases.map((caseItem) => {
                const completed = caseItem.document_status?.completed || 0
                const total = caseItem.document_status?.total || 0
                const percent = total > 0 ? Math.round((completed / total) * 100) : 0

                return (
                  <Link
                    key={caseItem.id}
                    href={`/cases/${caseItem.id}/documents`}
                    className="block p-4 border rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <FileText className="h-8 w-8 text-primary-600" />
                        <div>
                          <p className="font-medium text-gray-900">
                            {caseItem.client?.name || '의뢰인 미지정'}
                          </p>
                          <p className="text-sm text-gray-500">
                            {caseItem.case_number || '사건번호 미입력'} · {COURT_NAMES[caseItem.court_type]}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-sm font-medium text-gray-700">
                            {completed} / {total} 완료
                          </p>
                          <div className="w-24 bg-gray-200 rounded-full h-2 mt-1">
                            <div
                              className={`h-2 rounded-full transition-all ${getProgressColor(completed, total)}`}
                              style={{ width: `${percent}%` }}
                            />
                          </div>
                        </div>
                        {getStatusIcon(completed, total)}
                      </div>
                    </div>
                  </Link>
                )
              })}
            </div>
          ) : (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">등록된 사건이 없습니다</p>
              <Link
                href="/cases"
                className="inline-block mt-3 text-primary-600 hover:underline"
              >
                사건 등록하기
              </Link>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
