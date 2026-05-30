String? resolveSourceFaviconUrl({
  String? sourceSiteUrl,
  String? articleUrl,
}) {
  final candidate = sourceSiteUrl?.trim().isNotEmpty == true
      ? sourceSiteUrl!.trim()
      : articleUrl?.trim();

  if (candidate == null || candidate.isEmpty) {
    return null;
  }

  final uri = Uri.tryParse(candidate);
  if (uri == null || uri.host.isEmpty) {
    return null;
  }

  return 'https://www.google.com/s2/favicons?domain=${uri.host}&sz=32';
}
