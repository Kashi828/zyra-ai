import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:zyra_flutter/session_context.dart';
import 'package:zyra_flutter/zyra_service.dart';

void main() {
  group('session models', () {
    test('session inventory parses active and inactive sessions', () {
      final inventory = ZyraSessionInventory.fromJson({
        'device': {'device_id': 'phone-1', 'capabilities': ['session:list'], 'revoked': false, 'created_at': 123},
        'summary': {'total': 2, 'active': 1, 'inactive': 1},
        'sessions': [
          {'session_id': 'session-current', 'device_id': 'phone-1', 'active': true, 'revoked': false, 'current': true, 'expires_at': 456},
          {'session_id': 'session-old', 'device_id': 'phone-1', 'active': false, 'revoked': true, 'current': false, 'expires_at': 100},
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
      final json = const ZyraSessionCredentials(deviceId: 'phone-1', sessionId: 'session-1').toJson();
      expect(json, {'device_id': 'phone-1', 'session_id': 'session-1'});
      expect(json.containsKey('device_secret'), isFalse);
    });
  });

  group('session context', () {
    test('keeps identifiers in memory and exposes credentials', () {
      final context = ZyraSessionContext();
      context.setCredentials(deviceId: ' device-1 ', sessionId: ' session-1 ');
      expect(context.configured, isTrue);
      expect(context.deviceId, 'device-1');
      expect(context.sessionId, 'session-1');
      expect(context.credentials?.toJson(), {'device_id': 'device-1', 'session_id': 'session-1'});
      context.clear();
      expect(context.configured, isFalse);
      expect(context.credentials, isNull);
    });
  });

  group('authenticated command bridge', () {
    test('serializes authenticated command request and parses result', () async {
      final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      final service = ZyraService(baseUrl: 'http://${server.address.address}:${server.port}');
      final responseFuture = service.executeRemoteCommand(const ZyraSessionCredentials(deviceId: 'device-123', sessionId: 'session-456'), action: 'open_app', payload: {'name': 'calculator'}, commandId: 'test-command-1');
      final request = await server.first;
      final body = jsonDecode(await utf8.decoder.bind(request).join()) as Map<String, dynamic>;
      expect(request.method, 'POST');
      expect(request.uri.path, '/v1/remote/commands');
      expect(body['device_id'], 'device-123');
      expect(body['session_id'], 'session-456');
      expect(body['action'], 'open_app');
      expect(body['payload'], {'name': 'calculator'});
      expect(body['command_id'], 'test-command-1');
      request.response.headers.contentType = ContentType.json;
      request.response.write(jsonEncode({'accepted': true, 'action': 'open_app', 'status': 'completed', 'message': 'Opened calculator'}));
      await request.response.close();
      final result = await responseFuture;
      expect(result.success, isTrue);
      expect(result.action, 'open_app');
      expect(result.status, 'completed');
      expect(result.message, 'Opened calculator');
      await server.close(force: true);
    });

    test('surfaces protected API errors', () async {
      final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      final service = ZyraService(baseUrl: 'http://${server.address.address}:${server.port}');
      final responseFuture = service.executeRemoteCommand(const ZyraSessionCredentials(deviceId: 'device-123', sessionId: 'session-456'), action: 'open_app', payload: {'name': 'calculator'});
      final request = await server.first;
      request.response.statusCode = HttpStatus.forbidden;
      request.response.headers.contentType = ContentType.json;
      request.response.write(jsonEncode({'detail': 'session is not authorized'}));
      await request.response.close();

      ZyraApiException? error;
      try {
        await responseFuture;
        fail('Expected a ZyraApiException');
      } on ZyraApiException catch (caught) {
        error = caught;
      }
      expect(error, isNotNull);
      expect(error!.statusCode, HttpStatus.forbidden);
      expect(error.message, 'session is not authorized');
      await server.close(force: true);
    });
  });
}
