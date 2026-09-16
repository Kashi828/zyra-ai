import 'connection_diagnostics.dart';
import 'connection_target.dart';
import 'zyra_service.dart';

/// Converts transport/session state into concise, actionable beta guidance.
/// This layer contains no credentials and is safe to surface in the UI.
class ZyraConnectionExplanation {
  const ZyraConnectionExplanation({required this.title, required this.message, required this.action});

  final String title;
  final String message;
  final String action;

  factory ZyraConnectionExplanation.fromStatus({
    required ZyraConnectionStatus status,
    required ZyraConnectionTarget target,
    ZyraTransportProbe? probe,
  }) {
    // A response proves the transport path is reachable, even when the API
    // itself reports a server-side failure. Check the status code before the
    // generic unreachable branch so 5xx responses are explained correctly.
    if (probe?.statusCode != null && probe!.statusCode! >= 500) {
      return ZyraConnectionExplanation(
        title: 'Windows API error',
        message: 'The Windows API responded with HTTP ${probe.statusCode}. The network path is reachable.',
        action: 'Check the Windows API service logs and retry.',
      );
    }

    if (probe != null && !probe.reachable) {
      final reason = switch (probe.reason) {
        'timeout' => 'The Windows host did not respond before the timeout.',
        'network_unreachable' => 'The Windows host could not be reached over the current network.',
        _ => 'The connection test could not reach the Windows API.',
      };
      return ZyraConnectionExplanation(
        title: 'Windows host unreachable',
        message: '$reason Target: ${target.uri.host}:${target.uri.port}.',
        action: target.isAndroidEmulatorBridge
            ? 'Start the Windows API and verify the emulator bridge is available.'
            : 'Start the Windows API and verify the phone and PC are on the same network.',
      );
    }

    return switch (status.state) {
      ZyraConnectionState.offline => const ZyraConnectionExplanation(
          title: 'Windows offline',
          message: 'No response was received from the configured Windows endpoint.',
          action: 'Check the endpoint and local network connection.',
        ),
      ZyraConnectionState.reachable => ZyraConnectionExplanation(
          title: 'Authentication required',
          message: status.detail.isEmpty ? 'Windows is reachable, but an authenticated session is not ready.' : status.detail,
          action: 'Configure a current device ID and session ID.',
        ),
      ZyraConnectionState.authenticated => ZyraConnectionExplanation(
          title: 'Session needs attention',
          message: status.detail.isEmpty ? 'The session is authenticated but the Windows command bridge is not ready.' : status.detail,
          action: 'Refresh the session or update the Windows device capabilities.',
        ),
      ZyraConnectionState.ready => const ZyraConnectionExplanation(
          title: 'Windows ready',
          message: 'The authenticated Windows command bridge is ready for allowlisted actions.',
          action: 'Run a Quick action to verify end-to-end control.',
        ),
      ZyraConnectionState.error => ZyraConnectionExplanation(
          title: 'Connection error',
          message: status.detail.isEmpty ? 'ZYRA could not determine the Windows connection state.' : status.detail,
          action: 'Run the connection test and inspect the API response.',
        ),
    };
  }
}
