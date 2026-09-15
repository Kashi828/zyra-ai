import 'package:flutter_test/flutter_test.dart';

import '../lib/endpoint_policy.dart';

void main() {
  test('allows local and private beta endpoints', () {
    expect(ZyraEndpointPolicy.isAllowed('http://127.0.0.1:8000'), isTrue);
    expect(ZyraEndpointPolicy.isAllowed('http://10.0.2.2:8000'), isTrue);
    expect(ZyraEndpointPolicy.isAllowed('http://192.168.1.10:8000'), isTrue);
    expect(ZyraEndpointPolicy.isAllowed('https://zyra.local:8443'), isTrue);
  });

  test('rejects public and unsupported endpoints', () {
    expect(ZyraEndpointPolicy.isAllowed('https://example.com'), isFalse);
    expect(ZyraEndpointPolicy.isAllowed('ftp://127.0.0.1:8000'), isFalse);
    expect(ZyraEndpointPolicy.isAllowed('http://8.8.8.8:8000'), isFalse);
    expect(ZyraEndpointPolicy.isAllowed('http://user:pass@127.0.0.1:8000'), isFalse);
  });

  test('validation fails closed for an unsafe endpoint', () {
    expect(() => ZyraEndpointPolicy.validate('https://example.com'), throwsArgumentError);
  });
}
