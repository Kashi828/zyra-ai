import 'dart:async';
import 'dart:io';

/// Small, platform-neutral retry policy for transient ZYRA API connectivity.
/// Backoff is capped so the UI remains responsive during LAN outages.
class ZyraConnectionRetry {
  const ZyraConnectionRetry({this.maxAttempts = 3, this.baseDelay = const Duration(milliseconds: 350), this.maxDelay = const Duration(seconds: 2)})
      : assert(maxAttempts > 0);

  final int maxAttempts;
  final Duration baseDelay;
  final Duration maxDelay;

  Duration delayForAttempt(int attempt) {
    if (attempt <= 0) return Duration.zero;
    final multiplier = 1 << (attempt - 1);
    final candidate = Duration(milliseconds: baseDelay.inMilliseconds * multiplier);
    return candidate <= maxDelay ? candidate : maxDelay;
  }

  Future<T> run<T>(Future<T> Function() operation, {bool Function(Object error)? shouldRetry}) async {
    Object? lastError;
    StackTrace? lastStack;
    for (var attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        return await operation();
      } catch (error, stack) {
        lastError = error;
        lastStack = stack;
        final retry = attempt < maxAttempts && (shouldRetry?.call(error) ?? _defaultRetry(error));
        if (!retry) Error.throwWithStackTrace(error, stack);
        final delay = delayForAttempt(attempt);
        if (delay > Duration.zero) await Future<void>.delayed(delay);
      }
    }
    Error.throwWithStackTrace(lastError!, lastStack ?? StackTrace.current);
  }

  static bool _defaultRetry(Object error) => error is TimeoutException || error is SocketException;
}
