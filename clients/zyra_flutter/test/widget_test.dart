import 'package:flutter_test/flutter_test.dart';
import 'package:zyra_flutter/main.dart';

void main() {
  testWidgets('ZYRA home renders core shell', (tester) async {
    await tester.pumpWidget(const ZyraApp());

    expect(find.text('ZYRA'), findsOneWidget);
    expect(find.text('How can I help?'), findsOneWidget);
    expect(find.text('Secure session'), findsOneWidget);
    expect(find.text('Open calculator'), findsOneWidget);
  });
}
