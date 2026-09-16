import 'package:flutter_test/flutter_test.dart';

import '../lib/connection_diagnostics.dart';
import '../lib/connection_explanation.dart';
import '../lib/connection_target.dart';
import '../lib/zyra_service.dart';

void main() {
  const target = ZyraConnectionTarget(
    uri: Uri.parse('http://192.168.1.20:8000'),
    source: ZyraConnectionTargetSource.explicit,
  );

  test('explains network failure as a host connectivity problem', () {
    final explanation = ZyraConnectionExplanation.fromStatus(
      status: const ZyraConnectionStatus(ZyraConnectionState.offline),
      target: target,
      probe: const ZyraTransportProbe(
        reachable: false,
        latency: Duration(milliseconds: 20),
        reason: 'network_unreachable',
      ),
    );

    expect(explanation.title, 'Windows host unreachable');
    expect(explanation.message, contains('could not be reached'));
  });

  test('explains server errors without calling the network path offline', () {
    final explanation = ZyraConnectionExplanation.fromStatus(
      status: const ZyraConnectionStatus(ZyraConnectionState.error),
      target: target,
      probe: const ZyraTransportProbe(
        reachable: false,
        latency: Duration(milliseconds: 30),
        statusCode: 503,
      ),
    );

    expect(explanation.title, 'Windows API error');
    expect(explanation.message, contains('HTTP 503'));
    expect(explanation.message, contains('network path is reachable'));
  });

  test('explains an authenticated but incomplete session', () {
    final explanation = ZyraConnectionExplanation.fromStatus(
      status: const ZyraConnectionStatus(
        ZyraConnectionState.authenticated,
        detail: 'Missing Windows capabilities: windows.browser',
      ),
      target: target,
    );

    expect(explanation.title, 'Session needs attention');
    expect(explanation.message, contains('windows.browser'));
  });

  test('explains ready state as actionable', () {
    final explanation = ZyraConnectionExplanation.fromStatus(
      status: const ZyraConnectionStatus(ZyraConnectionState.ready, ready: true),
      target: target,
    );

    expect(explanation.title, 'Windows ready');
    expect(explanation.action, contains('Quick action'));
  });
}
