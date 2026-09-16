import 'package:flutter/material.dart';

import 'connection_diagnostics.dart';
import 'session_context.dart';
import 'zyra_service.dart';

class ZyraDevicesPage extends StatefulWidget {
  const ZyraDevicesPage({super.key, this.service, this.context});
  final ZyraService? service;
  final ZyraSessionContext? context;
  @override
  State<ZyraDevicesPage> createState() => _ZyraDevicesPageState();
}

class _ZyraDevicesPageState extends State<ZyraDevicesPage> {
  ZyraService get _service => widget.service ?? ZyraService();
  ZyraSessionContext get _context => widget.context ?? zyraSessionContext;
  ZyraSessionInventory? inventory;
  ZyraTransportProbe? probe;
  bool includeInactive = false;
  bool loading = false;
  bool probing = false;
  String? error;

  Future<void> _probeConnection() async {
    if (probing) return;
    setState(() => probing = true);
    try {
      final result = await const ZyraConnectionDiagnostics().probe(_service.target.uri.resolve('/health'));
      if (mounted) setState(() => probe = result);
    } finally {
      if (mounted) setState(() => probing = false);
    }
  }

  Future<void> _load() async {
    final credentials = _context.credentials;
    if (credentials == null) {
      setState(() => error = 'Configure the device ID and current session ID on Home first.');
      return;
    }
    setState(() { loading = true; error = null; });
    try {
      final result = await _service.listSessions(credentials, includeInactive: includeInactive);
      if (!mounted) return;
      setState(() => inventory = result);
    } catch (e) {
      if (mounted) setState(() => error = _message(e));
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> _revoke(ZyraSession target) async {
    if (target.current) {
      _show('The current session cannot be revoked from this screen.');
      return;
    }
    final credentials = _context.credentials;
    if (credentials == null) {
      _show('Current session is not configured.');
      return;
    }
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Revoke session?'),
        content: const Text('This will invalidate the selected session. Authorization remains server-side.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Revoke')),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await _service.revokeSession(credentials, target.sessionId);
      _show('Session revoked.');
      await _load();
    } catch (e) {
      _show(_message(e));
    }
  }

  void _show(String text) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
  String _message(Object error) => error.toString().replaceFirst('Exception: ', '');

  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.fromLTRB(24, 28, 24, 40), children: [
        Row(children: [
          const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Devices', style: TextStyle(fontSize: 31, fontWeight: FontWeight.w700)),
            SizedBox(height: 5),
            Text('Manage sessions and verify the local connection path.', style: TextStyle(color: Colors.white54)),
          ])),
          IconButton(onPressed: loading ? null : _load, tooltip: 'Refresh sessions', icon: const Icon(Icons.refresh)),
        ]),
        const SizedBox(height: 18),
        Card(child: Padding(padding: const EdgeInsets.all(16), child: Row(children: [
          const Icon(Icons.lan_outlined), const SizedBox(width: 12),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(_service.target.displayName, style: const TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 3),
            Text('${_service.target.uri.host}:${_service.target.uri.port}', style: const TextStyle(color: Colors.white54, fontSize: 12)),
          ])),
          FilledButton.tonalIcon(onPressed: probing ? null : _probeConnection, icon: probing ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.network_check_outlined), label: const Text('Test')),
        ])),
        if (probe != null) ...[
          const SizedBox(height: 10),
          Card(child: ListTile(
            leading: Icon(probe!.reachable ? Icons.check_circle_outline : Icons.error_outline),
            title: Text(probe!.reachable ? 'Transport reachable' : 'Transport unavailable'),
            subtitle: Text(probe!.reachable ? '${probe!.statusCode} · ${probe!.latency.inMilliseconds} ms' : '${probe!.reason ?? 'probe_failed'} · ${probe!.latency.inMilliseconds} ms'),
          )),
        ],
        const SizedBox(height: 12),
        Card(child: Padding(padding: const EdgeInsets.all(16), child: Row(children: [const Icon(Icons.verified_user_outlined), const SizedBox(width: 12), Expanded(child: Text(_context.configured ? 'Authenticated session configured' : 'No authenticated session configured', style: const TextStyle(fontWeight: FontWeight.w600))), if (_context.configured) Text(_context.deviceId, style: const TextStyle(color: Colors.white54, fontSize: 12))]))),
        const SizedBox(height: 12),
        SwitchListTile.adaptive(contentPadding: const EdgeInsets.symmetric(horizontal: 4), value: includeInactive, onChanged: loading ? null : (v) => setState(() => includeInactive = v), title: const Text('Show inactive sessions'), subtitle: const Text('Historical sessions are read-only.', style: TextStyle(color: Colors.white54))),
        if (loading) const Padding(padding: EdgeInsets.all(28), child: Center(child: CircularProgressIndicator())),
        if (error != null) _ErrorCard(error!),
        if (!loading && error == null && inventory == null) const _EmptyCard(),
        if (!loading && inventory != null) _Inventory(inventory: inventory!, onRevoke: _revoke),
      ]);
}

class _Inventory extends StatelessWidget {
  const _Inventory({required this.inventory, required this.onRevoke});
  final ZyraSessionInventory inventory;
  final Future<void> Function(ZyraSession) onRevoke;
  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Card(child: Padding(padding: const EdgeInsets.all(18), child: Row(children: [_Stat('Total', inventory.summary.total), _Stat('Active', inventory.summary.active), _Stat('Inactive', inventory.summary.inactive)]))),
    const SizedBox(height: 20), const Text('Sessions', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)), const SizedBox(height: 10),
    if (inventory.sessions.isEmpty) const _EmptyCard(message: 'No sessions returned.'),
    for (final session in inventory.sessions) Card(margin: const EdgeInsets.only(bottom: 10), child: ListTile(leading: Icon(session.active ? Icons.verified_user_outlined : Icons.history_outlined), title: Row(children: [Expanded(child: Text(_short(session.sessionId))), if (session.current) const Chip(label: Text('Current'))]), subtitle: Text(session.active ? 'Active · expires ${session.expiresAt}' : 'Inactive${session.revoked ? ' · revoked' : ''}'), trailing: session.active && !session.current ? IconButton(onPressed: () => onRevoke(session), tooltip: 'Revoke', icon: const Icon(Icons.block_outlined)) : null)),
  ]);
  String _short(String value) => value.length <= 18 ? value : '${value.substring(0, 8)}…${value.substring(value.length - 6)}';
}

class _Stat extends StatelessWidget {
  const _Stat(this.label, this.value);
  final String label; final int value;
  @override
  Widget build(BuildContext context) => Expanded(child: Column(children: [Text('$value', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w700)), Text(label, style: const TextStyle(color: Colors.white54, fontSize: 12))]));
}

class _ErrorCard extends StatelessWidget {
  const _ErrorCard(this.message);
  final String message;
  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(18), child: Row(children: [const Icon(Icons.error_outline), const SizedBox(width: 12), Expanded(child: Text(message))])));
}

class _EmptyCard extends StatelessWidget {
  const _EmptyCard({this.message = 'Configure the authenticated session on Home, then load sessions.'});
  final String message;
  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(24), child: Text(message, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white54))));
}
