'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Case, Client, COURT_NAMES, CASE_STATUS_NAMES } from '@/lib/types'
import Link from 'next/link'
import { FileText, Users, Briefcase, AlertCircle } from 'lucide-react'
import { DashboardLayout } from '@/components/layout/DashboardLayout'

export default function DashboardPage() {
  const { data: casesData } = useQuery({
    queryKey: ['cases', { limit: 5 }],
    queryFn: () => api.get('/api/v1/cases?limit=5').then((res) => res.data),
  })

  const { data: clientsData } = useQuery({
    queryKey: ['clients', { limit: 5 }],
    queryFn: () => api.get('/api/v1/clients?limit=5').then((res) => res.data),
  })

  const recentCases = casesData?.items || []
  const totalCases = casesData?.total || 0
  const totalClients = clientsData?.total || 0

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">대시보드</h1>

        {/* 통계 카드 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card flex items-center gap-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Users className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">전체 의뢰인</p>
              <p className="text-2xl font-bold">{totalClients}</p>
            </div>
          </div>

          <div className="card flex items-center gap-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <Briefcase className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">전체 사건</p>
              <p className="text-2xl font-bold">{totalCases}</p>
            </div>
          </div>

          <div className="card flex items-center gap-4">
            <div className="p-3 bg-orange-100 rounded-lg">
              <AlertCircle className="h-6 w-6 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">서류 준비중</p>
              <p className="text-2xl font-bold">
                {recentCases.filter((c: Case) => c.status === 'document_preparation').length}
              </p>
            </div>
          </div>
        </div>

        {/* 최근 사건 */}
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">최근 사건</h2>
            <Link href="/cases" className="text-primary-600 hover:text-primary-700 text-sm">
              전체 보기
            </Link>
          </div>

          {recentCases.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-sm text-gray-500 border-b">
                    <th className="pb-3 font-medium">의뢰인</th>
                    <th className="pb-3 font-medium">법원</th>
                    <th className="pb-3 font-medium">사건번호</th>
                    <th className="pb-3 font-medium">상태</th>
                    <th className="pb-3 font-medium">등록일</th>
                  </tr>
                </thead>
                <tbody>
                  {recentCases.map((caseItem: Case) => (
                    <tr key={caseItem.id} className="border-b last:border-0">
                      <td className="py-3">
                        <Link
                          href={`/cases/${caseItem.id}`}
                          className="text-primary-600 hover:underline"
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
                              : 'bg-blue-100 text-blue-700'
                          }`}
                        >
                          {CASE_STATUS_NAMES[caseItem.status]}
                        </span>
                      </td>
                      <td className="py-3 text-sm text-gray-500">
                        {new Date(caseItem.created_at).toLocaleDateString('ko-KR')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">
              등록된 사건이 없습니다
            </p>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
