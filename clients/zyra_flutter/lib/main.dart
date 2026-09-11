import 'package:flutter/material.dart';

import 'devices_page.dart';

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
  ZyraTab tab = ZyraTab.home;
  final command = TextEditingController();
  bool listening = false;
  @override
  void dispose() { command.dispose(); super.dispose(); }
  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 860;
    return Scaffold(
      body: SafeArea(child: Row(children: [if (wide) _Rail(tab: tab, onTab: (v) => setState(() => tab = v)), Expanded(child: _page(wide))])),
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
          ZyraTab.home => _Home(command: command, listening: listening, wide: wide, onListen: () => setState(() => listening = !listening), onRun: _run),
          ZyraTab.activity => const _InfoPage(key: ValueKey('activity'), title: 'Activity', icon: Icons.bolt_outlined, body: 'Your ZYRA task timeline, progress, and protected actions.'),
          ZyraTab.devices => const ZyraDevicesPage(key: ValueKey('devices')),
          ZyraTab.settings => const _InfoPage(key: ValueKey('settings'), title: 'Settings', icon: Icons.tune_outlined, body: 'Appearance, privacy, notifications, and advanced controls.'),
        },
      );
  void _run() {
    final text = command.text.trim();
    if (text.isEmpty) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Ready: $text')));
    command.clear();
  }
}

class _Rail extends StatelessWidget {
  const _Rail({required this.tab, required this.onTab});
  final ZyraTab tab; final ValueChanged<ZyraTab> onTab;
  @override
  Widget build(BuildContext context) => Container(
        width: 82, margin: const EdgeInsets.all(14),
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
  const _Home({required this.command, required this.listening, required this.wide, required this.onListen, required this.onRun});
  final TextEditingController command; final bool listening; final bool wide; final VoidCallback onListen; final VoidCallback onRun;
  @override
  Widget build(BuildContext context) => CustomScrollView(slivers: [SliverPadding(padding: EdgeInsets.fromLTRB(wide ? 38 : 22, 24, wide ? 38 : 22, 40), sliver: SliverList(delegate: SliverChildListDelegate([
    Row(children: [const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text('Good to see you', style: TextStyle(color: Colors.white54)), SizedBox(height: 4), Text('ZYRA', style: TextStyle(fontSize: 31, fontWeight: FontWeight.w700))])), const _Pill(text: 'Protected')]),
    const SizedBox(height: 36), Center(child: Column(children: [AnimatedContainer(duration: const Duration(milliseconds: 260), width: listening ? 166 : 146, height: listening ? 166 : 146, decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [const Color(0xFFB7A6FF).withValues(alpha: .95), const Color(0xFF6E5DE7).withValues(alpha: .4), Colors.transparent]), boxShadow: [BoxShadow(color: const Color(0xFF8B7CFF).withValues(alpha: .22), blurRadius: 45, spreadRadius: 8)]), child: Center(child: Container(width: 84, height: 84, decoration: BoxDecoration(shape: BoxShape.circle, color: const Color(0xFF0D0F16), border: Border.all(color: Colors.white.withValues(alpha: .12))), child: const Icon(Icons.auto_awesome, size: 34)))), const SizedBox(height: 18), Text(listening ? 'Listening…' : 'How can I help?', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w700)), const SizedBox(height: 6), Text(listening ? 'Speak naturally. Your permissions still apply.' : 'One assistant across your phone and PC.', textAlign: TextAlign.center, style: const TextStyle(color: Colors.white54))])),
    const SizedBox(height: 28), _Composer(controller: command, listening: listening, onListen: onListen, onRun: onRun), const SizedBox(height: 26), const _Title('Quick actions'), const SizedBox(height: 12), _Actions(wide: wide), const SizedBox(height: 26), const _Title('Your ecosystem'), const SizedBox(height: 12), const _Ecosystem(), const SizedBox(height: 26), const _Title('Recent'), const SizedBox(height: 12), const _Recent(),
  ]))) ]);
}

class _Composer extends StatelessWidget {
  const _Composer({required this.controller, required this.listening, required this.onListen, required this.onRun});
  final TextEditingController controller; final bool listening; final VoidCallback onListen; final VoidCallback onRun;
  @override
  Widget build(BuildContext context) => Container(padding: const EdgeInsets.fromLTRB(16, 8, 8, 8), decoration: BoxDecoration(color: const Color(0xFF11141D), borderRadius: BorderRadius.circular(25), border: Border.all(color: Colors.white.withValues(alpha: .08))), child: Row(children: [const Icon(Icons.chat_bubble_outline, color: Colors.white54), const SizedBox(width: 10), Expanded(child: TextField(controller: controller, onSubmitted: (_) => onRun(), decoration: const InputDecoration(hintText: 'Ask ZYRA anything…', border: InputBorder.none))), IconButton(onPressed: onListen, icon: Icon(listening ? Icons.mic : Icons.mic_none)), FilledButton(onPressed: onRun, child: const Icon(Icons.arrow_upward))]));
}

class _Actions extends StatelessWidget {
  const _Actions({required this.wide}); final bool wide;
  @override
  Widget build(BuildContext context) { const items = [(Icons.apps_outlined, 'Open app'), (Icons.folder_open_outlined, 'Find files'), (Icons.language_outlined, 'Browse'), (Icons.more_horiz, 'More')]; return GridView.builder(shrinkWrap: true, physics: const NeverScrollableScrollPhysics(), itemCount: items.length, gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: wide ? 4 : 2, crossAxisSpacing: 12, mainAxisSpacing: 12, childAspectRatio: wide ? 1.65 : 1.35), itemBuilder: (_, i) => Material(color: const Color(0xFF11141D), borderRadius: BorderRadius.circular(20), child: InkWell(borderRadius: BorderRadius.circular(20), onTap: () {}, child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.center, children: [Icon(items[i].$1, size: 25), const SizedBox(height: 13), Text(items[i].$2, style: const TextStyle(fontWeight: FontWeight.w600))]))))); }
}

class _Ecosystem extends StatelessWidget {
  const _Ecosystem();
  @override
  Widget build(BuildContext context) => Container(padding: const EdgeInsets.all(18), decoration: BoxDecoration(color: const Color(0xFF11141D), borderRadius: BorderRadius.circular(24), border: Border.all(color: Colors.white.withValues(alpha: .07))), child: const Column(children: [ _Device(icon: Icons.smartphone_rounded, title: 'This phone', subtitle: 'Active session'), SizedBox(height: 14), _Device(icon: Icons.desktop_windows_rounded, title: 'Windows PC', subtitle: 'Ready for secure tasks') ]));
}

class _Device extends StatelessWidget {
  const _Device({required this.icon, required this.title, required this.subtitle}); final IconData icon; final String title; final String subtitle;
  @override
  Widget build(BuildContext context) => Row(children: [Container(width: 46, height: 46, decoration: BoxDecoration(color: Colors.white.withValues(alpha: .05), borderRadius: BorderRadius.circular(15)), child: Icon(icon)), const SizedBox(width: 13), Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: const TextStyle(fontWeight: FontWeight.w600)), const SizedBox(height: 4), Text(subtitle, style: const TextStyle(color: Colors.white54, fontSize: 12))])), const _Dot(), const SizedBox(width: 7), const Text('Online', style: TextStyle(fontSize: 12, color: Colors.white70))]);
}

class _Recent extends StatelessWidget {
  const _Recent();
  @override
  Widget build(BuildContext context) { const items = [('Opened browser', 'Windows PC · just now'), ('Checked connection', 'Windows PC · 8 min ago'), ('Paired device', 'Android · yesterday')]; return Container(decoration: BoxDecoration(color: const Color(0xFF11141D), borderRadius: BorderRadius.circular(22)), child: Column(children: [for (var i = 0; i < items.length; i++) ...[ListTile(leading: const CircleAvatar(child: Icon(Icons.history_rounded, size: 18)), title: Text(items[i].$1, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)), subtitle: Text(items[i].$2, style: const TextStyle(color: Colors.white54, fontSize: 12))), if (i != items.length - 1) Divider(height: 1, color: Colors.white.withValues(alpha: .05))]])); }
}

class _InfoPage extends StatelessWidget {
  const _InfoPage({required this.title, required this.icon, required this.body, super.key}); final String title; final String body; final IconData icon;
  @override
  Widget build(BuildContext context) => Center(child: Padding(padding: const EdgeInsets.all(28), child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [Container(width: 76, height: 76, decoration: BoxDecoration(color: Colors.white.withValues(alpha: .06), shape: BoxShape.circle), child: Icon(icon, size: 32)), const SizedBox(height: 22), Text(title, style: const TextStyle(fontSize: 30, fontWeight: FontWeight.w700)), const SizedBox(height: 10), Text(body, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white54, height: 1.5))])));
}
class _Title extends StatelessWidget { const _Title(this.text); final String text; @override Widget build(BuildContext context) => Text(text, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600)); }
class _Pill extends StatelessWidget { const _Pill({required this.text}); final String text; @override Widget build(BuildContext context) => Container(padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 9), decoration: BoxDecoration(color: const Color(0xFF102016), borderRadius: BorderRadius.circular(18)), child: Row(mainAxisSize: MainAxisSize.min, children: [const _Dot(), const SizedBox(width: 8), Text(text, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600))])); }
class _Mark extends StatelessWidget { const _Mark(); @override Widget build(BuildContext context) => Container(width: 44, height: 44, decoration: BoxDecoration(color: Colors.white.withValues(alpha: .07), borderRadius: BorderRadius.circular(15)), child: const Icon(Icons.auto_awesome)); }
class _Dot extends StatelessWidget { const _Dot(); @override Widget build(BuildContext context) => Container(width: 7, height: 7, decoration: const BoxDecoration(color: Color(0xFF77F29A), shape: BoxShape.circle)); }
