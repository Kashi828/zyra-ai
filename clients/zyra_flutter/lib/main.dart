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
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xFF8F7CFF),
            brightness: Brightness.dark,
          ),
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
  ZyraTab tab = ZyraTab.home;
  bool connected = false;
  bool listening = false;
  bool running = false;
  String? lastAction;

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
    if (deviceId.text != zyraSessionContext.deviceId) {
      deviceId.value = TextEditingValue(text: zyraSessionContext.deviceId);
    }
    if (sessionId.text != zyraSessionContext.sessionId) {
      sessionId.value = TextEditingValue(text: zyraSessionContext.sessionId);
    }
    setState(() {});
  }

  void _syncContext() => zyraSessionContext.setCredentials(
        deviceId: deviceId.text,
        sessionId: sessionId.text,
      );

  Future<void> _checkConnection() async {
    try {
      final ok = await service.health();
      if (mounted) setState(() => connected = ok);
    } catch (_) {
      if (mounted) setState(() => connected = false);
    }
  }

  Future<void> _run() async {
    final text = command.text.trim().toLowerCase();
    if (text.isEmpty || running) return;
    if (text == 'calculator' || text == 'open calculator') {
      await _remote('open_app', {'name': 'calculator'});
      command.clear();
      return;
    }
    _show('Free-form execution is disabled. Use an allowlisted Quick action.');
  }

  Future<void> _remote(String action, Map<String, dynamic> payload) async {
    _syncContext();
    final credentials = zyraSessionContext.credentials;
    if (credentials == null) {
      _show('Enter a device ID and current session ID first.');
      return;
    }
    setState(() => running = true);
    try {
      final result = await service.executeRemoteCommand(
        credentials,
        action: action,
        payload: payload,
        commandId: 'flutter-${DateTime.now().microsecondsSinceEpoch}',
      );
      if (mounted) {
        setState(() => lastAction = result.message ?? '$action · ${result.status ?? 'completed'}');
        _show(result.message ?? (result.success ? 'Action completed.' : 'Action rejected.'));
      }
    } on ZyraApiException catch (error) {
      if (mounted) _show(error.message);
    } catch (error) {
      if (mounted) _show('ZYRA request failed: $error');
    } finally {
      if (mounted) setState(() => running = false);
    }
  }

  Future<void> _openFolder() async {
    final path = await _inputDialog('Open folder', 'Existing Windows folder path');
    if (path != null && path.trim().isNotEmpty) {
      await _remote('open_folder', {'path': path.trim()});
    }
  }

  Future<void> _openUrl() async {
    final url = await _inputDialog('Open URL', 'http:// or https:// URL');
    if (url != null && url.trim().isNotEmpty) {
      await _remote('open_url', {'url': url.trim()});
    }
  }

  Future<String?> _inputDialog(String title, String hint) async {
    final controller = TextEditingController();
    final value = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: InputDecoration(hintText: hint),
        ),
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

  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 860;
    return Scaffold(
      body: SafeArea(
        child: Row(
          children: [
            if (wide) _Rail(tab: tab, onTab: (value) => setState(() => tab = value)),
            Expanded(child: _page(wide)),
          ],
        ),
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
        ZyraTab.activity => _info('Activity', Icons.bolt_outlined, lastAction ?? 'No protected action has run yet.'),
        ZyraTab.devices => const ZyraDevicesPage(),
        ZyraTab.settings => _info('Settings', Icons.tune_outlined, 'Advanced controls and privacy settings.'),
      };

  Widget _home(bool wide) => ListView(
        padding: EdgeInsets.fromLTRB(wide ? 38 : 22, 24, wide ? 38 : 22, 40),
        children: [
          Row(children: [
            const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Good to see you', style: TextStyle(color: Colors.white54)),
              SizedBox(height: 4),
              Text('ZYRA', style: TextStyle(fontSize: 31, fontWeight: FontWeight.w700)),
            ])),
            Chip(label: Text(connected ? 'API connected' : 'API offline')),
          ]),
          const SizedBox(height: 20),
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
                  IconButton(onPressed: _checkConnection, tooltip: 'Check API', icon: const Icon(Icons.refresh)),
                ]),
                const SizedBox(height: 8),
                const Text('Shared in memory with Devices. No device secret or refresh token is stored.', style: TextStyle(color: Colors.white54, fontSize: 11)),
              ]),
            ),
          ),
          const SizedBox(height: 26),
          Center(child: Column(children: [
            Icon(running ? Icons.sync : Icons.auto_awesome, size: 62),
            const SizedBox(height: 14),
            Text(running ? 'Working…' : listening ? 'Listening…' : 'How can I help?', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w700)),
            const SizedBox(height: 6),
            const Text('One assistant across your phone and PC.', style: TextStyle(color: Colors.white54)),
          ])),
          const SizedBox(height: 24),
          Card(child: Padding(padding: const EdgeInsets.fromLTRB(16, 8, 8, 8), child: Row(children: [
            const Icon(Icons.chat_bubble_outline, color: Colors.white54),
            const SizedBox(width: 10),
            Expanded(child: TextField(controller: command, onSubmitted: (_) => _run(), decoration: const InputDecoration(hintText: 'Ask ZYRA anything…', border: InputBorder.none))),
            IconButton(onPressed: running ? null : () => setState(() => listening = !listening), icon: Icon(listening ? Icons.mic : Icons.mic_none)),
            FilledButton(onPressed: running ? null : _run, child: const Icon(Icons.arrow_upward)),
          ]))),
          if (lastAction != null) Padding(padding: const EdgeInsets.only(top: 10), child: Text('Latest: $lastAction', style: const TextStyle(color: Colors.white54, fontSize: 12))),
          const SizedBox(height: 26),
          const Text('Quick actions', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
          const SizedBox(height: 12),
          GridView.count(shrinkWrap: true, physics: const NeverScrollableScrollPhysics(), crossAxisCount: wide ? 4 : 2, crossAxisSpacing: 12, mainAxisSpacing: 12, childAspectRatio: wide ? 1.6 : 1.35, children: [
            _ActionTile(Icons.apps_outlined, 'Open calculator', () => _remote('open_app', {'name': 'calculator'})),
            _ActionTile(Icons.folder_open_outlined, 'Open folder', _openFolder),
            _ActionTile(Icons.language_outlined, 'Open URL', _openUrl),
            _ActionTile(Icons.devices_outlined, 'Manage devices', () => setState(() => tab = ZyraTab.devices)),
          ]),
          const SizedBox(height: 26),
          Card(child: ListTile(leading: const Icon(Icons.verified_user_outlined), title: Text(zyraSessionContext.configured ? 'Session configured' : 'Session not configured'), subtitle: Text(zyraSessionContext.configured ? 'Devices and protected actions share this in-memory context.' : 'Enter the current device and session IDs above.'))),
        ],
      );

  Widget _info(String title, IconData icon, String body) => Center(child: Padding(padding: const EdgeInsets.all(32), child: Card(child: Padding(padding: const EdgeInsets.all(28), child: Column(mainAxisSize: MainAxisSize.min, children: [Icon(icon, size: 42), const SizedBox(height: 16), Text(title, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w700)), const SizedBox(height: 8), Text(body, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white54))])))));
}

class _ActionTile extends StatelessWidget {
  const _ActionTile(this.icon, this.title, this.onTap);
  final IconData icon;
  final String title;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Card(child: InkWell(borderRadius: BorderRadius.circular(12), onTap: onTap, child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.center, children: [Icon(icon, size: 26), const SizedBox(height: 12), Text(title, style: const TextStyle(fontWeight: FontWeight.w600))]))));
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
