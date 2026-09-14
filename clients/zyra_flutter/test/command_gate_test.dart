import 'package:flutter_test/flutter_test.dart';
import 'package:zyra_flutter/zyra_service.dart';

void main() {
  group('Flutter command readiness gate', () {
    test('only Ready permits protected commands', () {
      const states = [
        ZyraConnectionState.offline,
        ZyraConnectionState.reachable,
        ZyraConnectionState.authenticated,
        ZyraConnectionState.error,
      ];

      for (final state in states) {
        final status = ZyraConnectionStatus(state);
        expect(status.isReady, isFalse);
      }

      final ready = ZyraConnectionStatus.fromJson({
        'state': 'ready',
        'device_id': 'windows-1',
        'session_id': 'session-1',
        'session_active': true,
        'device_revoked': false,
        'capabilities': [
          'windows.apps',
          'windows.files.read',
          'windows.browser',
        ],
      });
      expect(ready.isReady, isTrue);
    });

    test('missing capability blocks readiness', () {
      final status = ZyraConnectionStatus.fromJson({
        'state': 'ready',
        'session_active': true,
        'device_revoked': false,
        'capabilities': ['windows.apps', 'windows.browser'],
      });
      expect(status.state, ZyraConnectionState.authenticated);
      expect(status.isReady, isFalse);
    });

    test('revoked device and inactive session block readiness', () {
      for (final json in [
        {
          'state': 'ready',
          'session_active': true,
          'device_revoked': true,
          'capabilities': ['windows.apps', 'windows.files.read', 'windows.browser'],
        },
        {
          'state': 'ready',
          'session_active': false,
          'device_revoked': false,
          'capabilities': ['windows.apps', 'windows.files.read', 'windows.browser'],
        },
      ]) {
        final status = ZyraConnectionStatus.fromJson(json);
        expect(status.isReady, isFalse);
      }
    });
  });
}
