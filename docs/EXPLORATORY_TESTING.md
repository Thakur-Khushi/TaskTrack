# Exploratory Testing Report – TaskTrack

Exploratory testing means designing tests, running them and learning about the application at the same time, without a fixed script. It finds bugs that nobody thought to write a test case for. This session used **session-based test management (SBTM)**: time-boxed sessions, each guided by a *charter*.

| Item | Detail |
|---|---|
| Builds explored | v1.0 and v1.1 (fixes retested on v1.2) |
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
| EXP-01 | Search wildcard characters are not escaped. In v1.0 `*`/`?` (SQL GLOB) match everything; in v1.1 `%`/`_` (SQL LIKE) match everything | FUN | S3 Minor | P2 | v1.0, v1.1 | **Fixed in v1.2** – TC-22 |
| EXP-02 | Dashboard and task data are visible with the browser Back button after logout (no `Cache-Control: no-store`) | SES / SEC | S2 Major | P1 | v1.0, v1.1 | **Fixed in v1.2** – TC-23 |
| EXP-03 | `POST /__reset` test endpoint is reachable by anyone and deletes all data | SEC | S1 Critical | P1 | v1.0, v1.1 | **Fixed in v1.2** – TC-25 |
| EXP-04 | Past due dates accepted | VAL | S4 Trivial | P3 | v1.0, v1.1 | **Fixed in v1.2** – TC-24 |
| EXP-05 | Duplicate task titles allowed | USA | S4 Trivial | P3 | v1.0, v1.1 | Deferred (enhancement) |

### Security findings (follow-up review)
CH-6 (URL tampering) led to a closer look at how requests and sessions are protected. Three more defects were logged. Each was reproduced with a plain HTTP request outside the browser, then turned into an automated test.

| ID | Title | Category | Severity | Priority | Build | Status |
|---|---|---|---|---|---|---|
| SEC-01 | No CSRF protection: a POST without any token (e.g. from another website, carrying the user's session cookie) adds or deletes tasks | SEC | S2 Major | P1 | v1.0, v1.1 | **Fixed in v1.2** – TC-26 |
| SEC-02 | Logout is a GET link, so any page can log the user out (e.g. `<img src="/logout">`) | SEC | S3 Minor | P2 | v1.0, v1.1 | **Fixed in v1.2** – TC-27 |
| SEC-03 | Session signing key is hard-coded in the source; anyone with the code can forge a session cookie for any user | SEC | S1 Critical | P1 | v1.0, v1.1 | **Fixed in v1.2** – code review |

### Notable learning
**EXP-01 is a regression caused by a bug fix.** BUG-02 (case-sensitive search) was fixed in v1.1 by switching from `GLOB` to `LIKE`. That changed *which* characters act as wildcards, but did not remove the problem. The scripted test TC-18 only checked letter case, so it passed. Only exploratory testing caught the side effect. It was then turned into the automated regression test **TC-22**, so it will be checked on every future build.

### Fixes (build v1.2)
* EXP-01 – `%`, `_` and `\` are escaped and the query uses `LIKE ? ESCAPE '\'`.
* EXP-02 – responses for logged-in pages send `Cache-Control: no-store`, `Pragma: no-cache` and `Expires: 0`.
* EXP-03 – `/__reset` is registered only when the app starts with `TESTING=1` (the pytest fixture sets it).
* EXP-04 – a due date before today is rejected with "Due date cannot be in the past."
* SEC-01 – Flask-WTF `CSRFProtect`; every POST form carries a hidden `csrf_token`. A POST without it gets 400.
* SEC-02 – logout is a POST form (styled like the old link); `GET /logout` returns 405.
* SEC-03 – the key is read from the `SECRET_KEY` environment variable, with a random key generated at start-up for local development.

Search `app/app.py` for `EXP-0` and `SEC-0` to see each fix. All of them apply only to v1.2, so v1.0 and v1.1 still reproduce the original defects.

## How to repeat the session
```
python app/app.py                                  # start the app on :5000 (v1.2: set TESTING=1)
python tests/exploratory/explore_probe.py          # prints observations per charter
```
Then explore further by hand in the browser, using the charters above as a starting point.
