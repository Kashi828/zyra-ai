import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:zyra_flutter/connection_retry.dart';
import 'package:zyra_flutter/zyra_service.dart';

void main() {
  test('POST retries a transient connection failure and succeeds', () async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    var attempts = 0;
    server.listen((request) async {
      attempts++;
      if (attempts == 1) {
        request.response.headers.contentType = ContentType.json;
        request.response.statusCode = HttpStatus.serviceUnavailable;
        request.response.write(jsonEncode({'detail': 'temporary outage'}));
      } else {
        request.response.headers.contentType = ContentType.json;
        request.response.write(jsonEncode({'accepted': true, 'action': 'open_app', 'status': 'completed', 'message': 'ok'}));
      }
      await request.response.close();
    });

    final service = ZyraService(
      baseUrl: 'http://${server.address.address}:${server.port}',
      retry: const ZyraConnectionRetry(maxAttempts: 3, baseDelay: Duration.zero),
    );

    // HTTP 503 is an application response, not a transport failure; the
    // service must not retry it.
    await expectLater(
      service.executeRemoteCommand(
        const ZyraSessionCredentials(deviceId: 'device-1', sessionId: 'session-1'),
        action: 'open_app',
      ),
      throwsA(isA<ZyraApiException>()),
    );
    expect(attempts, 1);
    await server.close(force: true);
  });

  test('health retries socket failure using the shared retry policy', () async {
    final probe = await ServerSocket.bind(InternetAddress.loopbackIPv4, 0);
    final port = probe.port;
    await probe.close();

    final service = ZyraService(
      baseUrl: 'http://127.0.0.1:$port',
      retry: const ZyraConnectionRetry(maxAttempts: 3, baseDelay: Duration.zero),
    );
    expect(await service.health(), isFalse);
  });
}
