import 'package:flutter/material.dart';

import 'zyra_service.dart';

class ZyraDevicesPage extends StatefulWidget {
  ZyraDevicesPage({super.key, ZyraService? service}) : service = service ?? ZyraService();

  final ZyraService service;

  @override
  State<ZyraDevicesPage> createState() => _ZyraDevicesPageState();
}

class _ZyraDevicesPageState extends State<ZyraDevicesPage> {
  final deviceId = TextEditingController();
  final sessionId = TextEditingController();
  ZyraSessionInventory? inventory;
  bool includeInactive = false;
  bool loading = false;
  String? error;

  @override
  void dispose() {
    deviceId.dispose();
    sessionId.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final device = deviceId.text.trim();
    final session = sessionId.text.trim();
    if (device.isEmpty || session.isEmpty) {
      setState(() => error = 'Enter your device ID and current session ID.');
      return;
    }
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final result = await widget.service.listSessions(
        ZyraSessionCredentials(deviceId: device, sessionId: session),
        includeInactive: includeInactive,
      );
      if (!mounted) return;
      setState(() => inventory = result);
    } catch (e) {
      if (!mounted) return;
      setState(() => error = _message(e));
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> _revoke(ZyraSession target) async {
    if (target.current) {
      _show('The current session cannot be revoked from this screen.');
      return;
    }
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Revoke session?'),
        content: const Text('This will invalidate the selected session. The server remains responsible for authorization.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Revoke')),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await widget.service.revokeSession(
        ZyraSessionCredentials(deviceId: deviceId.text.trim(), sessionId: sessionId.text.trim()),
        target.sessionId,
      );
      _show('Session revoked.');
      await _load();
    } catch (e) {
      _show(_message(e));
    }
  }

  void _show(String text) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));

  String _message(Object error) {
    final text = error.toString();
    return text.startsWith('Exception: ') ? text.substring(11) : text;
  }

  @override
  Widget build(BuildContext context) => CustomScrollView(
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(24, 28, 24, 40),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                Row(children: [
                  const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('Devices', style: TextStyle(fontSize: 31, fontWeight: FontWeight.w700)),
                    SizedBox(height: 5),
                    Text('Manage sessions authorized for your device.', style: TextStyle(color: Colors.white54)),
                  ])),
                  IconButton(onPressed: loading ? null : _load, tooltip: 'Refresh', icon: const Icon(Icons.refresh)),
                ]),
                const SizedBox(height: 24),
                _Credentials(deviceId: deviceId, sessionId: sessionId, onLoad: _load),
                const SizedBox(height: 12),
                SwitchListTile.adaptive(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 4),
                  value: includeInactive,
                  onChanged: loading ? null : (value) => setState(() => includeInactive = value),
                  title: const Text('Show inactive sessions'),
                  subtitle: const Text('Historical sessions are read-only and cannot be revived here.', style: TextStyle(color: Colors.white54)),
                ),
                if (loading) const Padding(padding: EdgeInsets.all(28), child: Center(child: CircularProgressIndicator())),
                if (error != null) _ErrorCard(message: error!),
                if (!loading && error == null && inventory == null) const _EmptyCard(),
                if (inventory != null && !loading) _Inventory(inventory: inventory!, onRevoke: _revoke),
              ]),
            ),
          ),
        ],
      );
}

class _Credentials extends StatelessWidget {
  const _Credentials({required this.deviceId, required this.sessionId, required this.onLoad});
  final TextEditingController deviceId;
  final TextEditingController sessionId;
  final VoidCallback onLoad;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(color: const Color(0xFF11141D), borderRadius: BorderRadius.circular(22), border: Border.all(color: Colors.white.withValues(alpha: .07))),
        child: Column(children: [
          TextField(controller: deviceId, decoration: const InputDecoration(labelText: 'Device ID', prefixIcon: Icon(Icons.devices_outlined))),
          const SizedBox(height: 10),
          TextField(controller: sessionId, decoration: const InputDecoration(labelText: 'Current session ID', prefixIcon: Icon(Icons.key_outlined))),
          const SizedBox(height: 14),
          Align(alignment: Alignment.centerRight, child: FilledButton.icon(onPressed: onLoad, icon: const Icon(Icons.sync), label: const Text('Load sessions'))),
        ]),
      );
}

class _Inventory extends StatelessWidget {
  const _Inventory({required this.inventory, required this.onRevoke});
  final ZyraSessionInventory inventory;
  final Future<void> Function(ZyraSession) onRevoke;

  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(color: const Color(0xFF11141D), borderRadius: BorderRadius.circular(22)),
          child: Row(children: [
            Expanded(child: _Stat(label: 'Total', value: inventory.summary.total.toString())),
            Expanded(child: _Stat(label: 'Active', value: inventory.summary.active.toString())),
            Expanded(child: _Stat(label: 'Inactive', value: inventory.summary.inactive.toString())),
          ]),
        ),
        const SizedBox(height: 20),
        const Text('Sessions', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
        const SizedBox(height: 10),
        if (inventory.sessions.isEmpty) const _EmptyCard(message: 'No sessions returned.'),
        for (final session in inventory.sessions) Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(color: const Color(0xFF11141D), borderRadius: BorderRadius.circular(20), border: Border.all(color: session.current ? const Color(0xFF8F7CFF).withValues(alpha: .35) : Colors.transparent)),
            child: Row(children: [
              Icon(session.active ? Icons.verified_user_outlined : Icons.history_outlined),
              const SizedBox(width: 12),
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [Expanded(child: Text(_short(session.sessionId), style: const TextStyle(fontWeight: FontWeight.w600))), if (session.current) const _Tag(text: 'Current')]),
                const SizedBox(height: 5),
                Text(session.active ? 'Active · expires ${session.expiresAt}' : 'Inactive${session.revoked ? ' · revoked' : ''}', style: const TextStyle(color: Colors.white54, fontSize: 12)),
              ])),
              if (session.active && !session.current) IconButton(onPressed: () => onRevoke(session), tooltip: 'Revoke', icon: const Icon(Icons.block_outlined)),
            ]),
          ),
        ),
      ]);

  String _short(String value) => value.length <= 18 ? value : '${value.substring(0, 8)}…${value.substring(value.length - 6)}';
}

class _Stat extends StatelessWidget {
  const _Stat({required this.label, required this.value});
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => Column(children: [Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w700)), const SizedBox(height: 3), Text(label, style: const TextStyle(color: Colors.white54, fontSize: 12))]);
}

class _Tag extends StatelessWidget {
  const _Tag({required this.text});
  final String text;
  @override
  Widget build(BuildContext context) => Container(padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4), decoration: BoxDecoration(color: const Color(0xFF8F7CFF).withValues(alpha: .14), borderRadius: BorderRadius.circular(9)), child: Text(text, style: const TextStyle(fontSize: 11)));
}

class _ErrorCard extends StatelessWidget {
  const _ErrorCard({required this.message});
  final String message;
  @override
  Widget build(BuildContext context) => Container(width: double.infinity, margin: const EdgeInsets.only(top: 16), padding: const EdgeInsets.all(18), decoration: BoxDecoration(color: const Color(0xFF2A1518), borderRadius: BorderRadius.circular(20)), child: Row(children: [const Icon(Icons.error_outline), const SizedBox(width: 12), Expanded(child: Text(message))]));
}

class _EmptyCard extends StatelessWidget {
  const _EmptyCard({this.message = 'Enter the authenticated context above to load your sessions.'});
  final String message;
  @override
  Widget build(BuildContext context) => Container(width: double.infinity, margin: const EdgeInsets.only(top: 16), padding: const EdgeInsets.all(24), decoration: BoxDecoration(color: const Color(0xFF11141D), borderRadius: BorderRadius.circular(20)), child: Text(message, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white54)));
}
