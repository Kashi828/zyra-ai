import 'dart:io';

/// Validates beta client API endpoints before the Flutter client connects.
/// Beta builds are intentionally limited to local/private HTTP(S) endpoints.
class ZyraEndpointPolicy {
  const ZyraEndpointPolicy._();

  static bool isAllowed(String value) {
    final uri = Uri.tryParse(value.trim());
    if (uri == null || (uri.scheme != 'http' && uri.scheme != 'https')) return false;
    if (uri.userInfo.isNotEmpty || uri.host.isEmpty) return false;
    return _isPrivateOrLocalHost(uri.host);
  }

  static void validate(String value) {
    if (!isAllowed(value)) {
      throw ArgumentError.value(value, 'baseUrl', 'ZYRA beta API endpoint must use HTTP(S) and a local/private host');
    }
  }

  static bool _isPrivateOrLocalHost(String host) {
    final normalized = host.toLowerCase().replaceFirst(RegExp(r'\.$'), '');
    if (normalized == 'localhost' || normalized == '127.0.0.1' || normalized == '::1' || normalized.endsWith('.local')) return true;
    final ip = InternetAddress.tryParse(normalized);
    if (ip == null || ip.type != InternetAddressType.IPv4) return false;
    final octets = normalized.split('.').map(int.parse).toList();
    if (octets[0] == 10 || octets[0] == 192 && octets[1] == 168) return true;
    return octets[0] == 172 && octets[1] >= 16 && octets[1] <= 31;
  }
}
