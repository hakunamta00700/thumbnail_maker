# 썸네일 생성기 (Python)

JavaScript 기반 썸네일 생성기를 Python으로 변환한 프로젝트입니다.

## 주요 변경사항

- **Pillow**: 이미지 생성 라이브러리로 사용
- **PySide6**: GUI 프레임워크로 사용
- **Python**: 모든 코드를 Python으로 변환

## 설치 방법

```bash
pip install -r requirements.txt
```

또는 uv를 사용하여 설치:

```bash
uv sync
```

## 사용 방법

### 1. GUI 사용 (추천)

GUI 모드로 실행하면 시각적으로 썸네일을 생성하고 편집할 수 있습니다.

```bash
thumbnail_maker gui
```

또는

```bash
uv run python -m thumbnail_maker gui
```

#### GUI 기능

GUI는 다음과 같은 기능을 제공합니다:

**해상도 설정**
- 크기 모드: Preset, Fixed Ratio, Custom
- 종횡비: 16:9, 9:16, 4:3, 1:1
- 너비/높이: 직접 입력 가능

**배경 설정**
- 배경 타입: 단색(Solid), 그라디언트(Gradient), 이미지(Image)
- 색상 선택: 색상 피커로 선택
- 이미지 설정: 로컬 이미지 파일 선택
- 투명도: 슬라이더로 조절 (0-100%)
- 블러 효과: 슬라이더로 조절 (0-20)

**제목 설정**
- 텍스트 입력: 여러 줄 지원
- 위치: 9개 그리드 위치 (tl, tc, tr, ml, mc, mr, bl, bc, br)
- 폰트: 웹 폰트 URL 또는 로컬 폰트 파일
- 폰트 설정: 이름, 굵기(normal/bold), 스타일(normal/italic)
- 폰트 크기: 8-200px
- 색상: 색상 피커로 선택
- 외곽선: 사용 여부 및 두께 설정
- 단어 단위 줄바꿈: 체크박스로 활성화/비활성화

**부제목 설정**
- 표시 여부: 체크박스로 제어
- 텍스트 입력: 여러 줄 지원
- 위치: 9개 그리드 위치
- 폰트 설정: 제목과 동일한 옵션 제공
- 단어 단위 줄바꿈: 체크박스로 활성화/비활성화

**저장 및 내보내기**
- 미리보기 생성: 실시간 미리보기
- 썸네일 저장: PNG 파일로 저장
- DSL 저장: JSON 형식의 DSL 파일로 저장
- 패키지 저장(.thl): 템플릿과 폰트를 포함한 패키지로 저장
- 패키지 로드(.thl): 저장된 템플릿 불러오기

### 2. CLI 사용

CLI는 두 가지 모드를 제공합니다: `generate-thumbnail` (전체 옵션)과 `genthumb` (간편 모드).

#### 2.1 generate-thumbnail 명령어

GUI에서 설정 가능한 모든 옵션을 CLI 파라미터로 제공합니다.

**기본 사용**
```bash
thumbnail_maker generate-thumbnail
```

**DSL 파일 지정**
```bash
thumbnail_maker generate-thumbnail mydsl.json -o output.png
```

**템플릿 파일(.thl) 사용**
```bash
thumbnail_maker generate-thumbnail template.thl -o output.png
```

**해상도 설정**
```bash
# Preset 모드
thumbnail_maker generate-thumbnail -rm preset -ar 16:9

# Fixed Ratio 모드
thumbnail_maker generate-thumbnail -rm fixedRatio -ar 4:3 -w 800

# Custom 모드
thumbnail_maker generate-thumbnail -rm custom -w 1920 -h 1080
```

**배경 설정**
```bash
# 단색 배경
thumbnail_maker generate-thumbnail -bt solid -bc "#ff0000"

# 그라디언트 배경
thumbnail_maker generate-thumbnail -bt gradient -bc "#00ff00"

# 이미지 배경
thumbnail_maker generate-thumbnail -bt image -bi bg.png -bo 80 -bb 5
```

**제목 설정**
```bash
thumbnail_maker generate-thumbnail \
  -tt "제목 텍스트" \
  -tp mc \
  -tfn "SBAggroB" \
  -tfu "https://example.com/font.woff" \
  -tfw bold \
  -tfs normal \
  -tfsz 64 \
  -tc "#ff0000" \
  -to \
  -tot 5 \
  -tww
```

**부제목 설정**
```bash
thumbnail_maker generate-thumbnail \
  -sv \
  -st "부제목 텍스트" \
  -sp bl \
  -sfn "SBAggroB" \
  -sfu "https://example.com/font.woff" \
  -sfw normal \
  -sfs italic \
  -sfsz 32 \
  -sc "#00ff00" \
  -sww
```

**업로드 기능**
```bash
thumbnail_maker generate-thumbnail -u -o output.png
```

**전체 옵션 예제**
```bash
thumbnail_maker generate-thumbnail template.thl \
  -o result.png \
  -rm custom -w 1920 -h 1080 \
  -bt image -bi background.jpg -bo 90 -bb 3 \
  -tt "메인 제목" -tp tl -tfsz 72 -tc "#ffffff" -to -tot 7 \
  -sv -st "서브 제목" -sp bl -sfsz 36 -sc "#cccccc" \
  -u
```

#### 2.2 genthumb 명령어 (간편 모드)

템플릿 파일을 사용하여 빠르게 썸네일을 생성하는 간편 모드입니다.

**기본 사용**
```bash
thumbnail_maker genthumb
```

**템플릿 파일 지정**
```bash
thumbnail_maker genthumb --template template.thl
```

**제목/부제목 덮어쓰기**
```bash
thumbnail_maker genthumb --template template.thl -t "새 제목" --subtitle "새 부제목"
```

**배경 이미지 변경**
```bash
thumbnail_maker genthumb --template template.thl -b bg.png
```

**출력 파일 지정**
```bash
thumbnail_maker genthumb --template template.thl -o result.png
```

**업로드까지 자동 처리**
```bash
thumbnail_maker genthumb --template template.thl -t "제목" -u
```

**전체 예제**
```bash
thumbnail_maker genthumb --template mytemplate.thl \
  -t "동영상 제목" \
  --subtitle "2024년 1월 1일" \
  -b background.jpg \
  -o thumbnail.png \
  -u
```

#### 2.3 upload 명령어

이미지 파일을 업로드하고 URL을 받습니다.

```bash
thumbnail_maker upload image.png
```

## CLI 파라미터 참조

### generate-thumbnail 파라미터

#### 해상도 관련
- `-rm, --resolution-mode`: 해상도 모드 (preset/fixedRatio/custom)
- `-ar, --aspect-ratio`: 종횡비 (16:9/9:16/4:3/1:1)
- `-w, --width`: 너비 (픽셀)
- `-h, --height`: 높이 (픽셀)

#### 배경 관련
- `-bt, --background-type`: 배경 타입 (solid/gradient/image)
- `-bc, --background-color`: 배경 색상 (hex 코드, 예: #ff0000)
- `-bi, --background-image`: 배경 이미지 경로
- `-bo, --background-opacity`: 배경 투명도 (0-100)
- `-bb, --background-blur`: 배경 블러 (0-20)

#### 제목 관련
- `-tt, --title-text`: 제목 텍스트
- `-tp, --title-position`: 제목 위치 (tl/tc/tr/ml/mc/mr/bl/bc/br)
- `-tfn, --title-font-name`: 제목 폰트 이름
- `-tfu, --title-font-url`: 제목 폰트 URL
- `-tff, --title-font-file`: 제목 로컬 폰트 파일 경로
- `-tfw, --title-font-weight`: 제목 폰트 굵기 (normal/bold)
- `-tfs, --title-font-style`: 제목 폰트 스타일 (normal/italic)
- `-tfsz, --title-font-size`: 제목 폰트 크기
- `-tc, --title-color`: 제목 색상 (hex 코드)
- `-to, --title-outline`: 제목 외곽선 사용 (플래그)
- `-tot, --title-outline-thickness`: 제목 외곽선 두께
- `-tww, --title-word-wrap`: 제목 단어 단위 줄바꿈 (플래그)

#### 부제목 관련
- `-sv, --subtitle-visible`: 부제목 표시 (플래그)
- `-st, --subtitle-text`: 부제목 텍스트
- `-sp, --subtitle-position`: 부제목 위치 (tl/tc/tr/ml/mc/mr/bl/bc/br)
- `-sfn, --subtitle-font-name`: 부제목 폰트 이름
- `-sfu, --subtitle-font-url`: 부제목 폰트 URL
- `-sff, --subtitle-font-file`: 부제목 로컬 폰트 파일 경로
- `-sfw, --subtitle-font-weight`: 부제목 폰트 굵기 (normal/bold)
- `-sfs, --subtitle-font-style`: 부제목 폰트 스타일 (normal/italic)
- `-sfsz, --subtitle-font-size`: 부제목 폰트 크기
- `-sc, --subtitle-color`: 부제목 색상 (hex 코드)
- `-sww, --subtitle-word-wrap`: 부제목 단어 단위 줄바꿈 (플래그)

#### 공통 옵션
- `-o, --output`: 출력 파일 경로 (기본값: thumbnail.png)
- `-u, --upload`: 생성 후 자동 업로드 (플래그)

### genthumb 파라미터

- `--template`: 템플릿 파일 경로 (.thl 파일)
- `-t, --title`: 제목 덮어쓰기 (\\n 또는 실제 줄바꿈 지원)
- `--subtitle`: 부제목 덮어쓰기 (\\n 또는 실제 줄바꿈 지원)
- `-b, --background-image`: 배경 이미지 경로
- `-o, --output`: 출력 파일 경로 (기본값: thumbnail.png)
- `-u, --upload`: 생성 후 자동 업로드 (플래그)

## 파일 구조

```
thumbnail_maker/
├── thumbnail_maker/
│   ├── __main__.py          # CLI 진입점
│   ├── cli.py               # CLI 로직
│   ├── renderer.py          # 핵심 렌더링 로직
│   ├── upload.py            # 이미지 업로드 기능
│   └── gui/                 # GUI 모듈
│       ├── main_window.py   # 메인 윈도우
│       ├── widgets.py        # 위젯 팩토리
│       ├── handlers.py       # 이벤트 핸들러
│       └── dsl_manager.py    # DSL 관리
├── tests/                   # 테스트 코드
│   └── test_generate_thumbnail.py
├── fonts/                   # 폰트 파일 저장소
├── requirements.txt         # Python 패키지 의존성
├── pytest.ini              # pytest 설정
└── thumbnail.json          # DSL 예제 파일
```

## DSL 파일 형식

```json
{
  "Thumbnail": {
    "Resolution": {
      "type": "preset",
      "value": "16:9"
    },
    "Background": {
      "type": "solid",
      "color": "#a3e635"
    },
    "Texts": [
      {
        "type": "title",
        "content": "제목 텍스트",
        "gridPosition": "tl",
        "font": {
          "name": "SBAggroB",
          "faces": [...]
        },
        "fontSize": 48,
        "color": "#4ade80",
        "outline": {
          "thickness": 7,
          "color": "#000000"
        },
        "enabled": true
      }
    ]
  }
}
```

## 해상도 설정

### Preset 모드
```json
{
  "type": "preset",
  "value": "16:9"  // "16:9", "9:16", "4:3", "1:1"
}
```

### Fixed Ratio 모드
```json
{
  "type": "fixedRatio",
  "ratioValue": "16:9",
  "width": 480  // 또는 height 지정
}
```

### Custom 모드
```json
{
  "type": "custom",
  "width": 480,
  "height": 270
}
```

## 테스트

프로젝트에는 pytest를 사용한 테스트 코드가 포함되어 있습니다.

```bash
# 모든 테스트 실행
pytest

# 특정 테스트 실행
pytest tests/test_generate_thumbnail.py

# 상세 출력
pytest -v
```

테스트는 다음을 포함합니다:
- 해상도 파라미터 테스트
- 배경 파라미터 테스트
- 제목 파라미터 테스트
- 부제목 파라미터 테스트
- 파라미터 조합 테스트
- 통합 테스트

## 위치 그리드 시스템

텍스트 위치는 9개 그리드 시스템을 사용합니다:

```
tl  tc  tr
ml  mc  mr
bl  bc  br
```

- `tl`: Top Left (상단 왼쪽)
- `tc`: Top Center (상단 중앙)
- `tr`: Top Right (상단 오른쪽)
- `ml`: Middle Left (중앙 왼쪽)
- `mc`: Middle Center (중앙 중앙)
- `mr`: Middle Right (중앙 오른쪽)
- `bl`: Bottom Left (하단 왼쪽)
- `bc`: Bottom Center (하단 중앙)
- `br`: Bottom Right (하단 오른쪽)

## 템플릿 파일 (.thl)

`.thl` 파일은 썸네일 템플릿을 패키지로 묶은 ZIP 파일입니다. 다음을 포함합니다:
- `thumbnail.json`: DSL 설정 파일
- `fonts/`: 사용된 폰트 파일들

템플릿 파일을 사용하면 설정과 폰트를 함께 공유할 수 있습니다.

## 기타

- JavaScript 버전의 파일들은 유지됩니다.
- 기존 DSL 파일과 호환됩니다.
- 폰트는 `fonts/` 디렉토리에 자동으로 다운로드 및 저장됩니다.
- 웹 폰트(WOFF, WOFF2)는 자동으로 TTF로 변환됩니다.

