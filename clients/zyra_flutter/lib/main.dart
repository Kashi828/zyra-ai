import 'package:flutter/material.dart';

import 'devices_page.dart';
import 'session_context.dart';
import 'zyra_service.dart';

void main() => runApp(const ZyraApp());

enum ZyraTab { home, activity, devices, settings }

class ZyraApp extends StatelessWidget {
  const ZyraApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        debugShowCheckedModeBanner: false,
        title: 'ZYRA AI',
        theme: ThemeData(
          brightness: Brightness.dark,
          useMaterial3: true,
          scaffoldBackgroundColor: const Color(0xFF07080D),
          colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF8F7CFF), brightness: Brightness.dark),
        ),
        home: const ZyraHome(),
      );
}

class ZyraHome extends StatefulWidget {
  const ZyraHome({super.key});

  @override
  State<ZyraHome> createState() => _ZyraHomeState();
}

class _ZyraHomeState extends State<ZyraHome> {
  final service = ZyraService();
  final command = TextEditingController();
  final deviceId = TextEditingController();
  final sessionId = TextEditingController();
  final List<_ActivityEntry> activity = <_ActivityEntry>[];
  ZyraTab tab = ZyraTab.home;
  ZyraConnectionStatus connection = const ZyraConnectionStatus(ZyraConnectionState.offline);
  bool listening = false;
  bool running = false;
  bool checkingConnection = false;
  String? lastAction;

  bool get commandReady => connection.isReady;

  @override
  void initState() {
    super.initState();
    deviceId.text = zyraSessionContext.deviceId;
    sessionId.text = zyraSessionContext.sessionId;
    zyraSessionContext.addListener(_contextChanged);
    _checkConnection();
  }

  @override
  void dispose() {
    zyraSessionContext.removeListener(_contextChanged);
    command.dispose();
    deviceId.dispose();
    sessionId.dispose();
    super.dispose();
  }

  void _contextChanged() {
    if (!mounted) return;
    if (deviceId.text != zyraSessionContext.deviceId) deviceId.value = TextEditingValue(text: zyraSessionContext.deviceId);
    if (sessionId.text != zyraSessionContext.sessionId) sessionId.value = TextEditingValue(text: zyraSessionContext.sessionId);
    _checkConnection();
  }

  void _syncContext() => zyraSessionContext.setCredentials(deviceId: deviceId.text, sessionId: sessionId.text);

  Future<void> _checkConnection() async {
    if (checkingConnection) return;
    checkingConnection = true;
    if (mounted) setState(() {});
    try {
      final status = await service.connectionStatus(zyraSessionContext.credentials);
      if (mounted) setState(() => connection = status);
    } catch (error) {
      if (mounted) setState(() => connection = ZyraConnectionStatus(ZyraConnectionState.error, detail: '$error'));
    } finally {
      checkingConnection = false;
      if (mounted) setState(() {});
    }
  }

  Future<void> _run() async {
    final text = command.text.trim().toLowerCase();
    if (text.isEmpty || running) return;
    if (!commandReady) {
      _recordActivity('command', 'Blocked: Windows connection is ${_stateLabel(connection.state).toLowerCase()}.', success: false);
      _show(connection.detail.isEmpty ? 'Windows connection is not ready.' : connection.detail);
      await _checkConnection();
      return;
    }
    if (text == 'calculator' || text == 'open calculator') {
      await _remote('open_app', {'name': 'calculator'});
      command.clear();
      return;
    }
    _show('Free-form execution is disabled. Use an allowlisted Quick action.');
  }

  void _recordActivity(String title, String detail, {bool success = true}) {
    activity.insert(0, _ActivityEntry(title: title, detail: detail, success: success, time: DateTime.now()));
    if (activity.length > 25) activity.removeLast();
  }

  Future<void> _remote(String action, Map<String, dynamic> payload) async {
    _syncContext();
    final credentials = zyraSessionContext.credentials;
    if (credentials == null) {
      _recordActivity(action, 'Blocked: device/session credentials are missing.', success: false);
      _show('Enter a device ID and current session ID first.');
      return;
    }
    final status = await service.connectionStatus(credentials);
    if (mounted) setState(() => connection = status);
    if (!status.isReady) {
      _recordActivity(action, 'Blocked: ${status.detail.isEmpty ? _stateLabel(status.state) : status.detail}', success: false);
      _show(status.detail.isEmpty ? 'Windows connection is not ready.' : status.detail);
      return;
    }
    if (running) return;
    setState(() => running = true);
    try {
      final result = await service.executeRemoteCommand(credentials, action: action, payload: payload, commandId: 'flutter-${DateTime.now().microsecondsSinceEpoch}');
      final detail = result.message ?? '$action · ${result.status ?? 'completed'}';
      if (mounted) {
        setState(() {
          lastAction = detail;
          activity.insert(0, _ActivityEntry(title: action, detail: detail, success: result.success, time: DateTime.now()));
          if (activity.length > 25) activity.removeLast();
        });
        _show(result.message ?? (result.success ? 'Action completed.' : 'Action rejected.'));
      }
    } on ZyraApiException catch (error) {
      _recordActivity(action, 'Rejected: ${error.message}', success: false);
      if (mounted) _show(error.message);
      await _checkConnection();
    } catch (error) {
      _recordActivity(action, 'Request failed: $error', success: false);
      if (mounted) _show('ZYRA request failed: $error');
    } finally {
      if (mounted) setState(() => running = false);
    }
  }

  Future<void> _openFolder() async {
    if (!await _requireReady()) return;
    final path = await _inputDialog('Open folder', 'Existing Windows folder path');
    if (path != null && path.trim().isNotEmpty) await _remote('open_folder', {'path': path.trim()});
  }

  Future<void> _openUrl() async {
    if (!await _requireReady()) return;
    final url = await _inputDialog('Open URL', 'http:// or https:// URL');
    if (url != null && url.trim().isNotEmpty) await _remote('open_url', {'url': url.trim()});
  }

  Future<bool> _requireReady() async {
    if (commandReady) return true;
    _show(connection.detail.isEmpty ? 'Windows connection is not ready.' : connection.detail);
    await _checkConnection();
    return false;
  }

  Future<String?> _inputDialog(String title, String hint) async {
    final controller = TextEditingController();
    final value = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: TextField(controller: controller, autofocus: true, decoration: InputDecoration(hintText: hint)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(context, controller.text), child: const Text('Continue')),
        ],
      ),
    );
    controller.dispose();
    return value;
  }

  void _show(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  String _stateLabel(ZyraConnectionState state) => switch (state) {
        ZyraConnectionState.offline => 'Offline',
        ZyraConnectionState.reachable => 'Reachable',
        ZyraConnectionState.authenticated => 'Authenticated',
        ZyraConnectionState.ready => 'Ready',
        ZyraConnectionState.error => 'Error',
      };

  IconData _stateIcon(ZyraConnectionState state) => switch (state) {
        ZyraConnectionState.offline => Icons.cloud_off_outlined,
        ZyraConnectionState.reachable => Icons.wifi_outlined,
        ZyraConnectionState.authenticated => Icons.lock_outline,
        ZyraConnectionState.ready => Icons.verified_outlined,
        ZyraConnectionState.error => Icons.error_outline,
      };

  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 860;
    return Scaffold(
      body: SafeArea(
        child: Row(children: [if (wide) _Rail(tab: tab, onTab: (value) => setState(() => tab = value)), Expanded(child: _page(wide))]),
      ),
      bottomNavigationBar: wide
          ? null
          : NavigationBar(
              selectedIndex: tab.index,
              onDestinationSelected: (index) => setState(() => tab = ZyraTab.values[index]),
              destinations: const [
                NavigationDestination(icon: Icon(Icons.auto_awesome), label: 'Home'),
                NavigationDestination(icon: Icon(Icons.bolt_outlined), label: 'Activity'),
                NavigationDestination(icon: Icon(Icons.devices_outlined), label: 'Devices'),
                NavigationDestination(icon: Icon(Icons.tune_outlined), label: 'Settings'),
              ],
            ),
    );
  }

  Widget _page(bool wide) => switch (tab) {
        ZyraTab.home => _home(wide),
        ZyraTab.activity => _activityPage(),
        ZyraTab.devices => const ZyraDevicesPage(),
        ZyraTab.settings => _info('Settings', Icons.tune_outlined, 'Advanced controls and privacy settings.'),
      };

  Widget _activityPage() => ListView(
        padding: const EdgeInsets.fromLTRB(22, 24, 22, 40),
        children: [
          Row(children: [
            const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Protected activity', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w700)),
              SizedBox(height: 5),
              Text('Recent actions from this ZYRA client session.', style: TextStyle(color: Colors.white54)),
            ])),
            if (activity.isNotEmpty) TextButton.icon(onPressed: () => setState(activity.clear), icon: const Icon(Icons.delete_outline), label: const Text('Clear')),
          ]),
          const SizedBox(height: 20),
          if (activity.isEmpty)
            Card(child: Padding(padding: const EdgeInsets.all(30), child: Column(children: const [Icon(Icons.history, size: 42), SizedBox(height: 12), Text('No activity yet', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)), SizedBox(height: 6), Text('Run an allowlisted Quick action and its result will appear here.', textAlign: TextAlign.center, style: TextStyle(color: Colors.white54))])))
          else
            for (final entry in activity) _activityTile(entry),
        ],
      );

  Widget _activityTile(_ActivityEntry entry) => Card(
        margin: const EdgeInsets.only(bottom: 10),
        child: ListTile(
          leading: Icon(entry.success ? Icons.check_circle_outline : Icons.error_outline),
          title: Text(entry.title),
          subtitle: Text(entry.detail),
          trailing: Text(_formatTime(entry.time), style: const TextStyle(color: Colors.white54, fontSize: 11)),
        ),
      );

  String _formatTime(DateTime time) => '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';

  Widget _home(bool wide) => ListView(
        padding: EdgeInsets.fromLTRB(wide ? 38 : 22, 24, wide ? 38 : 22, 40),
        children: [
          Row(children: [
            const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text('Good to see you', style: TextStyle(color: Colors.white54)), SizedBox(height: 4), Text('ZYRA', style: TextStyle(fontSize: 31, fontWeight: FontWeight.w700))])),
            _connectionChip(),
          ]),
          const SizedBox(height: 16),
          _connectionCard(),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('Secure session', style: TextStyle(fontWeight: FontWeight.w600)),
                const SizedBox(height: 10),
                Row(children: [
                  Expanded(child: TextField(controller: deviceId, onChanged: (_) => _syncContext(), decoration: const InputDecoration(labelText: 'Device ID', border: OutlineInputBorder(), isDense: true))),
                  const SizedBox(width: 10),
                  Expanded(child: TextField(controller: sessionId, onChanged: (_) => _syncContext(), decoration: const InputDecoration(labelText: 'Current session ID', border: OutlineInputBorder(), isDense: true))),
                  IconButton(onPressed: checkingConnection ? null : _checkConnection, tooltip: 'Check connection', icon: const Icon(Icons.refresh)),
                ]),
                const SizedBox(height: 8),
                const Text('Shared in memory with Devices. No device secret or refresh token is stored.', style: TextStyle(color: Colors.white54, fontSize: 11)),
              ]),
            ),
          ),
          const SizedBox(height: 26),
          Center(child: Column(children: [Icon(running ? Icons.sync : Icons.auto_awesome, size: 62), const SizedBox(height: 14), Text(running ? 'Working…' : listening ? 'Listening…' : 'How can I help?', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w700)), const SizedBox(height: 6), const Text('One assistant across your phone and PC.', style: TextStyle(color: Colors.white54))])),
          const SizedBox(height: 24),
          Card(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 8, 8),
              child: Row(children: [
                const Icon(Icons.chat_bubble_outline, color: Colors.white54),
                const SizedBox(width: 10),
                Expanded(child: TextField(controller: command, onSubmitted: (_) => _run(), decoration: InputDecoration(hintText: commandReady ? 'Ask ZYRA anything…' : 'Connect Windows to enable commands', border: InputBorder.none))),
                IconButton(onPressed: running ? null : () => setState(() => listening = !listening), icon: Icon(listening ? Icons.mic : Icons.mic_none)),
                FilledButton(onPressed: running || !commandReady ? null : _run, child: const Icon(Icons.arrow_upward)),
              ]),
            ),
          ),
          if (lastAction != null) Padding(padding: const EdgeInsets.only(top: 10), child: Text('Latest: $lastAction', style: const TextStyle(color: Colors.white54, fontSize: 12))),
          const SizedBox(height: 26),
          const Text('Quick actions', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
          const SizedBox(height: 12),
          GridView.count(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisCount: wide ? 4 : 2,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: wide ? 1.6 : 1.35,
            children: [
              _ActionTile(Icons.apps_outlined, 'Open calculator', commandReady ? () => _remote('open_app', {'name': 'calculator'}) : null),
              _ActionTile(Icons.folder_open_outlined, 'Open folder', commandReady ? _openFolder : null),
              _ActionTile(Icons.language_outlined, 'Open URL', commandReady ? _openUrl : null),
              _ActionTile(Icons.devices_outlined, 'Manage devices', () => setState(() => tab = ZyraTab.devices)),
            ],
          ),
          const SizedBox(height: 26),
          Card(child: ListTile(leading: Icon(_stateIcon(connection.state)), title: Text(commandReady ? 'Windows command bridge ready' : 'Windows command bridge blocked'), subtitle: Text(connection.detail.isEmpty ? 'Remote actions require an authenticated, active session and required capabilities.' : connection.detail))),
        ],
      );

  Widget _connectionChip() => Chip(avatar: Icon(_stateIcon(connection.state), size: 16), label: Text(_stateLabel(connection.state)));

  Widget _connectionCard() => Card(
        child: ListTile(
          leading: Icon(_stateIcon(connection.state), size: 30),
          title: Text('Windows connection · ${_stateLabel(connection.state)}', style: const TextStyle(fontWeight: FontWeight.w600)),
          subtitle: Text(connection.detail.isEmpty ? 'Reachability, authentication and readiness are checked separately.' : connection.detail),
          trailing: checkingConnection ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2)) : IconButton(onPressed: _checkConnection, tooltip: 'Refresh status', icon: const Icon(Icons.refresh)),
        ),
      );

  Widget _info(String title, IconData icon, String body) => Center(child: Padding(padding: const EdgeInsets.all(32), child: Card(child: Padding(padding: const EdgeInsets.all(28), child: Column(mainAxisSize: MainAxisSize.min, children: [Icon(icon, size: 42), const SizedBox(height: 16), Text(title, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w700)), const SizedBox(height: 8), Text(body, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white54))])))));
}

class _ActivityEntry {
  const _ActivityEntry({required this.title, required this.detail, required this.success, required this.time});
  final String title;
  final String detail;
  final bool success;
  final DateTime time;
}

class _ActionTile extends StatelessWidget {
  const _ActionTile(this.icon, this.title, this.onTap);
  final IconData icon;
  final String title;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) => Card(child: InkWell(borderRadius: BorderRadius.circular(12), onTap: onTap, child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.center, children: [Icon(icon, size: 26), const SizedBox(height: 12), Text(title, style: TextStyle(fontWeight: FontWeight.w600, color: onTap == null ? Colors.white38 : null))]))));
}

class _Rail extends StatelessWidget {
  const _Rail({required this.tab, required this.onTab});
  final ZyraTab tab;
  final ValueChanged<ZyraTab> onTab;

  @override
  Widget build(BuildContext context) => Container(
        width: 82,
        margin: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: const Color(0xFF0D0F16), borderRadius: BorderRadius.circular(26)),
        child: Column(children: [
          const SizedBox(height: 22),
          const Icon(Icons.auto_awesome, size: 28),
          const SizedBox(height: 30),
          for (final value in ZyraTab.values)
            Padding(padding: const EdgeInsets.symmetric(vertical: 5), child: IconButton.filledTonal(isSelected: value == tab, onPressed: () => onTab(value), icon: Icon(switch (value) { ZyraTab.home => Icons.auto_awesome, ZyraTab.activity => Icons.bolt_outlined, ZyraTab.devices => Icons.devices_outlined, ZyraTab.settings => Icons.tune_outlined }))),
          const Spacer(),
          const Padding(padding: EdgeInsets.only(bottom: 18), child: CircleAvatar(radius: 18, child: Icon(Icons.person_outline))),
        ]),
      );
}