# Test Plan – TaskTrack Web Application

| Item | Detail |
|---|---|
| Project | TaskTrack – a small web-based task manager (Mini Project, LP-IV) |
| Document | Test Plan v1.0 |
| Builds under test | v1.0 (initial release), v1.1 (bug-fix release) and v1.2 (exploratory + security fixes) |
| Test types | Functional, regression, smoke, exploratory, basic security |
| Tools | Selenium WebDriver 4 (Python), Selenium IDE, pytest, pytest-html |

---

## 1. Objective
Verify that TaskTrack's features work as specified. Find and classify defects. Confirm through regression testing that the fixes in v1.1 and v1.2 do not break features that already worked.

## 2. System environment / platform

| Layer | Selection | Reason |
|---|---|---|
| OS | Windows 11 | Developer machine |
| Language (server) | Python 3.8 | Simple, widely taught |
| Web framework | Flask 3.0 | Lightweight; built-in dev server |
| Database | SQLite 3 | File-based; no installation needed |
| Front end | HTML5, CSS3, Jinja2 templates, JavaScript | Standard web stack |
| Browsers | Google Chrome (primary), Microsoft Edge | Cross-browser check |
| Automation | Selenium WebDriver 4.27 + pytest 8 | Industry-standard UI automation |
| Record/playback | Selenium IDE (browser extension) / selenium-side-runner | Quick, codeless tests |
| Reporting | pytest-html, JUnit XML | Readable HTML report + CI-friendly XML |

## 3. Scope

### 3.1 Features to be tested

| ID | Feature | Description |
|---|---|---|
| F1 | Registration | Create an account with username, password and confirm password. Rules: password ≥ 6 characters, passwords match, username unique |
| F2 | Login / Logout | Authenticate with credentials; session handling; protected pages redirect to login |
| F3 | Add task | Title (required, ≤ 100 chars), priority (Low/Medium/High), optional due date |
| F4 | Complete task | Toggle a task between pending and completed |
| F5 | Delete task | Delete with a confirmation dialog (OK / Cancel) |
| F6 | Search | Find tasks by keyword, case-insensitively |
| F7 | Summary counters | Total, Completed and Pending counts |
| F8 | Security / privacy | Users see only their own tasks; HTML input is escaped (XSS) |

### 3.2 Features not to be tested
Performance/load testing, mobile browsers, password reset (not implemented), and deployment on a production WSGI server.

## 4. Test approach

| Level / type | How | Tool |
|---|---|---|
| Smoke | 3 critical-path tests (`-m smoke`) on every build | WebDriver + pytest |
| Functional + regression | 27 automated test cases (30 runs) covering F1–F8, run on v1.0, v1.1 and v1.2; also in CI on every push | WebDriver + pytest (Page Object Model) |
| Record & playback | 6 recorded scenarios | Selenium IDE (`TaskTrack.side`) |
| Exploratory | Session-based, time-boxed (charters CH-1…CH-7) | Manual, plus `explore_probe.py` helper |
| Cross-browser | Smoke suite with `--browser edge` | WebDriver |

Techniques used for test design: equivalence partitioning (valid/invalid passwords), boundary values (title length 100/150, password length 3 vs 6), negative testing (wrong password, empty title), and state transitions (pending ↔ completed, logged in → logged out).

## 5. Test cases

| TC | Feature | Test case | Expected result | Type |
|---|---|---|---|---|
| TC-01 | F1 | Register with valid data | Redirect to login, success message | Smoke |
| TC-02 | F1 | Register with an existing username | "Username already exists" | Negative |
| TC-03 | F1 | Passwords do not match | "Passwords do not match" | Negative |
| TC-04 | F1 | Password of 3 characters | Rejected: "at least 6 characters" | Boundary |
| TC-05 | F2 | Login with valid credentials | Dashboard opens, username shown | Smoke |
| TC-06 | F2 | Login with wrong password | "Invalid username or password" | Negative |
| TC-07 | F2 | Logout | Login page; /tasks no longer reachable | Functional |
| TC-08 | F2 | Open /tasks without login | Redirect to login | Security |
| TC-09 | F3 | Add task with priority and due date | Row shows title, priority, date | Smoke |
| TC-10 | F3 | Empty title | Browser blocks the submit (HTML5 `required`) | Negative |
| TC-11 | F3 | Title of only spaces | Rejected: "Task title is required" | Negative |
| TC-12 | F3 | 150-character title | Only 100 characters accepted | Boundary |
| TC-13 | F4 | Toggle complete, then toggle again | Struck through, then normal | State |
| TC-14 | F5 | Delete → OK | Task removed | Functional |
| TC-15 | F5 | Delete → Cancel | Task kept | Functional |
| TC-16 | F7 | 3 tasks, 1 completed | Total 3, Completed 1, Pending 2 | Functional |
| TC-17 | F6 | Search "Homework" | Matching task only | Functional |
| TC-18 | F6 | Search "homework" (lowercase) | Still finds "Maths Homework" | Functional |
| TC-19 | F6 | Search with no match | "No tasks found." | Negative |
| TC-20 | F8 | Title `<script>alert(1)</script>` | Shown as plain text | Security |
| TC-21 | F8 | Second user logs in | Does not see the first user's tasks | Security |
| TC-22 | F6 | Search `%`, `_`, `*`, `?` | Treated literally (no match) | Added from exploratory |
| TC-23 | F2 | Browser Back after logout | Dashboard not shown | Added from exploratory |
| TC-24 | F3 | Add task with due date 2001-01-01 | Rejected: "Due date cannot be in the past." | Added from exploratory (EXP-04) |
| TC-25 | F8 | Start a second server without `TESTING=1`; `POST /__reset` | 404 – hook not available | Added from exploratory (EXP-03) |
| TC-26 | F8 | Raw HTTP `POST /tasks/add` with the session cookie but no CSRF token | 400; no task created | Security (SEC-01) |
| TC-27 | F2 | `GET /logout` (raw request and in the browser) | 405; user stays logged in | Security (SEC-02) |

TC-22 … TC-27 reproduce defects that are open in v1.0/v1.1. They are marked `xfail(strict=True)` on those builds and run as normal tests on v1.2.

## 6. Bug taxonomy

Every defect is classified on three axes: **category** (what kind of fault), **severity** (impact on the user), and **priority** (how soon to fix).

### 6.1 Defect categories

| Code | Category | Meaning | Example in TaskTrack |
|---|---|---|---|
| FUN | Functional | Feature does not do what the requirement says | Search is case-sensitive (BUG-02) |
| VAL | Input validation | Bad input is accepted, or good input is rejected | Whitespace title accepted (BUG-01), past due date (EXP-04) |
| LOG | Logic / calculation | Wrong computation or business rule | Pending counter wrong (BUG-03) |
| SEC | Security | Authentication, authorization, data exposure | Weak password accepted (BUG-04), unprotected reset hook (EXP-03), no CSRF protection (SEC-01) |
| SES | Session / state | Problems with login state, caching, navigation | Back button after logout (EXP-02) |
| UI | User interface / cosmetic | Layout, labels, text, alignment | – |
| USA | Usability | Works, but confusing or inconvenient | Duplicate titles allowed (EXP-05) |
| CMP | Compatibility | Browser- or OS-specific behaviour | – |
| PER | Performance | Slow response, timeouts | – |

### 6.2 Severity

| Level | Definition |
|---|---|
| S1 – Critical | Data loss, security breach, or the application is unusable; no workaround |
| S2 – Major | An important feature is broken or gives wrong results; a workaround may exist |
| S3 – Minor | Limited impact; the feature mostly works |
| S4 – Trivial | Cosmetic issue or suggestion |

### 6.3 Priority
**P1** fix before release · **P2** fix in the next build · **P3** fix when time permits.

### 6.4 Defect life cycle
New → Assigned → Open → Fixed → **Retest (regression)** → Closed. A failed retest goes back to Reopened. Other end states are Deferred, Rejected and Duplicate.

## 7. Entry and exit criteria
**Entry:** the build is deployed and starts; the smoke tests pass; test data can be reset.
**Exit:** all planned test cases have been executed; no open S1 defects; every S2 defect is fixed or deferred with a reason; reports are generated.

## 8. Deliverables
Test plan (this document) · automated scripts (`tests/`) · Selenium IDE project (`selenium-ide/TaskTrack.side`) · HTML/XML reports (`reports/`) · exploratory session report · test summary report.

## 9. Risks
Flaky UI tests caused by timing (mitigated with explicit waits); browser/driver version mismatch (mitigated by Selenium Manager); browser popups such as Chrome's password manager (disabled in the test browser options).
