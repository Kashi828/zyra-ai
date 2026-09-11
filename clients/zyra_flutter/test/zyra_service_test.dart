import 'package:flutter_test/flutter_test.dart';
import 'package:zyra_flutter/zyra_service.dart';

void main() {
  test('session inventory parses active and inactive sessions', () {
    final inventory = ZyraSessionInventory.fromJson({
      'device': {
        'device_id': 'phone-1',
        'capabilities': ['session:list'],
        'revoked': false,
        'created_at': 123,
      },
      'summary': {'total': 2, 'active': 1, 'inactive': 1},
      'sessions': [
        {
          'session_id': 'session-current',
          'device_id': 'phone-1',
          'active': true,
          'revoked': false,
          'current': true,
          'expires_at': 456,
        },
        {
          'session_id': 'session-old',
          'device_id': 'phone-1',
          'active': false,
          'revoked': true,
          'current': false,
          'expires_at': 100,
        },
      ],
    });

    expect(inventory.device.deviceId, 'phone-1');
    expect(inventory.summary.total, 2);
    expect(inventory.summary.active, 1);
    expect(inventory.summary.inactive, 1);
    expect(inventory.sessions, hasLength(2));
    expect(inventory.sessions.first.current, isTrue);
    expect(inventory.sessions.last.revoked, isTrue);
  });

  test('session credentials never add a device secret', () {
    final json = const ZyraSessionCredentials(
      deviceId: 'phone-1',
      sessionId: 'session-1',
    ).toJson();

    expect(json, {'device_id': 'phone-1', 'session_id': 'session-1'});
    expect(json.containsKey('device_secret'), isFalse);
  });
}
