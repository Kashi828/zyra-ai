import 'dart:async';
import 'dart:io';

import 'connection_retry.dart';

/// Platform-neutral diagnostics for the beta connection layer.
/// It deliberately reports only transport-level facts and never exposes credentials.
class ZyraConnectionDiagnostics {
  const ZyraConnectionDiagnostics({this.retry = const ZyraConnectionRetry()});

  final ZyraConnectionRetry retry;

  Future<ZyraTransportProbe> probe(Uri endpoint) async {
    final started = DateTime.now();
    try {
      final statusCode = await retry.run(() async {
        final client = HttpClient()..connectionTimeout = const Duration(seconds: 3);
        try {
          final request = await client.getUrl(endpoint).timeout(const Duration(seconds: 4));
          request.headers.set(HttpHeaders.acceptHeader, 'application/json');
          final response = await request.close().timeout(const Duration(seconds: 5));
          await response.drain<void>();
          return response.statusCode;
        } finally {
          client.close(force: true);
        }
      });
      return ZyraTransportProbe(
        reachable: statusCode >= 200 && statusCode < 500,
        statusCode: statusCode,
        latency: DateTime.now().difference(started),
      );
    } on TimeoutException {
      return ZyraTransportProbe(reachable: false, latency: DateTime.now().difference(started), reason: 'timeout');
    } on SocketException {
      return ZyraTransportProbe(reachable: false, latency: DateTime.now().difference(started), reason: 'network_unreachable');
    } catch (_) {
      return ZyraTransportProbe(reachable: false, latency: DateTime.now().difference(started), reason: 'probe_failed');
    }
  }
}

class ZyraTransportProbe {
  const ZyraTransportProbe({required this.reachable, required this.latency, this.statusCode, this.reason});

  final bool reachable;
  final Duration latency;
  final int? statusCode;
  final String? reason;
}
