import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:zyra_flutter/connection_retry.dart';
import 'package:zyra_flutter/zyra_service.dart';

void main() {
  test('POST does not retry an HTTP application failure', () async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    var attempts = 0;
    server.listen((request) async {
      attempts++;
      request.response.headers.contentType = ContentType.json;
      request.response.statusCode = HttpStatus.serviceUnavailable;
      request.response.write(jsonEncode({'detail': 'temporary outage'}));
      await request.response.close();
    });

    final service = ZyraService(
      baseUrl: 'http://${server.address.address}:${server.port}',
      retry: const ZyraConnectionRetry(maxAttempts: 3, baseDelay: Duration.zero),
    );

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

  test('health uses the shared retry policy for unreachable targets', () async {
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
