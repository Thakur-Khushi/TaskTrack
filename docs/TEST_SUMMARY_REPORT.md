# Test Summary Report – TaskTrack

| Item | Detail |
|---|---|
| Builds tested | v1.0 (initial), v1.1 (bug-fix release) and v1.2 (exploratory + security fixes) |
| Environment | Windows 11, Python 3.8.6, Flask 3.0.3, Flask-WTF 1.2.1, SQLite, Chrome 158 (headless). The same suite also runs in CI (GitHub Actions, Ubuntu, Python 3.11) |
| Tools | Selenium WebDriver 4.27.1 + pytest 8.3.5 + pytest-html 4.1.1; Selenium IDE project via selenium-side-runner 4 |
| Detailed reports | `reports/report_v1.0.html`, `reports/report_v1.1.html`, `reports/report_v1.2.html` (open in a browser; failed tests include a screenshot), `reports/junit_v1.*.xml`, `reports/selenium_ide_results_v1.*.txt` |

## 1. Execution summary – Selenium WebDriver (30 test runs)

| Build | Total | Passed | Failed | Known-open (xfail) | Pass rate* |
|---|---|---|---|---|---|
| v1.0 | 30 | 19 | **4** | 7 | 82.6 % |
| v1.1 | 30 | 23 | **0** | 7 | 100 % |
| v1.2 | 30 | 30 | **0** | 0 | 100 % |

\*Pass rate = passed ÷ (passed + failed); known-open defects are reported separately.
(TC-22 runs once for each of 4 wildcard characters, so there are 27 test cases but 30 runs.)

The 7 known-open runs on v1.0 and v1.1 are TC-22 (2 of its 4 wildcard runs), TC-23, TC-24, TC-25, TC-26 and TC-27. They are marked `xfail(strict=True)` on those builds. On v1.2 the same tests run without the marker and all pass, which confirms the fixes. Because of `strict=True`, an unexpected pass (XPASS) on v1.0/v1.1 would have failed the run, so none occurred.

## 2. Execution summary – Selenium IDE (6 tests)

| Build | Passed | Failed |
|---|---|---|
| v1.0 | 2 | 4 (IDE-03, 04, 05, 06) |
| v1.1 | 6 | 0 |
| v1.2 | 6 | 0 |

Both tools found the same 4 defects on v1.0, and both confirm the fixes on v1.1. On v1.2 the recorded IDE tests still pass unchanged, including the logout step (now a POST form button instead of a link).

## 3. Defects found by scripted tests

| Bug ID | Summary | Category | Severity | Priority | Found by | v1.0 | v1.1 (retest) | v1.2 (retest) |
|---|---|---|---|---|---|---|---|---|
| BUG-01 | A title made only of spaces creates a blank task | VAL | S3 Minor | P2 | TC-11, IDE-05 | Fail | **Closed** | Pass |
| BUG-02 | Search is case-sensitive ("homework" does not find "Homework") | FUN | S2 Major | P1 | TC-18, IDE-04 | Fail | **Closed** | Pass |
| BUG-03 | "Pending" counter shows the total instead of total − completed | LOG | S2 Major | P1 | TC-16, IDE-03 | Fail | **Closed** | Pass |
| BUG-04 | Password shorter than 6 characters is accepted although the UI says min 6 | SEC | S2 Major | P1 | TC-04, IDE-06 | Fail | **Closed** | Pass |

Sample failure messages from the v1.0 report:
* TC-04 – `AssertionError: weak password was accepted`
* TC-11 – `AssertionError: a blank task was created`
* TC-16 – `assert 3 == 2` (pending)
* IDE-03 – `waitForText id=count-pending 0` timed out (value stayed 1)

## 4. Defects found by exploratory testing and security review
See [EXPLORATORY_TESTING.md](EXPLORATORY_TESTING.md).

| ID | Summary | Severity | Test | v1.0 | v1.1 | v1.2 |
|---|---|---|---|---|---|---|
| EXP-01 | Search wildcards not escaped | S3 | TC-22 | Open (xfail) | Open (xfail) | **Fixed** |
| EXP-02 | Dashboard visible with Back after logout | S2 | TC-23 | Open (xfail) | Open (xfail) | **Fixed** |
| EXP-03 | `/__reset` reachable on the live server | S1 | TC-25 | Open (xfail) | Open (xfail) | **Fixed** |
| EXP-04 | Past due dates accepted | S4 | TC-24 | Open (xfail) | Open (xfail) | **Fixed** |
| EXP-05 | Duplicate task titles allowed | S4 | – | Deferred | Deferred | Deferred |
| SEC-01 | No CSRF protection | S2 | TC-26 | Open (xfail) | Open (xfail) | **Fixed** |
| SEC-02 | Logout via GET | S3 | TC-27 | Open (xfail) | Open (xfail) | **Fixed** |
| SEC-03 | Hard-coded session secret key | S1 | code review | Open | Open | **Fixed** |

SEC-03 has no automated test: the key is internal to the server and is not visible through the UI or HTTP. The fix (key from the `SECRET_KEY` environment variable, random fallback) was verified by code review.

## 5. Defect distribution (all 12 defects)

| Category | Count | | Severity | Count |
|---|---|---|---|---|
| Functional (FUN) | 2 | | S1 Critical | 2 |
| Validation (VAL) | 2 | | S2 Major | 5 |
| Logic (LOG) | 1 | | S3 Minor | 3 |
| Security (SEC) | 5 | | S4 Trivial | 2 |
| Session (SES) | 1 | | | |
| Usability (USA) | 1 | | | |

(EXP-02 is counted under Session.)

## 6. Conclusion
* All 4 defects reported on v1.0 are fixed and verified in v1.1, and none of the 19 previously passing tests regressed.
* Exploratory testing found 5 more issues, including a regression *introduced* by the BUG-02 fix (EXP-01) that the scripted tests had missed. A follow-up security review added SEC-01 … SEC-03.
* v1.2 fixes EXP-01 … EXP-04 and SEC-01 … SEC-03. All 30 WebDriver runs and all 6 IDE tests pass on v1.2, and none of the 23 tests that passed on v1.1 regressed.
* **Recommendation:** v1.2 meets the exit criteria (no open S1 defects; every S2 defect fixed). Only EXP-05 (S4, enhancement) remains, deferred. v1.2 can be released, provided `SECRET_KEY` is set on the server and `TESTING` is not.
