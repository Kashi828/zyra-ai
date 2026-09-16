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
    expect(result.serverError, isFalse);
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

  test('HTTP 5xx is classified as a reachable server error', () async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    server.listen((request) {
      request.response.statusCode = HttpStatus.internalServerError;
      request.response.close();
    });
    addTearDown(server.close);

    const diagnostics = ZyraConnectionDiagnostics(
      retry: ZyraConnectionRetry(maxAttempts: 1, baseDelay: Duration.zero),
    );
    final result = await diagnostics.probe(
      Uri.parse('http://127.0.0.1:${server.port}/health'),
    );

    expect(result.reachable, isFalse);
    expect(result.serverError, isTrue);
    expect(result.statusCode, HttpStatus.internalServerError);
    expect(result.reason, 'server_error');
  });
}
