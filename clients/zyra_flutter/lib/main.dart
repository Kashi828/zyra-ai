import 'package:flutter/material.dart';

import 'devices_page.dart';
import 'zyra_service.dart';

void main() => runApp(const ZyraApp());

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

enum ZyraTab { home, activity, devices, settings }

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
  bool listening = false;
  bool connected = false;
  bool running = false;
  String? lastAction;

  @override
  void initState() {
    super.initState();
    _checkConnection();
  }

  @override
  void dispose() {
    command.dispose();
    deviceId.dispose();
    sessionId.dispose();
    super.dispose();
  }

  Future<void> _checkConnection() async {
    final ok = await service.health();
    if (mounted) setState(() => connected = ok);
  }

  ZyraSessionCredentials? _credentials() {
    final device = deviceId.text.trim();
    final session = sessionId.text.trim();
    if (device.isEmpty || session.isEmpty) return null;
    return ZyraSessionCredentials(deviceId: device, sessionId: session);
  }

  Future<void> _run() async {
    final text = command.text.trim();
    if (text.isEmpty || running) return;
    // Free-form text is deliberately not mapped to shell execution. Only the
    // explicit allowlisted actions below can reach the Windows command bridge.
    if (text.toLowerCase() == 'calculator' || text.toLowerCase() == 'open calculator') {
      await _remote('open_app', {'name': 'calculator'});
      command.clear();
      return;
    }
    _showMessage('Free-form commands are not connected yet. Use a Quick action.');
  }

  Future<void> _remote(String action, Map<String, dynamic> payload) async {
    final credentials = _credentials();
    if (credentials == null) {
      _showMessage('Enter your device ID and current session ID first.');
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
        _showMessage(result.message ?? (result.success ? 'Action completed.' : 'Action rejected.'));
      }
    } on ZyraApiException catch (error) {
      if (mounted) _showMessage(error.message);
    } catch (error) {
      if (mounted) _showMessage('ZYRA request failed: $error');
    } finally {
      if (mounted) setState(() => running = false);
    }
  }

  Future<void> _openApp() => _remote('open_app', {'name': 'calculator'});

  Future<void> _findFiles() async {
    final path = await _textDialog('Folder path', 'Enter an existing Windows folder path.');
    if (path != null && path.trim().isNotEmpty) await _remote('open_folder', {'path': path.trim()});
  }

  Future<void> _browse() async {
    final url = await _textDialog('Open URL', 'Only http:// and https:// URLs are accepted.');
    if (url != null && url.trim().isNotEmpty) await _remote('open_url', {'url': url.trim()});
  }

  Future<String?> _textDialog(String title, String hint) async {
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

  void _showMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 860;
    return Scaffold(
      body: SafeArea(child: Row(children: [
        if (wide) _Rail(tab: tab, onTab: (v) => setState(() => tab = v)),
        Expanded(child: _page(wide)),
      ])),
      bottomNavigationBar: wide ? null : NavigationBar(
        selectedIndex: tab.index,
        onDestinationSelected: (i) => setState(() => tab = ZyraTab.values[i]),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.auto_awesome), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.bolt_outlined), label: 'Activity'),
          NavigationDestination(icon: Icon(Icons.devices_outlined), label: 'Devices'),
          NavigationDestination(icon: Icon(Icons.tune_outlined), label: 'Settings'),
        ],
      ),
    );
  }

  Widget _page(bool wide) => AnimatedSwitcher(
        duration: const Duration(milliseconds: 260),
        child: switch (tab) {
          ZyraTab.home => _Home(
              key: const ValueKey('home'),
              command: command,
              deviceId: deviceId,
              sessionId: sessionId,
              listening: listening,
              wide: wide,
              connected: connected,
              running: running,
              lastAction: lastAction,
              onListen: () => setState(() => listening = !listening),
              onRun: _run,
              onOpenApp: _openApp,
              onFindFiles: _findFiles,
              onBrowse: _browse,
              onRefresh: _checkConnection,
            ),
          ZyraTab.activity => _InfoPage(key: const ValueKey('activity'), title: 'Activity', icon: Icons.bolt_outlined, body: lastAction ?? 'Run a protected action to see its latest result here.'),
          ZyraTab.devices => const ZyraDevicesPage(key: ValueKey('devices')),
          ZyraTab.settings => const _InfoPage(key: ValueKey('settings'), title: 'Settings', icon: Icons.tune_outlined, body: 'Appearance, privacy, notifications, and advanced controls.'),
        },
      );
}

class _Rail extends StatelessWidget {
  const _Rail({required this.tab, required this.onTab});
  final ZyraTab tab;
  final ValueChanged<ZyraTab> onTab;
  @override
  Widget build(BuildContext context) => Container(
        width: 82,
        margin: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: const Color(0xFF0D0F16), borderRadius: BorderRadius.circular(26), border: Border.all(color: Colors.white.withValues(alpha: .07))),
        child: Column(children: [
          const SizedBox(height: 22), const _Mark(), const SizedBox(height: 30),
          for (final value in ZyraTab.values) Padding(
            padding: const EdgeInsets.symmetric(vertical: 5),
            child: IconButton.filledTonal(isSelected: value == tab, onPressed: () => onTab(value), icon: Icon(_tabIcon(value))),
          ),
          const Spacer(), const Padding(padding: EdgeInsets.only(bottom: 18), child: CircleAvatar(radius: 18, child: Icon(Icons.person_outline))),
        ]),
      );
  IconData _tabIcon(ZyraTab v) => switch (v) { ZyraTab.home => Icons.auto_awesome, ZyraTab.activity => Icons.bolt_outlined, ZyraTab.devices => Icons.devices_outlined, ZyraTab.settings => Icons.tune_outlined };
}

class _Home extends StatelessWidget {
  const _Home({super.key, required this.command, required this.deviceId, required this.sessionId, required this.listening, required this.wide, required this.connected, required this.running, required this.lastAction, required this.onListen, required this.onRun, required this.onOpenApp, required this.onFindFiles, required this.onBrowse, required this.onRefresh});
  final TextEditingController command;
  final TextEditingController deviceId;
  final TextEditingController sessionId;
  final bool listening;
  final bool wide;
  final bool connected;
  final bool running;
  final String? lastAction;
  final VoidCallback onListen;
  final VoidCallback onRun;
  final VoidCallback onOpenApp;
  final VoidCallback onFindFiles;
  final VoidCallback onBrowse;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) => CustomScrollView(slivers: [
        SliverPadding(
          padding: EdgeInsets.fromLTRB(wide ? 38 : 22, 24, wide ? 38 : 22, 40),
          sliver: SliverList(delegate: SliverChildListDelegate([
            Row(children: [
              const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text('Good to see you', style: TextStyle(color: Colors.white54)), SizedBox(height: 4), Text('ZYRA', style: TextStyle(fontSize: 31, fontWeight: FontWeight.w700))])),
              _Pill(text: connected ? 'Connected' : 'Offline'),
            ]),
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(color: const Color(0xFF11141D), borderRadius: BorderRadius.circular(20), border: Border.all(color: Colors.white.withValues(alpha: .07))),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('Secure session', style: TextStyle(fontWeight: FontWeight.w600)),
                const SizedBox(height: 10),
                Row(children: [
                  Expanded(child: TextField(controller: deviceId, decoration: const InputDecoration(labelText: 'Device ID', border: OutlineInputBorder(), isDense: true))),
                  const SizedBox(width: 10),
                  Expanded(child: TextField(controller: sessionId, decoration: const InputDecoration(labelText: 'Current session ID', border: OutlineInputBorder(), isDense: true))),
                  const SizedBox(width: 8),
                  IconButton(onPressed: onRefresh, tooltip: 'Check API', icon: const Icon(Icons.refresh)),
                ]),
                const SizedBox(height: 8),
                const Text('Only device/session identifiers are used here; no device secret or refresh token is stored.', style: TextStyle(color: Colors.white54, fontSize: 11)),
              ]),
            ),
            const SizedBox(height: 28),
            Center(child: Column(children: [
              AnimatedContainer(duration: const Duration(milliseconds: 260), width: listening ? 166 : 146, height: listening ? 166 : 146, decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [const Color(0xFFB7A6FF).withValues(alpha: .95), const Color(0xFF6E5DE7).withValues(alpha: .4), Colors.transparent]), boxShadow: [BoxShadow(color: const Color(0xFF8B7CFF).withValues(alpha: .22), blurRadius: 45, spreadRadius: 8)]), child: Center(child: Container(width: 84, height: 84, decoration: BoxDecoration(shape: BoxShape.circle, color: const Color(0xFF0D0F16), border: Border.all(color: Colors.white.withValues(alpha: .12))), child: Icon(running ? Icons.sync : Icons.auto_awesome, size: 34)))),
              const SizedBox(height: 18), Text(listening ? 'Listening…' : (running ? 'Working…' : 'How can I help?'), style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w700)),
              const SizedBox(height: 6), Text(listening ? 'Speak naturally. Your permissions still apply.' : 'One assistant across your phone and PC.', textAlign: TextAlign.center, style: const TextStyle(color: Colors.white54)),
            ])),
            const SizedBox(height: 28),
            _Composer(controller: command, listening: listening, running: running, onListen: onListen, onRun: onRun),
            if (lastAction != null) Padding(padding: const EdgeInsets.only(top: 10), child: Text('Latest: $lastAction', style: const TextStyle(color: Colors.white54, fontSize: 12))),
            const SizedBox(height: 26), const _Title('Quick actions'), const SizedBox(height: 12),
            _Actions(wide: wide, onOpenApp: onOpenApp, onFindFiles: onFindFiles, onBrowse: onBrowse),
            const SizedBox(height: 26), const _Title('Your ecosystem'), const SizedBox(height: 12), const _Ecosystem(),
            const SizedBox(height: 26), const _Title('Recent'), const SizedBox(height: 12), _Recent(lastAction: lastAction),
          ])),
        ),
      ]);
}

class _Composer extends StatelessWidget {
  const _Composer({required this.controller, required this.listening, required this.running, required this.onListen, required this.onRun});
  final TextEditingController controller;
  final bool listening;
  final bool running;
  final VoidCallback onListen;
  final VoidCallback onRun;
  @override
  Widget build(BuildContext context) => Container(padding: const EdgeInsets.fromLTRB(16, 8, 8, 8), decoration: BoxDecoration(color: const Color(0xFF11141D), borderRadius: BorderRadius.circular(25), border: Border.all(color: Colors.white.withValues(alpha: .08))), child: Row(children: [const Icon(Icons.chat_bubble_outline, color: Colors.white54), const SizedBox(width: 10), Expanded(child: TextField(controller: controller, onSubmitted: (_) => onRun(), decoration: const InputDecoration(hintText: 'Ask ZYRA anything…', border: InputBorder.none))), IconButton(onPressed: running ? null : onListen, icon: Icon(listening ? Icons.mic : Icons.mic_none)), FilledButton(onPressed: running ? null : onRun, child: const Icon(Icons.arrow_upward))]));
}

class _Actions extends StatelessWidget {
  const _Actions({required this.wide, required this.onOpenApp, required this.onFindFiles, required this.onBrowse});
  final bool wide;
  final VoidCallback onOpenApp;
  final VoidCallback onFindFiles;
  final VoidCallback onBrowse;
  @override
  Widget build(BuildContext context) {
    final items = [
      (Icons.apps_outlined, 'Open app', onOpenApp),
      (Icons.folder_open_outlined, 'Find files', onFindFiles),
      (Icons.language_outlined, 'Browse', onBrowse),
      (Icons.devices_outlined, 'Manage devices', () {}),
    ];
    return GridView.builder(shrinkWrap: true, physics: const NeverScrollableScrollPhysics(), itemCount: items.length, gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: wide ? 4 : 2, crossAxisSpacing: 12, mainAxisSpacing: 12, childAspectRatio: wide ? 1.65 : 1.35), itemBuilder: (_, i) => Material(color: const Color(0xFF11141D), borderRadius: BorderRadius.circular(20), child: InkWell(borderRadius: BorderRadius.circular(20), onTap: items[i].$3, child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.center, children: [Icon(items[i].$1, size: 25), const SizedBox(height: 13), Text(items[i].$2, style: const TextStyle(fontWeight: FontWeight.w600))])))));
  }
}

class _Ecosystem extends StatelessWidget {
  const _Ecosystem();
  @override
  Widget build(BuildContext context) => Container(padding: const EdgeInsets.all(18), decoration: BoxDecoration(color: const Color(0xFF11141D), borderRadius: BorderRadius.circular(24), border: Border.all(color: Colors.white.withValues(alpha: .07))), child: const Column(children: [_Device(icon: Icons.smartphone_rounded, title: 'This phone', subtitle: 'Authenticated client'), SizedBox(height: 14), _Device(icon: Icons.desktop_windows_rounded, title: 'Windows PC', subtitle: 'Allowlisted secure actions')]));
}

class _Device extends StatelessWidget {
  const _Device({required this.icon, required this.title, required this.subtitle});
  final IconData icon;
  final String title;
  final String subtitle;
  @override
  Widget build(BuildContext context) => Row(children: [Container(width: 46, height: 46, decoration: BoxDecoration(color: Colors.white.withValues(alpha: .05), borderRadius: BorderRadius.circular(15)), child: Icon(icon)), const SizedBox(width: 13), Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: const TextStyle(fontWeight: FontWeight.w600)), const SizedBox(height: 4), Text(subtitle, style: const TextStyle(color: Colors.white54, fontSize: 12))])), const _Dot(), const SizedBox(width: 7), const Text('Ready', style: TextStyle(fontSize: 12, color: Colors.white70))]);
}

class _Recent extends StatelessWidget {
  const _Recent({this.lastAction});
  final String? lastAction;
  @override
  Widget build(BuildContext context) {
    final items = <(String, String)>[
      if (lastAction != null) ('Protected action', lastAction!),
      ('Session security', 'Device/session credentials only'),
      ('Command bridge', 'Allowlisted Windows actions'),
    ];
    return Container(decoration: BoxDecoration(color: const Color(0xFF11141D), borderRadius: BorderRadius.circular(22)), child: Column(children: [for (var i = 0; i < items.length; i++) ...[ListTile(leading: const CircleAvatar(child: Icon(Icons.history_rounded, size: 18)), title: Text(items[i].$1, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)), subtitle: Text(items[i].$2, style: const TextStyle(color: Colors.white54, fontSize: 12))), if (i != items.length - 1) Divider(height: 1, color: Colors.white.withValues(alpha: .05))]]));
  }
}

class _InfoPage extends StatelessWidget {
  const _InfoPage({required this.title, required this.icon, required this.body, super.key});
  final String title;
  final String body;
  final IconData icon;
  @override
  Widget build(BuildContext context) => Center(child: Padding(padding: const EdgeInsets.all(28), child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [Container(width: 76, height: 76, decoration: BoxDecoration(color: Colors.white.withValues(alpha: .06), shape: BoxShape.circle), child: Icon(icon, size: 32)), const SizedBox(height: 22), Text(title, style: const TextStyle(fontSize: 30, fontWeight: FontWeight.w700)), const SizedBox(height: 10), Text(body, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white54, height: 1.5))])));
}

class _Title extends StatelessWidget {
  const _Title(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Text(text, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600));
}

class _Pill extends StatelessWidget {
  const _Pill({required this.text});
  final String text;
  @override
  Widget build(BuildContext context) => Container(padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 9), decoration: BoxDecoration(color: const Color(0xFF102016), borderRadius: BorderRadius.circular(18)), child: Row(mainAxisSize: MainAxisSize.min, children: [const _Dot(), const SizedBox(width: 8), Text(text, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600))]));
}

class _Mark extends StatelessWidget {
  const _Mark();
  @override
  Widget build(BuildContext context) => Container(width: 44, height: 44, decoration: BoxDecoration(color: Colors.white.withValues(alpha: .07), borderRadius: BorderRadius.circular(15)), child: const Icon(Icons.auto_awesome));
}

class _Dot extends StatelessWidget {
  const _Dot();
  @override
  Widget build(BuildContext context) => Container(width: 7, height: 7, decoration: const BoxDecoration(color: Color(0xFF77F29A), shape: BoxShape.circle));
}
