import 'dart:convert';
import 'dart:io';

class ZyraService {
  ZyraService({this.baseUrl = 'http://127.0.0.1:8000'});

  final String baseUrl;

  Future<bool> health() async {
    final client = HttpClient();
    try {
      final request = await client.getUrl(Uri.parse('$baseUrl/health'));
      final response = await request.close();
      return response.statusCode >= 200 && response.statusCode < 300;
    } catch (_) {
      return false;
    } finally {
      client.close(force: true);
    }
  }

  Future<List<ZyraDevice>> devices() async {
    final data = await _getJson('/devices');
    final items = data is Map<String, dynamic> ? data['devices'] : data;
    if (items is! List) return const [];
    return items.whereType<Map>().map((item) => ZyraDevice.fromJson(Map<String, dynamic>.from(item))).toList();
  }

  Future<ZyraSessionInventory> listSessions(ZyraSessionCredentials credentials, {bool includeInactive = false}) async {
    final data = await _postJson('/v1/session/list', {
      ...credentials.toJson(),
      'include_inactive': includeInactive,
    });
    return ZyraSessionInventory.fromJson(data);
  }

  Future<ZyraSessionRevokeResult> revokeSession(ZyraSessionCredentials credentials, String targetSessionId) async {
    final data = await _postJson('/v1/session/revoke', {
      ...credentials.toJson(),
      'target_session_id': targetSessionId,
    });
    return ZyraSessionRevokeResult.fromJson(data);
  }

  Future<ZyraCommandResult> execute(String command, {String? deviceId}) async {
    final body = <String, dynamic>{'command': command};
    if (deviceId != null && deviceId.isNotEmpty) body['device_id'] = deviceId;
    final data = await _postJson('/commands', body);
    return ZyraCommandResult.fromJson(data);
  }

  Future<dynamic> _getJson(String path) async {
    final client = HttpClient();
    try {
      final request = await client.getUrl(Uri.parse('$baseUrl$path'));
      request.headers.set(HttpHeaders.acceptHeader, 'application/json');
      final response = await request.close();
      final text = await utf8.decoder.bind(response).join();
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw HttpException('ZYRA API returned ${response.statusCode}');
      }
      return jsonDecode(text);
    } finally {
      client.close(force: true);
    }
  }

  Future<Map<String, dynamic>> _postJson(String path, Map<String, dynamic> body) async {
    final client = HttpClient();
    try {
      final request = await client.postUrl(Uri.parse('$baseUrl$path'));
      request.headers.contentType = ContentType.json;
      request.headers.set(HttpHeaders.acceptHeader, 'application/json');
      request.write(jsonEncode(body));
      final response = await request.close();
      final text = await utf8.decoder.bind(response).join();
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw HttpException('ZYRA API returned ${response.statusCode}');
      }
      final decoded = jsonDecode(text);
      return decoded is Map<String, dynamic> ? decoded : <String, dynamic>{'result': decoded};
    } finally {
      client.close(force: true);
    }
  }
}

class ZyraSessionCredentials {
  const ZyraSessionCredentials({required this.deviceId, required this.sessionId});

  final String deviceId;
  final String sessionId;

  Map<String, dynamic> toJson() => {
        'device_id': deviceId,
        'session_id': sessionId,
      };
}

class ZyraSessionInventory {
  const ZyraSessionInventory({required this.device, required this.summary, required this.sessions});

  final ZyraSessionDevice device;
  final ZyraSessionSummary summary;
  final List<ZyraSession> sessions;

  factory ZyraSessionInventory.fromJson(Map<String, dynamic> json) {
    final rawSessions = json['sessions'];
    return ZyraSessionInventory(
      device: ZyraSessionDevice.fromJson(_map(json['device'])),
      summary: ZyraSessionSummary.fromJson(_map(json['summary'])),
      sessions: rawSessions is List
          ? rawSessions.whereType<Map>().map((item) => ZyraSession.fromJson(Map<String, dynamic>.from(item))).toList()
          : const [],
    );
  }
}

class ZyraSessionDevice {
  const ZyraSessionDevice({required this.deviceId, required this.capabilities, required this.revoked, this.createdAt});

  final String deviceId;
  final List<String> capabilities;
  final bool revoked;
  final int? createdAt;

  factory ZyraSessionDevice.fromJson(Map<String, dynamic> json) => ZyraSessionDevice(
        deviceId: '${json['device_id'] ?? ''}',
        capabilities: (json['capabilities'] is List) ? (json['capabilities'] as List).map((v) => '$v').toList() : const [],
        revoked: json['revoked'] == true,
        createdAt: json['created_at'] is num ? (json['created_at'] as num).toInt() : null,
      );
}

class ZyraSessionSummary {
  const ZyraSessionSummary({required this.total, required this.active, required this.inactive});

  final int total;
  final int active;
  final int inactive;

  factory ZyraSessionSummary.fromJson(Map<String, dynamic> json) => ZyraSessionSummary(
        total: _int(json['total']),
        active: _int(json['active']),
        inactive: _int(json['inactive']),
      );
}

class ZyraSession {
  const ZyraSession({required this.sessionId, required this.deviceId, required this.active, required this.revoked, required this.current, required this.expiresAt});

  final String sessionId;
  final String deviceId;
  final bool active;
  final bool revoked;
  final bool current;
  final int expiresAt;

  factory ZyraSession.fromJson(Map<String, dynamic> json) => ZyraSession(
        sessionId: '${json['session_id'] ?? ''}',
        deviceId: '${json['device_id'] ?? ''}',
        active: json['active'] == true,
        revoked: json['revoked'] == true,
        current: json['current'] == true,
        expiresAt: _int(json['expires_at']),
      );
}

class ZyraSessionRevokeResult {
  const ZyraSessionRevokeResult({required this.revoked, required this.sessionId, required this.currentSession});

  final bool revoked;
  final String sessionId;
  final bool currentSession;

  factory ZyraSessionRevokeResult.fromJson(Map<String, dynamic> json) => ZyraSessionRevokeResult(
        revoked: json['revoked'] == true,
        sessionId: '${json['session_id'] ?? ''}',
        currentSession: json['current_session'] == true,
      );
}

int _int(dynamic value) => value is num ? value.toInt() : int.tryParse('$value') ?? 0;
Map<String, dynamic> _map(dynamic value) => value is Map ? Map<String, dynamic>.from(value) : <String, dynamic>{};

class ZyraDevice {
  const ZyraDevice({required this.id, required this.name, required this.online, this.platform});

  final String id;
  final String name;
  final bool online;
  final String? platform;

  factory ZyraDevice.fromJson(Map<String, dynamic> json) => ZyraDevice(
        id: '${json['id'] ?? json['device_id'] ?? ''}',
        name: '${json['name'] ?? json['device_name'] ?? 'Unknown device'}',
        online: json['online'] == true || json['status'] == 'online',
        platform: json['platform']?.toString(),
      );
}

class ZyraCommandResult {
  const ZyraCommandResult({this.message, this.success = true, this.data});

  final String? message;
  final bool success;
  final dynamic data;

  factory ZyraCommandResult.fromJson(Map<String, dynamic> json) => ZyraCommandResult(
        message: json['message']?.toString() ?? json['result']?.toString(),
        success: json['success'] != false,
        data: json['data'] ?? json['result'],
      );
}
