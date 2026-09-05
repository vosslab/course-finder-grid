# News

## v26.09 - Unreleased

### Highlights

- The email scheduler now uses the native `CourseFinderMailer` helper for
  bounded Mail delivery and explicit macOS authorization.
- Startup verifies that the daemon can deliver email before it begins recurring
  reports, and the normal `cfmail` tmux session is easy to find and attach.

### Upgrade notes

- If macOS asks, allow `CourseFinderMailer` to automate Mail before relying on
  scheduled reports.
