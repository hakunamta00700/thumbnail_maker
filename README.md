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

## 사용 방법

uv를 사용하여 설치:

```bash
uv sync
```

또는 직접 실행:

```bash
uv run python -m thumbnail_maker
```

### 1. GUI 사용 (추천)

```bash
uv run thumbnail-gui
```

PySide6 기반 GUI에서 썸네일을 생성할 수 있습니다.

### 2. CLI 사용

#### 기본 사용
```bash
uv run generate-thumbnail
```

#### DSL 파일 지정
```bash
uv run generate-thumbnail mydsl.json -o output.png
```

#### 간편 CLI (genthumb)
```bash
# 기본
uv run genthumb

# 제목/부제목 덮어쓰기
uv run genthumb --title "새 제목" --subtitle "새 부제목"

# 배경 이미지 설정
uv run genthumb --bgImg bg.png

# 출력 파일 지정
uv run genthumb -o result.png
```

## 파일 구조

```
thumbnail_maker/
├── requirements.txt           # Python 패키지 의존성
├── thumbnailRenderer.py      # 핵심 렌더링 로직
├── generateThumbnail.py      # 메인 생성 스크립트
├── genthumb.py              # 간편 CLI 스크립트
├── main_gui.py              # PySide6 GUI 애플리케이션
└── thumbnail.json           # DSL 예제 파일
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

## 기타

- JavaScript 버전의 파일들은 유지됩니다.
- 기존 DSL 파일과 호환됩니다.
- 폰트는 `fonts/` 디렉토리에 저장됩니다.

