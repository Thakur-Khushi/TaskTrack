# Exploratory Testing Report – TaskTrack

Exploratory testing means designing tests, running them and learning about the application at the same time, without a fixed script. It finds bugs that nobody thought to write a test case for. This session used **session-based test management (SBTM)**: time-boxed sessions, each guided by a *charter*.

| Item | Detail |
|---|---|
| Builds explored | v1.0 and v1.1 |
| Session length | 1 session × 45 min |
| Browser | Chrome (headless and headed) |
| Aids | `tests/exploratory/explore_probe.py` drives the steps and prints observations; screenshots in `reports/exploratory/` |
| Heuristics | Boundaries, special characters ("SFDPOT", "Goldilocks": too big, too small, just right), navigation/back button, URL tampering, duplicates, Unicode |

## Charters and observations

| Charter | Mission | Observation | Verdict |
|---|---|---|---|
| CH-1 | Explore search with special characters `% _ * ? [` | v1.0: `*` and `?` return **every** task. v1.1: `%` and `_` return **every** task | **Bug EXP-01** |
| CH-2 | Explore due-date values | A due date of 2001-01-01 (in the past) is accepted without a warning | **Bug EXP-04** |
| CH-3 | Explore duplicates and double submission | The same title can be added twice; no warning | **EXP-05** (usability) |
| CH-4 | Explore Unicode input | Hindi + emoji title "होमवर्क पूरा करो ✅" is stored, shown and searched correctly | OK |
| CH-5 | Explore navigation after logout | After logout, pressing **Back** shows the dashboard with the task list (served from the browser cache). Refresh then redirects to login | **Bug EXP-02** |
| CH-6 | Explore URL tampering | `GET /tasks/1/delete` → 405 (good). The `/__reset` test hook exists on the live server and wipes **all** users' data when it receives a POST | **Bug EXP-03** |
| CH-7 | Explore username edge cases | Leading/trailing spaces are trimmed ("␣␣spaced␣␣" → "spaced") | OK |

## Defects found by exploratory testing

| ID | Title | Category | Severity | Priority | Build | Status |
|---|---|---|---|---|---|---|
| EXP-01 | Search wildcard characters are not escaped. In v1.0 `*`/`?` (SQL GLOB) match everything; in v1.1 `%`/`_` (SQL LIKE) match everything | FUN | S3 Minor | P2 | v1.0, v1.1 | Open – TC-22 added |
| EXP-02 | Dashboard and task data are visible with the browser Back button after logout (no `Cache-Control: no-store`) | SES / SEC | S2 Major | P1 | v1.0, v1.1 | Open – TC-23 added |
| EXP-03 | `POST /__reset` test endpoint is reachable by anyone and deletes all data | SEC | S1 Critical | P1 | v1.0, v1.1 | Open – disable outside test mode |
| EXP-04 | Past due dates accepted | VAL | S4 Trivial | P3 | v1.0, v1.1 | Open |
| EXP-05 | Duplicate task titles allowed | USA | S4 Trivial | P3 | v1.0, v1.1 | Deferred (enhancement) |

### Notable learning
**EXP-01 is a regression caused by a bug fix.** BUG-02 (case-sensitive search) was fixed in v1.1 by switching from `GLOB` to `LIKE`. That changed *which* characters act as wildcards, but did not remove the problem. The scripted test TC-18 only checked letter case, so it passed. Only exploratory testing caught the side effect. It was then turned into the automated regression test **TC-22**, so it will be checked on every future build.

### Suggested fixes
* EXP-01 – escape `%`, `_` and `\` and use `LIKE ? ESCAPE '\'`.
* EXP-02 – add `Cache-Control: no-store` to responses for logged-in pages.
* EXP-03 – register `/__reset` only when `app.config["TESTING"]` is true.
* EXP-04 – validate `due_date >= today` (or show a warning).

## How to repeat the session
```
python app/app.py                                  # start the app on :5000
python tests/exploratory/explore_probe.py          # prints observations per charter
```
Then explore further by hand in the browser, using the charters above as a starting point.
