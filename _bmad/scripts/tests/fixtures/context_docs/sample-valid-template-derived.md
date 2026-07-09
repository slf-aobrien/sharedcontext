---
title: Session Token Lifecycle
domain: user-authentication
description: Describes how session tokens are issued, refreshed, and invalidated in the authentication service.
keywords:
  - session-token
  - authentication
  - token-lifecycle
created: 2026-07-08T00:00:00Z
updated: 2026-07-08T00:00:00Z
validated-by: aaron
validated-on: null
status: draft
---

# Session Token Lifecycle

## Summary

This document describes how session tokens are issued at login, transparently refreshed during
an active session, and explicitly invalidated on logout or security events.

## Details

### Token Issuance

A session token is issued when a user successfully completes primary authentication.  The token
is a signed opaque identifier stored server-side and delivered to the client via an HTTP-only
secure cookie.

### Token Refresh

Tokens are refreshed automatically on each authenticated request within the active window.
Idle sessions beyond the configured timeout are invalidated server-side and the next request
triggers a re-authentication challenge.

### Token Invalidation

Tokens are invalidated:

- On explicit logout by the user.
- On password change or security-policy reset.
- On detection of concurrent sessions that exceed the per-account limit.
- On administrator-initiated session termination.
