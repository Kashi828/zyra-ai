import 'package:flutter_test/flutter_test.dart';

import '../lib/connection_target.dart';

void main() {
  test('uses explicit private endpoint when configured', () {
    final target = ZyraConnectionTarget.resolve(configuredUrl: 'http://192.168.1.20:8000/');
    expect(target.uri.toString(), 'http://192.168.1.20:8000/');
    expect(target.source, ZyraConnectionTargetSource.explicit);
    expect(target.isExplicit, isTrue);
  });

  test('keeps emulator bridge target explicit and identifiable', () {
    final target = ZyraConnectionTarget.resolve();
    if (target.source == ZyraConnectionTargetSource.androidEmulatorBridge) {
      expect(target.uri.host, '10.0.2.2');
      expect(target.isAndroidEmulatorBridge, isTrue);
    }
  });

  test('rejects public configured endpoints during beta resolution', () {
    expect(
      () => ZyraConnectionTarget.resolve(configuredUrl: 'https://example.com/api'),
      throwsA(isA<ArgumentError>()),
    );
  });
}
