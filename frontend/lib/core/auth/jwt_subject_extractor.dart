import 'dart:convert';

/// Extract JWT subject claim without verifying signature.
class JwtSubjectExtractor {
  const JwtSubjectExtractor._();

  static String? extractSubject(String token) {
    final trimmed = token.trim();
    if (trimmed.isEmpty) {
      return null;
    }

    final parts = trimmed.split('.');
    if (parts.length != 3) {
      return null;
    }

    try {
      final normalized = base64Url.normalize(parts[1]);
      final decoded = utf8.decode(base64Url.decode(normalized));
      final payload = jsonDecode(decoded);
      if (payload is Map<String, dynamic>) {
        final subject = payload['sub'];
        if (subject is String && subject.isNotEmpty) {
          return subject;
        }
      }
    } catch (_) {
      return null;
    }

    return null;
  }
}
