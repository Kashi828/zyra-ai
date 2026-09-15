import 'dart:io';

import 'endpoint_policy.dart';

/// Describes the API target selected for the current Flutter runtime.
/// Physical Android devices should use an explicit private-LAN URL; the
/// emulator keeps the Android loopback bridge target for local development.
class ZyraConnectionTarget {
  const ZyraConnectionTarget({required this.uri, required this.source});

  final Uri uri;
  final ZyraConnectionTargetSource source;

  bool get isAndroidEmulatorBridge => source == ZyraConnectionTargetSource.androidEmulatorBridge;
  bool get isExplicit => source == ZyraConnectionTargetSource.explicit;
  bool get isDesktopLoopback => source == ZyraConnectionTargetSource.desktopLoopback;
  bool get isPrivateNetwork => isAndroidEmulatorBridge || isDesktopLoopback || isExplicit;

  String get displayName {
    if (isAndroidEmulatorBridge) return 'Android emulator bridge';
    if (isDesktopLoopback) return 'Windows local runtime';
    return 'Configured private endpoint';
  }

  static ZyraConnectionTarget resolve({String? configuredUrl}) {
    final configured = configuredUrl?.trim() ?? '';
    if (configured.isNotEmpty) {
      final uri = Uri.parse(configured);
      ZyraEndpointPolicy.validate(uri.toString());
      return ZyraConnectionTarget(uri: uri, source: ZyraConnectionTargetSource.explicit);
    }

    if (Platform.isAndroid) {
      return ZyraConnectionTarget(
        uri: Uri.parse('http://10.0.2.2:8000'),
        source: ZyraConnectionTargetSource.androidEmulatorBridge,
      );
    }

    return ZyraConnectionTarget(
      uri: Uri.parse('http://127.0.0.1:8000'),
      source: ZyraConnectionTargetSource.desktopLoopback,
    );
  }
}

enum ZyraConnectionTargetSource {
  explicit,
  androidEmulatorBridge,
  desktopLoopback,
}
