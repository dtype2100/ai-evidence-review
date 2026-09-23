# Real-case admission gate

No real case is admitted yet. The illustrative demo is not portfolio performance evidence.

`cases/urllib3-fingerprint-5211` is a public-source candidate, not an admitted result. Its fixed local check reproduces `binascii.Error` from an isolated pre-fix function excerpt; local stand-ins replace package imports, so this is not a full urllib3 package run. A Claude-produced finding is recorded, but it was informed by the included failing test and is not a blind-detection measurement. The owner has not directly reviewed the claim and explicitly left its verdict `unresolved`; this is not a valid or invalid adjudication.

Upstream context: [issue #5211](https://github.com/urllib3/urllib3/issues/5211), [fix PR #5212](https://github.com/urllib3/urllib3/pull/5212), [pre-fix source](https://github.com/urllib3/urllib3/blob/7a802a49bb7880624b5fa0053dd7cc77b94966c2/src/urllib3/util/ssl_.py#L107-L138), and [fix commit](https://github.com/urllib3/urllib3/commit/46ab811ed595633c2c4dfdf08bc71088dbd543de). The `real` case type means publicly sourced, not admitted or human-confirmed. `evaluate` counts the candidate as one real case but reports zero adjudicated findings and `precision: null`; do not use `case_count` as an admitted-case count.

A case enters this directory only after recording the public source URL, exact pre-fix revision, license and permission to redistribute the included code, a fixed local reproduction through `review.py check`, its observed `check.json`, agent-produced findings, and an independent human verdict. Reports must name the number of real cases and adjudicated findings; unresolved findings stay visible but out of the precision denominator.

If no case clears this gate, do not present a measured accuracy or impact claim. Publication and final submission remain owner decisions.
