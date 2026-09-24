#set page(
  paper: "a4",
  margin: (x: 19mm, y: 17mm),
  footer: context align(right)[
    #text(size: 7.5pt, fill: rgb("#657487"))[AI Evidence Review · 2026-09-24 · #counter(page).display()]
  ],
)
#set text(font: "Apple SD Gothic Neo", size: 9.5pt, fill: rgb("#172B40"))
#set par(leading: 0.74em)
#set heading(numbering: none)
#show heading.where(level: 1): it => {
  v(10pt)
  text(size: 13pt, weight: "bold", fill: rgb("#123D57"))[#it.body]
  v(3pt)
}

#let ink = rgb("#123D57")
#let teal = rgb("#167D82")
#let pale = rgb("#EAF4F3")
#let gray = rgb("#5D6E7E")

#text(size: 8pt, weight: "bold", fill: teal)[SK hynix AI Hackathon 2026 · Portfolio draft]
#v(8pt)
#text(size: 25pt, weight: "bold", fill: ink)[AI Evidence Review]
#v(3pt)
#text(size: 11pt, fill: gray)[AI 코드 리뷰의 주장, 관찰, 사람 판정을 분리하는 작은 검증 도구]
#v(13pt)
#block(width: 100%, fill: pale, inset: 11pt, radius: 5pt)[
  *핵심 질문*  AI가 발견했다고 말한 문제가 실제로 재현되는가? 그 관찰만으로 주장이 확정되는가?
  이 도구는 답을 서두르지 않고 근거를 서로 다른 칸에 남긴다.
]

= 문제와 해결

AI 리뷰 문장은 그럴듯하지만, 소스 위치가 틀리거나 테스트 결과와 인적 판단이 섞이면 검토자는 무엇을 믿어야 하는지 알기 어렵다. 저는 코드 리뷰를 자동 승인하는 대신, 제안에서 증거 카드까지 이어지는 최소한의 검증 경로를 만들었다.

#table(
  columns: (18%, 40%, 42%),
  inset: 6pt,
  stroke: (bottom: 0.4pt + rgb("#D8E2E8")),
  table.header([*단계*], [*기록*], [*검증·운영 규칙*]),
  [사례 선정], [`case.json`, 공개 출처·수정 전 리비전·라이선스], [사람이 출처·공개 권한을 확인],
  [AI 주장], [`findings.json`, 경로·줄·검증 제안], [스키마·경로·실제 줄 검사],
  [관찰], [`check.json`, 고정된 `unittest` 결과], [입력 JSON의 명령 실행 금지, 시간 제한, 변경 감지],
  [사람 판정], [`verdicts.json`, 유효·무효·미결], [사람에게 판정을 요청하고 미검토는 미결로 둠],
  [집계], [`report.md`와 `evaluate`], [미결은 정확도 분모에서 제외],
)

= 구현과 검증

Python 표준 라이브러리만 쓰는 CLI와 얇은 에이전트 스킬로 구현했다. 모델 API, 서버, DB, 자동 수정·PR 발행 기능은 넣지 않았다. Codex는 CLI·회귀 테스트 작성, Gemini와 BrowserOS Neo는 공개 사례·출처 조사, Claude는 독립 코드 감사와 후보의 finding 작성, Copilot CLI는 Git 검사를 맡았다. *자동 테스트 27개 통과*; 이 중 한 테스트는 urllib3 후보의 체크가 의도대로 종료 코드 1과 `binascii.Error`를 기록함을 확인한다.

= 독립 감사에서 회귀 테스트까지

Claude의 별도 코드 감사를 그대로 채택하지 않고, 각 위험을 재현하는 실패 테스트를 먼저 만들었다. 이후 공통 입력 경계에서 수정하고 같은 테스트가 통과하는지 확인했다.

#table(
  columns: (36%, 64%),
  inset: 5pt,
  stroke: (bottom: 0.4pt + rgb("#D8E2E8")),
  [*확인된 실패 모드*], [*수정과 확인*],
  [AI 문장에 판정 제목 삽입], [줄바꿈을 평탄화해 가짜 `Human verdict` 헤더 차단],
  [수정된 사례에 오래된 체크 재사용], [사례 메타데이터·fixture 해시가 달라지면 보고 거부],
  [심볼릭 링크로 실행·출력 범위 이탈], [fixture 및 출력 경로 링크 거부],
  [같은 사례를 중복 집계], [중복 사례 ID 거부],
)

#pagebreak()

#text(size: 8pt, weight: "bold", fill: teal)[EVIDENCE CARD · PUBLIC-SOURCE CANDIDATE]
#v(7pt)
#text(size: 19pt, weight: "bold", fill: ink)[재현된 오류, 아직 미결인 주장]
#v(6pt)

공개 urllib3의 수정 전 `assert_fingerprint` 함수 전체를 분리해 테스트했다. 패키지 import는 로컬 대체 정의를 사용했으므로 *전체 urllib3 패키지 테스트는 아니다*. 길이는 맞지만 16진수가 아닌 지문(`"g" * 32`)을 넣으면, 기대한 `SSLError` 대신 `binascii.Error`가 발생한다.

#v(5pt)
#table(
  columns: (23%, 77%),
  inset: 7pt,
  stroke: (bottom: 0.4pt + rgb("#D8E2E8")),
  [*AI 주장*], [Claude는 비16진수 지문이 `unhexlify`에서 다른 예외로 빠져나간다고 제안했다. 모델은 이미 실패 테스트를 볼 수 있었으므로 독립 탐지 성능으로 해석하지 않는다.],
  [*관찰된 체크*], [고정 `unittest` 실행의 종료 코드 1. `source.py:46`에서 `binascii.Error: Non-hexadecimal digit found`가 발생했다.],
  [*사람 판정*], [작성자가 직접 검토하기 전이라 `unresolved`. 유효/무효로 세지 않는다.],
)

#v(10pt)
#block(width: 100%, fill: rgb("#F2F5F8"), inset: 10pt, radius: 5pt)[
  *현재 집계*  공개 출처 후보 1건(채택 사례 아님) · 체크 실패 1건 · 미결 1건 · 판정 표본 0건 · precision = `null`.
  이는 모델 정확도, 산업 현장 효과, 본선 진출 가능성을 측정한 수치가 아니다.
]

= 재현과 출처

저장소 루트에서 아래 명령을 실행한다. 첫 번째 명령(`check`)은 이 사례에서 실패 코드 1이 예상된다. `check.json`은 실행한 Python 경로와 `case.json`·fixture 해시에 묶이므로, 환경이나 사례가 바뀌면 `evaluate`가 기존 결과를 거부한다. 다시 체크한 뒤의 예상 집계는 `case_count` 1, `check_failed` 1, `unresolved` 1, `sample_size` 0, `precision` `null`이다. 여기서 `case_count`는 채택된 사례 수가 아니다.

```sh
python3 review.py check cases/urllib3-fingerprint-5211
python3 review.py evaluate cases/urllib3-fingerprint-5211
```

원본: #link("https://github.com/urllib3/urllib3/issues/5211")[urllib3 issue \#5211] · #link("https://github.com/urllib3/urllib3/pull/5212")[fix PR \#5212] · #link("https://github.com/urllib3/urllib3/blob/7a802a49bb7880624b5fa0053dd7cc77b94966c2/src/urllib3/util/ssl_.py#L107-L138")[수정 전 함수] · #link("https://github.com/urllib3/urllib3/commit/46ab811ed595633c2c4dfdf08bc71088dbd543de")[수정 커밋]. MIT 고지는 저장소의 `LICENSE.txt`에 보존했다.

= 다음 검증 관문

전체 패키지에서의 재현, 테스트를 보지 않은 독립 AI 탐지, 사람의 직접 판정, 사례 수·소요 시간 비교가 남아 있다. 이 관문 전에는 후보를 검증 완료 사례로 승격하거나 성능 수치를 제시하지 않는다. *이 문서는 제출 전 검토용 초안이며 자동 제출되지 않았다.*
