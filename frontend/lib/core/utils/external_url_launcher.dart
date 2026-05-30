import 'package:url_launcher/url_launcher.dart';

Future<bool> launchExternalUrl(String url) async {
  final trimmed = url.trim();
  if (trimmed.isEmpty) {
    return false;
  }

  final uri = Uri.tryParse(trimmed);
  if (uri == null || !(uri.isScheme('http') || uri.isScheme('https'))) {
    return false;
  }

  return launchUrl(uri, mode: LaunchMode.externalApplication);
}
