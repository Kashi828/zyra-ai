import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

import '../lib/connection_diagnostics.dart';
import '../lib/connection_retry.dart';

void main() {
  test('diagnostics reports an unreachable endpoint without credentials', () async {
    const diagnostics = ZyraConnectionDiagnostics(
      retry: ZyraConnectionRetry(maxAttempts: 1, baseDelay: Duration.zero),
    );
    final result = await diagnostics.probe(Uri.parse('http://127.0.0.1:1/health'));
    expect(result.reachable, isFalse);
    expect(result.reason, anyOf('network_unreachable', 'timeout', 'probe_failed'));
  });

  test('diagnostics retries transient socket failures through the retry policy', () async {
    const retry = ZyraConnectionRetry(maxAttempts: 2, baseDelay: Duration.zero);
    var attempts = 0;
    final value = await retry.run(() async {
      attempts++;
      if (attempts == 1) throw const SocketException('temporary LAN failure');
      return true;
    });
    expect(value, isTrue);
    expect(attempts, 2);
  });
}
