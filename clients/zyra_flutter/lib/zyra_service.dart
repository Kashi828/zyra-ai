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
