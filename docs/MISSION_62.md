# ZYRA AI — Mission 62
## API Authentication + Rate Limiting

Mission 62 adds a centralized API guard in front of protected remote commands.

### Checks
1. Request authentication context is present.
2. Sliding-window rate limit is enforced.
3. Device must exist and not be revoked.
4. Session must be durable, device-bound, unexpired and active.
5. Only then is the registered Windows action allowed to execute.

### Error contract
Protected API failures use HTTP 401/403/429 with a stable reason and
`Retry-After` on rate limiting.

### Local-first behavior
This protects remote command APIs without changing the existing public
onboarding/settings/runtime shell. Public remote exposure remains disabled by
default by the existing product configuration.
