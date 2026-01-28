// 사용자
export interface User {
  id: number
  email: string
  name: string
  role: 'admin' | 'staff'
  is_active: boolean
  created_at: string
}

// 의뢰인
export interface Client {
  id: number
  name: string
  phone?: string
  email?: string
  address?: string
  memo?: string
  created_at: string
  cases?: Case[]
}

// 법원 유형
export type CourtType = 'daegu' | 'busan' | 'daejeon' | 'jeonju' | 'cheongju'

export const COURT_NAMES: Record<CourtType, string> = {
  daegu: '대구지방법원',
  busan: '부산회생법원',
  daejeon: '대전지방법원',
  jeonju: '전주지방법원',
  cheongju: '청주지방법원',
}

// 사건 상태
export type CaseStatus =
  | 'document_preparation'
  | 'application_submitted'
  | 'under_review'
  | 'approved'
  | 'rejected'
  | 'completed'

export const CASE_STATUS_NAMES: Record<CaseStatus, string> = {
  document_preparation: '서류 준비',
  application_submitted: '신청 완료',
  under_review: '심사 중',
  approved: '인가',
  rejected: '기각',
  completed: '완료',
}

// 사건
export interface Case {
  id: number
  client_id: number
  court_type: CourtType
  case_number?: string
  status: CaseStatus
  memo?: string
  created_at: string
  client?: Client
  required_documents?: RequiredDocument[]
  documents?: Document[]
}

// 서류 상태
export type DocumentStatus = 'not_started' | 'in_progress' | 'completed'

export const DOCUMENT_STATUS_NAMES: Record<DocumentStatus, string> = {
  not_started: '미시작',
  in_progress: '진행중',
  completed: '완료',
}

// 필수 서류
export interface RequiredDocument {
  id: number
  case_id: number
  document_type: string
  document_name: string
  is_required: boolean
  status: DocumentStatus
  document_id?: number
  issue_url?: string
  auto_available: boolean
}

// 발급 서류
export interface Document {
  id: number
  case_id: number
  document_type: string
  file_path: string
  file_name: string
  file_size: number
  mime_type: string
  api_source: string
  issued_at: string
}

// 페이지네이션 응답
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}
