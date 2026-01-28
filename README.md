# 개인회생 서류 관리 시스템

개인회생 신청에 필요한 서류를 자동으로 발급하고 관리하는 웹 애플리케이션입니다.

## 주요 기능

- **의뢰인 관리**: 의뢰인 정보 등록/수정/삭제
- **사건 관리**: 개인회생 사건 생성 및 진행 상태 관리
- **서류 관리**: 필수 서류 체크리스트 및 업로드
- **법원별 지원**: 대구, 부산, 대전, 전주, 청주 지방법원 지원
- **API 연동**: Hyphen API를 통한 서류 자동 발급 (예정)

## 기술 스택

### 백엔드
- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 (async)
- SQLite (개발) / PostgreSQL (운영)
- JWT 인증

### 프론트엔드
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Zustand (상태 관리)
- Axios

## 프로젝트 구조

\`\`\`
personal-rehabilitation-docs/
├── backend/                    # FastAPI 백엔드
│   ├── app/
│   │   ├── api/               # API 라우터
│   │   │   ├── auth.py        # 인증 API
│   │   │   ├── clients.py     # 의뢰인 API
│   │   │   ├── cases.py       # 사건 API
│   │   │   └── documents.py   # 서류 API
│   │   ├── core/              # 핵심 설정
│   │   │   ├── config.py      # 환경 설정
│   │   │   ├── database.py    # DB 연결
│   │   │   └── security.py    # 인증/보안
│   │   ├── models/            # SQLAlchemy 모델
│   │   ├── schemas/           # Pydantic 스키마
│   │   ├── services/          # 비즈니스 로직
│   │   └── main.py            # FastAPI 앱
│   ├── init_db.py             # DB 초기화 스크립트
│   └── requirements.txt
│
├── frontend/                   # Next.js 프론트엔드
│   ├── app/                   # App Router
│   │   ├── login/             # 로그인 페이지
│   │   └── dashboard/         # 대시보드
│   ├── components/            # React 컴포넌트
│   ├── lib/                   # 유틸리티
│   │   ├── api.ts             # API 클라이언트
│   │   └── store/             # Zustand 스토어
│   └── package.json
│
└── README.md
\`\`\`

## 설치 및 실행

### 백엔드

\`\`\`bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate    # Linux/Mac

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정 (.env 파일 생성)
cp .env.example .env
# .env 파일 수정

# 데이터베이스 초기화
python init_db.py

# 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

### 프론트엔드

\`\`\`bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
\`\`\`

## API 문서

서버 실행 후 아래 URL에서 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 기본 계정

\`\`\`
이메일: admin@example.com
비밀번호: admin123
\`\`\`

## API 엔드포인트

### 인증 (Auth)
- \`POST /api/v1/auth/login\` - 로그인
- \`POST /api/v1/auth/register\` - 회원가입
- \`GET /api/v1/auth/me\` - 현재 사용자 정보

### 의뢰인 (Clients)
- \`GET /api/v1/clients/\` - 의뢰인 목록
- \`POST /api/v1/clients/\` - 의뢰인 등록
- \`GET /api/v1/clients/{id}\` - 의뢰인 상세
- \`PUT /api/v1/clients/{id}\` - 의뢰인 수정
- \`DELETE /api/v1/clients/{id}\` - 의뢰인 삭제

### 사건 (Cases)
- \`GET /api/v1/cases/\` - 사건 목록
- \`POST /api/v1/cases/\` - 사건 생성
- \`GET /api/v1/cases/{id}\` - 사건 상세
- \`PUT /api/v1/cases/{id}\` - 사건 수정
- \`DELETE /api/v1/cases/{id}\` - 사건 삭제
- \`GET /api/v1/cases/{id}/documents/status\` - 서류 진행 현황

### 서류 (Documents)
- \`GET /api/v1/documents/types\` - 서류 유형 목록
- \`GET /api/v1/documents/case/{case_id}\` - 사건별 필수 서류
- \`POST /api/v1/documents/upload/{case_id}\` - 서류 업로드
- \`GET /api/v1/documents/{id}\` - 서류 상세
- \`DELETE /api/v1/documents/{id}\` - 서류 삭제

## 지원 법원

| 코드 | 법원명 |
|------|--------|
| daegu | 대구지방법원 |
| busan | 부산회생법원 |
| daejeon | 대전지방법원 |
| jeonju | 전주지방법원 |
| cheongju | 청주지방법원 |

## 환경 변수

\`\`\`env
# 앱 설정
APP_NAME=개인회생 서류 관리 시스템
DEBUG=true

# 데이터베이스
DATABASE_URL=sqlite+aiosqlite:///./rehabilitation_docs.db

# JWT 인증
SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Hyphen API (서류 자동 발급용)
HYPHEN_API_KEY=your-hyphen-api-key
HYPHEN_CLIENT_ID=your-client-id
HYPHEN_EKEY=your-encryption-key

# 암호화
ENCRYPTION_KEY=your-encryption-key-32-bytes-long
\`\`\`

## 라이선스

MIT License
