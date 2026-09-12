import 'package:flutter/foundation.dart';

import 'zyra_service.dart';

/// Holds only the identifiers needed to authorize the current client session.
/// The context lives for the app process and is intentionally not persisted.
class ZyraSessionContext extends ChangeNotifier {
  String _deviceId = '';
  String _sessionId = '';

  String get deviceId => _deviceId;
  String get sessionId => _sessionId;
  bool get configured => _deviceId.isNotEmpty && _sessionId.isNotEmpty;

  ZyraSessionCredentials? get credentials => configured
      ? ZyraSessionCredentials(deviceId: _deviceId, sessionId: _sessionId)
      : null;

  void setCredentials({required String deviceId, required String sessionId}) {
    final nextDevice = deviceId.trim();
    final nextSession = sessionId.trim();
    if (_deviceId == nextDevice && _sessionId == nextSession) return;
    _deviceId = nextDevice;
    _sessionId = nextSession;
    notifyListeners();
  }

  void clear() {
    if (!configured) return;
    _deviceId = '';
    _sessionId = '';
    notifyListeners();
  }
}

/// App-process session context shared by Home and Devices.
/// It is memory-only and is never written to disk.
final zyraSessionContext = ZyraSessionContext();
