# Development Toolchain

이 문서는 Python 버전, 패키지 관리, 정적 검사, pre-commit, 환경 변수 분리 기준을 정의한다.

## 1. Python 버전

- 고정 버전: `Python 3.12`
- 기준 파일:
  - `.python-version`
  - `pyproject.toml`

## 2. 패키지/가상환경 전략

- 가상환경: `.venv/`
- 기본 패키지 관리자: `pip`
- 생성 예:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -U pip
```

## 3. 정적 검사 기준

- linter: `ruff`
- formatter: `black`
- type checker: `mypy`

도구 설정은 `pyproject.toml`에 모은다.

## 4. pre-commit

- 파일: `.pre-commit-config.yaml`
- 기본 hook:
  - trailing whitespace
  - end-of-file-fixer
  - mixed line ending
  - `ruff`
  - `black`
  - `mypy`

## 5. 환경 변수 분리

- local: `.env`
- dev: `.env.dev.example`
- staging: `.env.staging.example`
- prod: `.env.prod.example`

실제 값은 커밋하지 않는다. 예시 파일에는 key 이름과 placeholder만 둔다.
