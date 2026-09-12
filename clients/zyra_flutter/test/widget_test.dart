import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:zyra_flutter/main.dart';

void main() {
  testWidgets('ZYRA home renders core shell', (tester) async {
    await tester.pumpWidget(const ZyraApp());

    expect(find.text('ZYRA'), findsOneWidget);
    expect(find.text('How can I help?'), findsOneWidget);
    expect(find.text('Secure session'), findsOneWidget);

    final calculator = find.text('Open calculator');
    if (calculator.evaluate().isEmpty) {
      await tester.dragUntilVisible(
        calculator,
        find.byType(Scrollable).first,
        const Offset(0, -300),
      );
      await tester.pumpAndSettle();
    }
    expect(calculator, findsOneWidget);
  });

  testWidgets('ZYRA activity page shows empty state before actions', (tester) async {
    await tester.pumpWidget(const ZyraApp());

    final activityIcon = find.byIcon(Icons.bolt_outlined);
    expect(activityIcon, findsWidgets);
    await tester.tap(activityIcon.first);
    await tester.pumpAndSettle();

    expect(find.text('Protected activity'), findsOneWidget);
    expect(find.text('No activity yet'), findsOneWidget);
  });
}
