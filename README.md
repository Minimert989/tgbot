# Telegram PDF Downloader

이 프로젝트는 지정한 텔레그램 채널 또는 그룹에서 PDF 파일을 자동으로 다운로드하는 **GUI 앱**입니다.

## 기능
- 채널 ID 또는 @username 기반 다운로드
- 다운로드 진행률 표시
- 이미 다운로드한 파일은 건너뜀
- `.env`로 API 자격증명 저장 가능

---

## 1. Telegram API 자격증명 얻는 방법

1. [my.telegram.org](https://my.telegram.org) 접속
2. 텔레그램 계정으로 로그인 (전화번호 → 인증코드)
3. **API development tools** 메뉴 클릭
4. **App title**, **Short name** 아무거나 입력 후 생성
5. 생성된 **API_ID**와 **API_HASH**를 복사
6. `.env` 파일에 저장

7. ---

## 2. Channel ID / @username 찾는 방법

### @username
- 공개 채널: `@채널이름` 형태 사용
- 예시: `@openai_news`

### 숫자 Channel ID
- 비공개 채널 또는 @username 없는 경우
1. [@userinfobot](https://t.me/userinfobot) 에게 채널 초대 후 `/start` 입력
2. 봇이 보내주는 `ID` 확인
3. 이 값을 **음수**까지 포함해 입력 (`-1001234567890` 형식)

---

## 3. 실행 방법
	1.	API_ID, API_HASH 입력
	•	.env가 있으면 자동 로드
	2.	Channel ID/@username 입력
	3.	Download Dir에서 저장 위치 선택
	4.	Start 버튼 클릭
	5.	첫 실행 시:
	•	전화번호 입력
	•	텔레그램 앱 인증코드 입력
	•	2단계 비밀번호(있을 경우) 입력
