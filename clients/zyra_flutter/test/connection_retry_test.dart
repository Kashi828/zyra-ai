import 'dart:async';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

import '../lib/connection_retry.dart';

void main() {
  test('uses bounded exponential backoff', () {
    const retry = ZyraConnectionRetry();
    expect(retry.delayForAttempt(0), Duration.zero);
    expect(retry.delayForAttempt(1), const Duration(milliseconds: 350));
    expect(retry.delayForAttempt(2), const Duration(milliseconds: 700));
    expect(retry.delayForAttempt(3), const Duration(seconds: 1, milliseconds: 400));
    expect(retry.delayForAttempt(4), const Duration(seconds: 2));
    expect(retry.delayForAttempt(8), const Duration(seconds: 2));
  });

  test('retries transient socket failures and succeeds', () async {
    const retry = ZyraConnectionRetry(baseDelay: Duration.zero);
    var attempts = 0;
    final result = await retry.run(() async {
      attempts++;
      if (attempts < 3) throw const SocketException('LAN unavailable');
      return 'connected';
    });
    expect(result, 'connected');
    expect(attempts, 3);
  });

  test('does not retry non-transient errors by default', () async {
    const retry = ZyraConnectionRetry(baseDelay: Duration.zero);
    var attempts = 0;
    await expectLater(
      retry.run(() async {
        attempts++;
        throw const FormatException('invalid response');
      }),
      throwsA(isA<FormatException>()),
    );
    expect(attempts, 1);
  });

  test('supports an explicit retry predicate', () async {
    const retry = ZyraConnectionRetry(baseDelay: Duration.zero);
    var attempts = 0;
    final result = await retry.run(() async {
      attempts++;
      if (attempts < 2) throw const FormatException('temporary protocol issue');
      return true;
    }, shouldRetry: (error) => error is FormatException);
    expect(result, isTrue);
    expect(attempts, 2);
  });

  test('retries timeout failures', () async {
    const retry = ZyraConnectionRetry(baseDelay: Duration.zero);
    var attempts = 0;
    await retry.run(() async {
      attempts++;
      if (attempts < 2) throw TimeoutException('timed out');
      return null;
    });
    expect(attempts, 2);
  });
}
