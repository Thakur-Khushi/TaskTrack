# Test Summary Report – TaskTrack

| Item | Detail |
|---|---|
| Builds tested | v1.0 (initial) and v1.1 (bug-fix release) |
| Environment | Windows 11, Python 3.8.6, Flask 3.0.3, SQLite, Chrome 157 (headless) |
| Tools | Selenium WebDriver 4.27.1 + pytest 8.3.5 + pytest-html 4.1.1; Selenium IDE project via selenium-side-runner 4 |
| Detailed reports | `reports/report_v1.0.html`, `reports/report_v1.1.html` (open in a browser; failed tests include a screenshot), `reports/junit_v1.*.xml`, `reports/selenium_ide_results_v1.*.txt` |

## 1. Execution summary – Selenium WebDriver (26 test runs)

| Build | Total | Passed | Failed | Known-open (xfail) | Pass rate* |
|---|---|---|---|---|---|
| v1.0 | 26 | 19 | **4** | 3 | 82.6 % |
| v1.1 | 26 | 23 | **0** | 3 | 100 % |

\*Pass rate = passed ÷ (passed + failed); known-open defects are reported separately.
(TC-22 runs once for each of 4 wildcard characters, so there are 23 test cases but 26 runs.)

## 2. Execution summary – Selenium IDE (6 tests)

| Build | Passed | Failed |
|---|---|---|
| v1.0 | 2 | 4 (IDE-03, 04, 05, 06) |
| v1.1 | 6 | 0 |

Both tools found the same 4 defects on v1.0, and both confirm the fixes on v1.1.

## 3. Defects found by scripted tests

| Bug ID | Summary | Category | Severity | Priority | Found by | v1.0 | v1.1 (retest) |
|---|---|---|---|---|---|---|---|
| BUG-01 | A title made only of spaces creates a blank task | VAL | S3 Minor | P2 | TC-11, IDE-05 | Fail | **Closed** |
| BUG-02 | Search is case-sensitive ("homework" does not find "Homework") | FUN | S2 Major | P1 | TC-18, IDE-04 | Fail | **Closed** |
| BUG-03 | "Pending" counter shows the total instead of total − completed | LOG | S2 Major | P1 | TC-16, IDE-03 | Fail | **Closed** |
| BUG-04 | Password shorter than 6 characters is accepted although the UI says min 6 | SEC | S2 Major | P1 | TC-04, IDE-06 | Fail | **Closed** |

Sample failure messages from the v1.0 report:
* TC-04 – `AssertionError: weak password was accepted`
* TC-11 – `AssertionError: a blank task was created`
* TC-16 – `assert 3 == 2` (pending)
* IDE-03 – `waitForText id=count-pending 0` timed out (value stayed 1)

## 4. Defects found by exploratory testing
See [EXPLORATORY_TESTING.md](EXPLORATORY_TESTING.md): **5 defects** (EXP-01 … EXP-05), including 1 critical (EXP-03, unprotected reset endpoint) and 1 major (EXP-02, cached dashboard after logout). EXP-01 and EXP-02 were converted into automated tests TC-22 and TC-23. These stay marked as known-open until they are fixed.

## 5. Defect distribution (all 9 defects)

| Category | Count | | Severity | Count |
|---|---|---|---|---|
| Functional (FUN) | 2 | | S1 Critical | 1 |
| Validation (VAL) | 2 | | S2 Major | 4 |
| Logic (LOG) | 1 | | S3 Minor | 2 |
| Security (SEC) | 2 | | S4 Trivial | 2 |
| Session (SES) | 1 | | | |
| Usability (USA) | 1 | | | |

(EXP-02 is counted under Session.)

## 6. Conclusion
* All 4 defects reported on v1.0 are fixed and verified in v1.1, and none of the 19 previously passing tests regressed.
* Exploratory testing found 5 more issues, including a regression *introduced* by the BUG-02 fix (EXP-01) that the scripted tests had missed.
* **Recommendation:** v1.1 is better than v1.0 but should **not** be released to production until EXP-03 (S1) and EXP-02 (S2) are fixed. The exit criterion "no open S1 defects" is not yet met.
