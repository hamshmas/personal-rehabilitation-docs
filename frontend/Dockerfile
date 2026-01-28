FROM node:20-alpine

WORKDIR /app

# 패키지 파일 복사 및 설치
COPY package*.json ./
RUN npm install

# 소스 복사
COPY . .

EXPOSE 8080

CMD ["npm", "run", "dev", "--", "-p", "8080"]
