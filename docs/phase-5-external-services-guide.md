# Phase 5 External Services Guide (Mobile App)

This guide covers mobile runtime dependencies and service integration.

## API and WebSocket Endpoints
- Set `EXPO_PUBLIC_API_URL` to backend API base (`/api/v1`).
- Set `EXPO_PUBLIC_WS_URL` to backend websocket host.
- Enforce HTTPS in production.

## Token Storage and Security
- Store access/refresh tokens in Expo SecureStore only.
- Never store tokens in AsyncStorage.
- Implement logout on repeated 401 refresh failures.

## Push Notifications
- Register Expo push token at first launch.
- Send token to backend endpoint `/users/me/push-token`.
- Configure notification routing by type:
  - `trade_opened`
  - `trade_closed`
  - `bot_error`
  - `daily_summary`

## Mobile Build and Release
- Use EAS build profiles for `staging` and `production`.
- Keep API/WS URLs environment-specific.
- Validate deep-link navigation for notification taps.

## Observability
- Track app startup success rate.
- Track auth failure rates and refresh retry loops.
- Track websocket disconnect frequency.

## Incident Notes
- If users stop receiving live updates:
  1. Verify websocket auth token validity.
  2. Verify server room subscription events.
  3. Verify Redis pub/sub to socket gateway path.
