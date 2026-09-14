import 'package:flutter_test/flutter_test.dart';

import '../lib/zyra_service.dart';

void main() {
  test('connection status keeps reachability separate from readiness', () {
    const status = ZyraConnectionStatus(ZyraConnectionState.reachable);
    expect(status.state, ZyraConnectionState.reachable);
    expect(status.ready, isFalse);
  });

  test('ready status is explicitly authenticated and ready', () {
    const status = ZyraConnectionStatus(
      ZyraConnectionState.ready,
      ready: true,
      detail: 'Windows agent is authenticated and ready.',
    );
    expect(status.state, ZyraConnectionState.ready);
    expect(status.ready, isTrue);
  });
}
